"""
Avatar Speaker - put a real person's 3D avatar on the couch and lip-sync it
===========================================================================

Takes the couch scene from ``speaker_couch_scene.py``, removes the cartoon
speaker, and seats a rigged, realistic avatar in its place. The avatar's mouth
is driven by a voice recording. The script also animates blinks, head nods,
breathing and hand gestures, timed to the phrases in the audio, and adds the
audio to the timeline so the rendered video has sound.

IMPORTANT - consent
-------------------
Only use the likeness and voice of yourself or of people who have explicitly
agreed to it. Label the result as an animated/AI-generated recreation when you
publish it, especially in a news context.

What you need
-------------
1. A *rigged* humanoid avatar (.fbx, .glb or .gltf). For example:
     * Reallusion Character Creator 4 + Headshot (photo -> realistic head,
       exports FBX with a full body rig and facial/viseme shape keys)
     * KeenTools FaceBuilder (photos -> head) on an MPFB / MakeHuman body
     * Any Mixamo-rigged character
   Supported bone naming: Mixamo, Character Creator (CC_Base_*), Rigify DEF
   bones, VRM/J_Bip, and generic "LeftArm"/"upper_arm.L" style names.
   Mouth: ARKit/CC/VRM/Oculus-viseme shape keys are used if present
   (jawOpen, mouthOpen, viseme_aa, V_Open, Fcl_MTH_A ...), otherwise the
   jaw bone is rotated.
2. A voice recording (.wav, .mp3, .m4a, .flac, .ogg ...).
3. ``speaker_couch_scene.blend`` (made by ``speaker_couch_scene.py``).

Usage
-----
Command line (recommended):

    blender --background --python avatar_speaker.py -- \
        --avatar /path/person.fbx --audio /path/voice.wav \
        [--scene speaker_couch_scene.blend] [--out speaker_avatar.blend] \
        [--render out/speaker.mp4] [--seat left|right] [--height 1.75]

Blender GUI: fill in CONFIG below, open the Scripting tab, Run Script.
"""

import argparse
import math
import os
import random
import re
import sys

import bpy
import numpy as np
from mathutils import Matrix, Quaternion, Vector

HERE = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else bpy.path.abspath("//")

# Edit these when running from the Blender GUI ------------------------------
CONFIG = {
    "avatar": "",                    # path to .fbx / .glb / .gltf
    "audio": "",                     # path to the voice recording
    "scene": os.path.join(HERE, "speaker_couch_scene.blend"),
    "out": os.path.join(HERE, "speaker_avatar_scene.blend"),
    "render": "",                    # e.g. "/tmp/speaker.mp4" to render the video
    "seat": "left",                  # which couch cushion to sit on
    "height": 0.0,                   # force standing height in metres (0 = auto)
    "seed": 3,
}

SEATS = {"left": Vector((-0.45, 0.55, 0.60)), "right": Vector((0.45, 0.55, 0.60))}
FLOOR_ANKLE_Z = 0.09           # world height of the ankle joint when feet are on the floor
BODY_KEY_STEP = 3              # body pose keyframe spacing (frames)
LATERAL = Vector((1, 0, 0))    # character faces -Y, so +X is their left side
UP = Vector((0, 0, 1))


# ---------------------------------------------------------------------------
# Arguments
# ---------------------------------------------------------------------------
def parse_args():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    p = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    p.add_argument("--avatar", default=CONFIG["avatar"])
    p.add_argument("--audio", default=CONFIG["audio"])
    p.add_argument("--scene", default=CONFIG["scene"])
    p.add_argument("--out", default=CONFIG["out"])
    p.add_argument("--render", default=CONFIG["render"])
    p.add_argument("--seat", default=CONFIG["seat"], choices=sorted(SEATS))
    p.add_argument("--height", type=float, default=CONFIG["height"])
    p.add_argument("--seed", type=int, default=CONFIG["seed"])
    args = p.parse_args(argv)
    for k in ("avatar", "audio"):
        path = getattr(args, k)
        if not path or not os.path.isfile(path):
            raise SystemExit(f"--{k} file not found: {path!r}")
    return args


# ---------------------------------------------------------------------------
# Scene / import
# ---------------------------------------------------------------------------
def remove_hierarchy(name):
    obj = bpy.data.objects.get(name)
    if not obj:
        return
    for o in [obj, *obj.children_recursive]:
        bpy.data.objects.remove(o, do_unlink=True)


def import_avatar(path):
    before = set(bpy.data.objects)
    ext = os.path.splitext(path)[1].lower()
    if ext == ".fbx":
        bpy.ops.import_scene.fbx(filepath=path, ignore_leaf_bones=False)
    elif ext in (".glb", ".gltf"):
        bpy.ops.import_scene.gltf(filepath=path)
    else:
        raise SystemExit(f"Unsupported avatar format {ext!r} (use .fbx, .glb or .gltf)")
    new = [o for o in bpy.data.objects if o not in before]
    arms = [o for o in new if o.type == "ARMATURE"]
    if not arms:
        raise SystemExit("The avatar has no armature (skeleton). Rig it first, e.g. with Mixamo.")
    arm = max(arms, key=lambda o: len(o.data.bones))
    meshes = [o for o in new if o.type == "MESH"]
    # Drop any animation that came with the file - we drive the pose ourselves
    for o in new:
        if o.animation_data:
            o.animation_data.action = None
        if o.type == "MESH" and o.data.shape_keys and o.data.shape_keys.animation_data:
            o.data.shape_keys.animation_data.action = None
    return arm, meshes, new


# ---------------------------------------------------------------------------
# Bone discovery
# ---------------------------------------------------------------------------
PREFIX = re.compile(r"^(mixamorig\d*:|cc_base_|def[-_]|org[-_]|j_bip_|bip0?1?[ _]?|armature[|:])")


def norm(name):
    return re.sub(r"[^a-z0-9]", "", PREFIX.sub("", name.lower()))


def side_variants(parts, side):
    """parts like ['arm','upperarm'] -> leftarm, larm, arml, armleft ..."""
    word = "left" if side == "L" else "right"
    s = side.lower()
    out = []
    for p in parts:
        out += [word + p, s + p, p + s, p + word]
    return out


CANDIDATES = {
    "hips": ["hips", "hip", "pelvis", "root"],
    "neck": ["neck", "neck1", "neck01", "necktwist01", "cneck"],
    "head": ["head", "chead"],
    "jaw": ["jaw", "jawroot", "jaw01", "lowerjaw", "jawbone"],
}
for side in ("L", "R"):
    CANDIDATES[f"upperarm{side}"] = side_variants(["arm", "upperarm", "uparm"], side)
    CANDIDATES[f"forearm{side}"] = side_variants(["forearm", "lowerarm"], side)
    CANDIDATES[f"thigh{side}"] = side_variants(["upleg", "thigh", "upperleg"], side)
    CANDIDATES[f"shin{side}"] = side_variants(["leg", "calf", "shin", "lowerleg"], side)
    CANDIDATES[f"foot{side}"] = side_variants(["foot", "ankle"], side)


def find_bones(arm):
    lookup = {}
    for b in arm.data.bones:
        lookup.setdefault(norm(b.name), b.name)
    found = {}
    for key, cands in CANDIDATES.items():
        for c in cands:
            if c in lookup:
                found[key] = lookup[c]
                break
    missing = [k for k in ("hips", "head", "upperarmL", "upperarmR", "forearmL", "forearmR",
                           "thighL", "thighR", "shinL", "shinR") if k not in found]
    if missing:
        raise SystemExit("Could not identify these bones: " + ", ".join(missing) +
                         "\nBones in rig: " + ", ".join(b.name for b in arm.data.bones))
    # Spine chain = bones between hips and neck/head
    top = found.get("neck", found["head"])
    chain, b = [], arm.data.bones[top].parent
    while b and b.name != found["hips"]:
        chain.append(b.name)
        b = b.parent
    found["spine"] = list(reversed(chain))  # lowest first
    if "neck" not in found:
        found["neck"] = None
    return found


# ---------------------------------------------------------------------------
# Lightweight forward kinematics (no depsgraph updates needed)
# ---------------------------------------------------------------------------
class Poser:
    def __init__(self, arm):
        self.arm = arm
        self.bones = arm.data.bones
        self.rest = {b.name: b.matrix_local.copy() for b in self.bones}
        self.obj_rot_inv = arm.matrix_world.to_quaternion().inverted()
        self.reset()

    def reset(self):
        self.basis = {}
        self._cache = {}

    def _parent_base(self, name):
        """Pose matrix this bone would have with an identity basis."""
        b = self.bones[name]
        if b.parent is None:
            return self.rest[name]
        rel = self.rest[b.parent.name].inverted() @ self.rest[name]
        return self.pose(b.parent.name) @ rel

    def pose(self, name):
        if name not in self._cache:
            self._cache[name] = self._parent_base(name) @ self.basis.get(name, Matrix.Identity(4))
        return self._cache[name]

    def _set_rot(self, name, new_rot3):
        base = self._parent_base(name)
        self.basis[name] = (base.to_3x3().inverted() @ new_rot3).to_4x4()
        self._cache.clear()

    def to_arm(self, v):
        return self.obj_rot_inv @ v

    def aim(self, name, world_dir):
        """Rotate a bone (minimal twist) so it points along world_dir."""
        base = self._parent_base(name)
        cur = base.to_3x3().col[1].normalized()
        q = cur.rotation_difference(self.to_arm(world_dir.normalized()))
        self._set_rot(name, q.to_matrix() @ base.to_3x3())

    def rotate(self, name, world_axis, angle):
        """Add a world-space rotation on top of the bone's current pose."""
        q = Quaternion(self.to_arm(world_axis), angle)
        self._set_rot(name, q.to_matrix() @ self.pose(name).to_3x3())

    def world_head(self, name):
        return self.arm.matrix_world @ self.pose(name).translation

    def key(self, names, frame):
        for n in names:
            pb = self.arm.pose.bones[n]
            pb.rotation_mode = "QUATERNION"
            pb.rotation_quaternion = self.basis.get(n, Matrix.Identity(4)).to_quaternion()
            pb.keyframe_insert("rotation_quaternion", frame=frame, group=n)


# ---------------------------------------------------------------------------
# Placement
# ---------------------------------------------------------------------------
def orient_and_place(arm, bones, seat, force_height):
    bpy.context.view_layer.update()
    mw = arm.matrix_world
    # Face -Y: the character's left arm should be on world +X
    l = mw @ arm.data.bones[bones["upperarmL"]].head_local
    r = mw @ arm.data.bones[bones["upperarmR"]].head_local
    across = (l - r)
    yaw = math.atan2(across.y, across.x)
    arm.rotation_mode = "XYZ"
    arm.rotation_euler.z -= yaw
    bpy.context.view_layer.update()

    # Scale to a sensible human height if the import units are off
    mw = arm.matrix_world
    zs = [(mw @ b.head_local).z for b in arm.data.bones] + [(mw @ b.tail_local).z for b in arm.data.bones]
    height = (max(zs) - min(zs)) * 1.04
    if force_height > 0:
        arm.scale *= force_height / height
    elif not 1.3 < height < 2.2:
        arm.scale *= 1.75 / height
    bpy.context.view_layer.update()

    hips = arm.matrix_world @ arm.data.bones[bones["hips"]].head_local
    arm.location += seat - hips
    bpy.context.view_layer.update()


# ---------------------------------------------------------------------------
# Audio analysis
# ---------------------------------------------------------------------------
def load_audio(path, rate=16000):
    import aud
    snd = aud.Sound.file(path).rechannel(1).resample(rate, 2)
    data = np.asarray(snd.data(), dtype=np.float32)
    return data[:, 0] if data.ndim == 2 else data, rate


def analyse(path, fps):
    samples, rate = load_audio(path)
    hop = rate / fps
    n = int(len(samples) / hop)
    rms = np.zeros(n)
    zcr = np.zeros(n)
    for i in range(n):
        w = samples[int(i * hop): int((i + 1) * hop)]
        if len(w):
            rms[i] = math.sqrt(float(np.mean(w * w)))
            zcr[i] = float(np.mean(np.abs(np.diff(np.sign(w))) > 0))
    floor = np.percentile(rms, 20) * 1.5 + 1e-5
    peak = max(np.percentile(rms, 97), floor * 2)
    level = np.clip((rms - floor) / (peak - floor), 0, 1) ** 0.7
    # Fast attack, slower release so the mouth closes naturally
    env = np.zeros(n)
    for i in range(n):
        prev = env[i - 1] if i else 0.0
        a = 0.75 if level[i] > prev else 0.45
        env[i] = prev + (level[i] - prev) * a
    voiced = env > 0.08
    zn = (zcr - zcr[voiced].min()) / (np.ptp(zcr[voiced]) + 1e-6) if voiced.any() else zcr * 0
    # Phrases: voiced runs separated by >= 0.35 s of silence
    phrases, start, gap = [], None, 0
    for i, v in enumerate(voiced):
        if v:
            if start is None:
                start = i
            gap = 0
        elif start is not None:
            gap += 1
            if gap >= int(0.35 * fps):
                phrases.append((start, i - gap))
                start, gap = None, 0
    if start is not None:
        phrases.append((start, n - 1))
    phrases = [p for p in phrases if p[1] - p[0] > fps * 0.25]
    return {"n": n, "open": env, "zcr": np.clip(zn, 0, 1), "voiced": voiced, "phrases": phrases}


# ---------------------------------------------------------------------------
# Facial animation
# ---------------------------------------------------------------------------
SHAPES = {
    "open": ["jawopen", "mouthopen", "visemeaa", "vopen", "fclmtha", "mouthopenwide", "aa", "a",
             "jawdown", "mouthwide"],
    "wide": ["visemee", "visemeih", "vwide", "fclmthe", "fclmthi", "ee", "e", "i", "mouthstretch"],
    "round": ["visemeou", "visemeo", "vtighto", "mouthfunnel", "mouthpucker", "fclmtho", "fclmthu",
              "oh", "ou", "o", "u"],
    "blink": ["eyeblinkleft", "eyeblinkright", "eyeblinkl", "eyeblinkr", "eyeblink", "blink",
              "eyesclosed", "eyeclose", "fcleyeclose", "blinkleft", "blinkright", "blinkl", "blinkr"],
}


def find_shape_keys(meshes):
    found = {k: [] for k in SHAPES}
    for m in meshes:
        sk = m.data.shape_keys
        if not sk:
            continue
        names = {norm(kb.name): kb for kb in sk.key_blocks[1:]}
        for kind, cands in SHAPES.items():
            for c in cands:
                if c in names:
                    found[kind].append(names[c])
                    if kind != "blink":
                        break
    return found


def key_shape(kbs, value, frame):
    for kb in kbs:
        kb.value = value
        kb.keyframe_insert("value", frame=frame)


def animate_face(poser, bones, keys, audio, start, fps, rng):
    n = audio["n"]
    use_jaw_bone = not keys["open"]
    if use_jaw_bone and not bones.get("jaw"):
        print("WARNING: no mouth shape keys and no jaw bone found - lips will not move.")
    jaw = bones.get("jaw")
    if use_jaw_bone and jaw:
        rest3 = poser.rest[jaw].to_3x3()
        axis_local = (rest3.inverted() @ poser.to_arm(LATERAL)).normalized()
        pb = poser.arm.pose.bones[jaw]
        pb.rotation_mode = "QUATERNION"

    for i in range(n):
        f = start + i
        o = float(audio["open"][i])
        z = float(audio["zcr"][i])
        if keys["open"]:
            key_shape(keys["open"], min(1.0, o * 0.9), f)
            key_shape(keys["wide"], o * max(0.0, z - 0.45) * 1.2, f)
            key_shape(keys["round"], o * max(0.0, 0.4 - z) * 1.5, f)
        elif jaw:
            pb.rotation_quaternion = Quaternion(axis_local, math.radians(16) * o)
            pb.keyframe_insert("rotation_quaternion", frame=f, group=jaw)

    # Blinks every 2-5 s
    if keys["blink"]:
        key_shape(keys["blink"], 0.0, start)
        t = start + rng.randint(20, 60)
        while t < start + n:
            key_shape(keys["blink"], 0.0, t - 2)
            key_shape(keys["blink"], 1.0, t)
            key_shape(keys["blink"], 0.0, t + 3)
            t += rng.randint(int(fps * 2), int(fps * 5))


# ---------------------------------------------------------------------------
# Body animation
# ---------------------------------------------------------------------------
def V(*a):
    return Vector(a).normalized()


# Arm directions for the character's LEFT side (x is mirrored for the right)
ARM_POSES = {
    "rest":    (V(0.12, -0.30, -1.0), V(-0.25, -1.0, -0.30)),   # hands on lap
    "explain": (V(0.25, -0.45, -0.9), V(0.10, -0.80, 0.55)),
    "open":    (V(0.45, -0.35, -0.8), V(0.70, -0.60, 0.35)),
    "point":   (V(0.18, -0.70, -0.6), V(0.00, -1.00, 0.25)),
    "chest":   (V(0.30, -0.25, -0.9), V(-0.70, -0.55, 0.45)),   # hand toward chest
}
GESTURES = ["explain", "open", "point", "chest", "explain", "open"]


def mirror(v, side):
    return Vector((v.x if side == "L" else -v.x, v.y, v.z))


def smoothstep(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


def schedule_gestures(audio, start, fps, rng):
    """Per-side list of (frame, pose_name) events driven by phrases."""
    events = {"L": [(start, "rest")], "R": [(start, "rest")]}
    for a, b in audio["phrases"]:
        a, b = start + a, start + b
        length = b - a
        if length < fps * 0.8 or rng.random() < 0.2:
            continue  # short phrase: stay still
        sides = rng.choice([["R"], ["R"], ["L"], ["L", "R"]])
        t = a + 4
        while t < b - fps * 0.5:
            g = rng.choice(GESTURES)
            for s in sides:
                events[s].append((t, g))
            t += rng.randint(int(fps * 1.4), int(fps * 2.6))
        for s in sides:
            events[s].append((b + 6, "rest"))
    for s in events:
        events[s].sort()
    return events


def arm_dirs(events, side, frame, blend=10):
    prev, cur = events[0], events[0]
    for e in events:
        if e[0] <= frame:
            prev, cur = cur, e
        else:
            break
    t = smoothstep((frame - cur[0]) / blend)
    pa, pb = ARM_POSES[prev[1]], ARM_POSES[cur[1]]
    return [mirror(x.lerp(y, t).normalized(), side) for x, y in zip(pa, pb)]


def animate_body(poser, bones, audio, start, fps, rng):
    n = audio["n"]
    end = start + n + fps
    events = schedule_gestures(audio, start, fps, rng)
    env = audio["open"]
    # Nods on stressed syllables (local loudness peaks)
    nods = []
    for i in range(2, n - 2):
        if env[i] > 0.85 and env[i] >= env[i - 2:i + 3].max() and (not nods or i - nods[-1] > fps):
            nods.append(i)

    posed = [*bones["spine"], bones["head"], bones["upperarmL"], bones["forearmL"],
             bones["upperarmR"], bones["forearmR"], bones["thighL"], bones["shinL"],
             bones["thighR"], bones["shinR"]]
    if bones["neck"]:
        posed.append(bones["neck"])
    for k in ("footL", "footR"):
        if bones.get(k):
            posed.append(bones[k])

    ph = [rng.uniform(0, 10) for _ in range(6)]
    for f in range(start, end + 1, BODY_KEY_STEP):
        i = f - start
        t = f / fps
        poser.reset()
        # Spine: lean back into the couch + breathing
        lean = math.radians(-9 + 1.2 * math.sin(t * 1.6 + ph[0]))
        for sb in bones["spine"][:1]:
            poser.rotate(sb, LATERAL, lean)
        for sb in bones["spine"][1:2]:
            poser.rotate(sb, UP, math.radians(2.5 * math.sin(t * 0.35 + ph[1])))
        # Head: slow look-around + nods on emphasis
        nod = sum(math.exp(-((i - p) / 4.0) ** 2) for p in nods) * math.radians(7)
        pitch = math.radians(2 * math.sin(t * 0.9 + ph[2])) + nod
        yaw = math.radians(7 * math.sin(t * 0.33 + ph[3]) + 3 * math.sin(t * 0.8 + ph[4]))
        roll = math.radians(2.5 * math.sin(t * 0.5 + ph[5]))
        if bones["neck"]:
            poser.rotate(bones["neck"], UP, yaw * 0.4)
            poser.rotate(bones["neck"], LATERAL, pitch * 0.4)
        poser.rotate(bones["head"], UP, yaw * 0.6)
        poser.rotate(bones["head"], LATERAL, pitch * 0.6)
        poser.rotate(bones["head"], Vector((0, -1, 0)), roll)
        # Arms
        for s in ("L", "R"):
            up, fore = arm_dirs(events[s], s, f)
            wob = Vector((math.sin(t * 2.1 + ph[0]), 0, math.sin(t * 1.7 + ph[3]))) * 0.03
            poser.aim(bones[f"upperarm{s}"], up)
            poser.aim(bones[f"forearm{s}"], fore + wob)
        # Legs: thighs forward, shins down to the floor
        for s in ("L", "R"):
            x = 0.10 if s == "L" else -0.10
            poser.aim(bones[f"thigh{s}"], Vector((x, -1, -0.06)))
            knee = poser.world_head(bones[f"shin{s}"])
            shin_len = poser.arm.data.bones[bones[f"shin{s}"]].length * poser.arm.matrix_world.to_scale().z
            drop = knee.z - FLOOR_ANKLE_Z
            fwd = math.sqrt(max(shin_len ** 2 - drop ** 2, 0.0)) if drop > 0 else shin_len
            poser.aim(bones[f"shin{s}"], Vector((x * 0.3, -fwd, -max(drop, 0.05))))
            if bones.get(f"foot{s}"):
                poser.aim(bones[f"foot{s}"], Vector((x * 0.4, -1, -0.35)))
        poser.key(posed, f)
    return end


# ---------------------------------------------------------------------------
# Scene finishing
# ---------------------------------------------------------------------------
def add_audio(scene, path, start):
    se = scene.sequence_editor or scene.sequence_editor_create()
    strips = se.strips if hasattr(se, "strips") else se.sequences
    strips.new_sound("Voice", path, 1, start)


def setup_camera(scene, arm, bones, seat):
    head = arm.matrix_world @ arm.data.bones[bones["head"]].head_local
    target = bpy.data.objects.get("Camera_Target")
    if target:
        target.location = (seat.x + 0.15, seat.y - 0.15, head.z - 0.35)
    cam = scene.camera
    if cam:
        cam.data.dof.focus_object = arm
        if hasattr(cam.data.dof, "focus_subtarget"):
            cam.data.dof.focus_subtarget = bones["head"]


def setup_video_output(scene, path):
    scene.render.filepath = path
    s = scene.render.image_settings
    if hasattr(s, "media_type"):
        s.media_type = "VIDEO"
    s.file_format = "FFMPEG"
    ff = scene.render.ffmpeg
    ff.format = "MPEG4"
    ff.codec = "H264"
    ff.constant_rate_factor = "HIGH"
    ff.audio_codec = "AAC"
    ff.audio_bitrate = 192


def main():
    args = parse_args()
    rng = random.Random(args.seed)
    if os.path.isfile(args.scene):
        bpy.ops.wm.open_mainfile(filepath=args.scene)
    else:
        print(f"Base scene {args.scene!r} not found, using the open scene.")
    scene = bpy.context.scene
    fps = scene.render.fps
    start = 1
    seat = SEATS[args.seat]

    remove_hierarchy("Speaker")
    arm, meshes, _ = import_avatar(args.avatar)
    bones = find_bones(arm)
    print("Bones:", {k: v for k, v in bones.items() if k != "spine"}, "spine:", bones["spine"])
    orient_and_place(arm, bones, seat, args.height)
    arm.data.pose_position = "POSE"
    for pb in arm.pose.bones:  # clear any imported pose
        pb.rotation_mode = "QUATERNION"
        pb.rotation_quaternion = (1, 0, 0, 0)
        pb.location = (0, 0, 0)
        pb.scale = (1, 1, 1)

    audio = analyse(args.audio, fps)
    print(f"Audio: {audio['n'] / fps:.1f}s, {len(audio['phrases'])} phrases")
    poser = Poser(arm)
    keys = find_shape_keys(meshes)
    print("Shape keys:", {k: [kb.name for kb in v] for k, v in keys.items()})
    animate_face(poser, bones, keys, audio, start, fps, rng)
    end = animate_body(poser, bones, audio, start, fps, rng)

    scene.frame_start, scene.frame_end = start, end
    add_audio(scene, os.path.abspath(args.audio), start)
    setup_camera(scene, arm, bones, seat)
    scene.frame_set(start + min(48, audio["n"] // 2))

    if args.out:
        bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(args.out))
        print("Saved", args.out)
    if args.render:
        setup_video_output(scene, os.path.abspath(args.render))
        bpy.ops.render.render(animation=True)
        print("Rendered", args.render)


main()
