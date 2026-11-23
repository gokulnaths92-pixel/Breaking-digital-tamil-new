"""
Speaker on a Couch - procedural Blender scene
=============================================

Builds a cozy living-room / talk-show set with a stylized person sitting on a
couch and *speaking*: animated mouth, blinking eyes, head nods and hand
gestures. Includes lighting, a camera, props and a 10-second animation.

Usage
-----
  * Blender GUI : open the "Scripting" tab, load this file, press "Run Script".
  * Command line:
        blender --background --python speaker_couch_scene.py
    (saves speaker_couch_scene.blend next to this script and renders a still
     preview to speaker_couch_preview.png)

Tested with Blender 4.2+ / 5.x.
"""

import math
import os
import random

import bpy
from mathutils import Vector

random.seed(7)

FPS = 24
FRAME_END = 240  # 10 seconds
OUT_DIR = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else "//"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def clear_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for coll in (bpy.data.meshes, bpy.data.materials, bpy.data.lights,
                 bpy.data.cameras, bpy.data.curves, bpy.data.actions):
        for block in list(coll):
            if block.users == 0:
                coll.remove(block)


def material(name, color, roughness=0.5, metallic=0.0, emission=None, strength=0.0, sss=0.0):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Metallic"].default_value = metallic
    if sss and "Subsurface Weight" in bsdf.inputs:
        bsdf.inputs["Subsurface Weight"].default_value = sss
        bsdf.inputs["Subsurface Radius"].default_value = (0.3, 0.12, 0.08)
        bsdf.inputs["Subsurface Scale"].default_value = 0.02
    if emission:
        key = "Emission Color" if "Emission Color" in bsdf.inputs else "Emission"
        bsdf.inputs[key].default_value = (*emission, 1.0)
        bsdf.inputs["Emission Strength"].default_value = strength
    return mat


def assign(obj, mat):
    obj.data.materials.clear()
    obj.data.materials.append(mat)
    return obj


def smooth(obj):
    for p in obj.data.polygons:
        p.use_smooth = True
    return obj


def bevel(obj, width=0.03, segments=3):
    m = obj.modifiers.new("Bevel", "BEVEL")
    m.width = width
    m.segments = segments
    m.limit_method = "ANGLE"
    smooth(obj)
    return obj


def subsurf(obj, levels=2):
    m = obj.modifiers.new("Subsurf", "SUBSURF")
    m.levels = levels
    m.render_levels = levels
    smooth(obj)
    return obj


def box(name, loc, size, mat, bev=0.0, parent=None):
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 0))
    obj = bpy.context.active_object
    obj.name = name
    obj.scale = size
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.location = loc
    assign(obj, mat)
    if bev:
        bevel(obj, bev)
    if parent:
        obj.parent = parent
    return obj


def cylinder(name, loc, radius, depth, mat, rot=(0, 0, 0), verts=32, r2=None, parent=None):
    if r2 is None:
        bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=radius, depth=depth,
                                            location=loc, rotation=rot)
    else:
        bpy.ops.mesh.primitive_cone_add(vertices=verts, radius1=radius, radius2=r2,
                                        depth=depth, location=loc, rotation=rot)
    obj = bpy.context.active_object
    obj.name = name
    assign(obj, mat)
    smooth(obj)
    if parent:
        obj.parent = parent
    return obj


def sphere(name, loc, scale, mat, parent=None, segs=32):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segs, ring_count=segs // 2, radius=1, location=loc)
    obj = bpy.context.active_object
    obj.name = name
    obj.scale = scale
    assign(obj, mat)
    smooth(obj)
    if parent:
        obj.parent = parent
    return obj


def empty(name, loc=(0, 0, 0), rot=(0, 0, 0), parent=None):
    obj = bpy.data.objects.new(name, None)
    bpy.context.collection.objects.link(obj)
    obj.empty_display_size = 0.08
    obj.parent = parent
    obj.location = loc
    obj.rotation_euler = rot
    return obj


def limb(name, parent, loc, rot, length, r_top, r_bot, mat, joint_mat=None):
    """A tapered limb hanging along the pivot's local -Z axis."""
    pivot = empty(f"{name}_pivot", loc, rot, parent)
    seg = cylinder(name, (0, 0, 0), r_top, length, mat, r2=r_bot)
    # cone_add puts radius1 at -Z, so flip so the thick end sits at the pivot
    seg.rotation_euler = (math.pi, 0, 0)
    seg.parent = pivot
    seg.location = (0, 0, -length / 2)
    sphere(f"{name}_joint", (0, 0, 0), (r_top,) * 3, joint_mat or mat, parent=pivot)
    end = empty(f"{name}_end", (0, 0, -length), parent=pivot)
    return pivot, end


def fcurves_of(obj):
    """Return the F-curves of obj's action (works with legacy & slotted actions)."""
    action = obj.animation_data.action
    if hasattr(action, "fcurves") and len(getattr(action, "fcurves", [])):
        return action.fcurves
    from bpy_extras import anim_utils
    bag = anim_utils.action_get_channelbag_for_slot(action, obj.animation_data.action_slot)
    return bag.fcurves


def add_noise(obj, data_path, index, strength, scale, phase=None):
    for fc in fcurves_of(obj):
        if fc.data_path == data_path and fc.array_index == index:
            mod = fc.modifiers.new("NOISE")
            mod.strength = strength
            mod.scale = scale
            mod.phase = phase if phase is not None else random.uniform(0, 100)
            return mod


def key(obj, path, frame, value=None, interp="BEZIER"):
    if value is not None:
        setattr(obj, path, value)
    obj.keyframe_insert(data_path=path, frame=frame)


# ---------------------------------------------------------------------------
# Scene
# ---------------------------------------------------------------------------
clear_scene()
scene = bpy.context.scene
scene.render.fps = FPS
scene.frame_start = 1
scene.frame_end = FRAME_END

# Materials ------------------------------------------------------------------
M = {
    "floor":   material("Floor_Wood", (0.32, 0.19, 0.11), 0.45),
    "wall":    material("Wall_Paint", (0.78, 0.70, 0.60), 0.9),
    "accent":  material("Wall_Accent", (0.16, 0.27, 0.30), 0.9),
    "rug":     material("Rug", (0.62, 0.52, 0.42), 1.0),
    "fabric":  material("Couch_Fabric", (0.12, 0.32, 0.36), 0.95),
    "cushion": material("Cushion_Mustard", (0.80, 0.55, 0.15), 0.95),
    "wood":    material("Wood_Dark", (0.14, 0.08, 0.04), 0.4),
    "skin":    material("Skin", (0.55, 0.36, 0.25), 0.45, sss=0.15),
    "lips":    material("Lips", (0.35, 0.15, 0.12), 0.4),
    "mouth":   material("Mouth_Inside", (0.08, 0.02, 0.02), 0.6),
    "eye":     material("Eye_White", (0.92, 0.92, 0.9), 0.2),
    "iris":    material("Iris", (0.05, 0.03, 0.02), 0.1),
    "hair":    material("Hair", (0.03, 0.02, 0.015), 0.6),
    "shirt":   material("Shirt", (0.85, 0.82, 0.76), 0.8),
    "blazer":  material("Blazer", (0.10, 0.12, 0.18), 0.7),
    "pants":   material("Pants", (0.20, 0.18, 0.16), 0.8),
    "shoe":    material("Shoes", (0.06, 0.04, 0.03), 0.3),
    "metal":   material("Metal_Black", (0.02, 0.02, 0.02), 0.3, metallic=1.0),
    "brass":   material("Brass", (0.8, 0.6, 0.3), 0.25, metallic=1.0),
    "shade":   material("Lamp_Shade", (1.0, 0.85, 0.6), 0.8, emission=(1.0, 0.75, 0.45), strength=3.0),
    "plant":   material("Leaves", (0.08, 0.30, 0.08), 0.6),
    "pot":     material("Pot_Ceramic", (0.85, 0.83, 0.78), 0.3),
    "ceramic": material("Mug", (0.75, 0.2, 0.15), 0.25),
    "book1":   material("Book_Red", (0.5, 0.08, 0.06), 0.7),
    "book2":   material("Book_Blue", (0.08, 0.15, 0.4), 0.7),
    "art":     material("Art", (0.9, 0.45, 0.2), 0.8),
    "window":  material("Window_Glow", (0.8, 0.9, 1.0), 0.5, emission=(0.75, 0.85, 1.0), strength=2.5),
}

# Room -------------------------------------------------------------------------
bpy.ops.mesh.primitive_plane_add(size=10, location=(0, 0, 0))
assign(bpy.context.active_object, M["floor"]).name = "Floor"
box("Back_Wall", (0, 1.6, 1.75), (10, 0.1, 3.5), M["wall"])
box("Accent_Panel", (0, 1.54, 1.25), (3.2, 0.03, 2.5), M["accent"])
box("Side_Wall", (-3.2, 0, 1.75), (0.1, 10, 3.5), M["wall"])
box("Window", (-3.14, -0.6, 1.7), (0.02, 1.4, 1.5), M["window"])
box("Baseboard", (0, 1.53, 0.06), (10, 0.03, 0.12), M["wood"])
box("Rug", (0, -0.5, 0.005), (3.2, 2.4, 0.01), M["rug"], bev=0.004)

# Wall art
box("Frame", (0, 1.52, 2.0), (1.2, 0.04, 0.75), M["wood"], bev=0.01)
box("Canvas", (0, 1.495, 2.0), (1.08, 0.02, 0.63), M["art"])

# Couch ------------------------------------------------------------------------
couch = empty("Couch", (0, 0.65, 0))
W, D = 2.3, 0.95
box("Couch_Base", (0, 0, 0.30), (W, D, 0.26), M["fabric"], 0.04, couch)
box("Couch_Back", (0, 0.38, 0.72), (W, 0.22, 0.62), M["fabric"], 0.07, couch)
for side in (-1, 1):
    box(f"Couch_Arm_{side}", (side * (W / 2 - 0.09), 0, 0.55), (0.2, D, 0.36), M["fabric"], 0.07, couch)
for i, x in enumerate((-0.52, 0.52)):
    c = box(f"Seat_Cushion_{i}", (x, -0.07, 0.5), (1.0, 0.78, 0.16), M["fabric"], 0.06, couch)
    b = box(f"Back_Cushion_{i}", (x, 0.22, 0.82), (0.98, 0.18, 0.5), M["fabric"], 0.08, couch)
    b.rotation_euler.x = math.radians(-10)
for i, (x, mat) in enumerate(((0.82, "cushion"), (-0.85, "accent"))):
    p = box(f"Throw_Pillow_{i}", (x, 0.12, 0.78), (0.42, 0.14, 0.42), M[mat], 0.07, couch)
    subsurf(p, 2)
    p.rotation_euler = (math.radians(-15), 0, math.radians(8 * (1 if x > 0 else -1)))
for sx in (-1, 1):
    for sy in (-1, 1):
        cylinder("Couch_Leg", (sx * (W / 2 - 0.1), sy * (D / 2 - 0.1), 0.085), 0.03, 0.17,
                 M["wood"], r2=0.02, parent=couch)

# Coffee table & props ---------------------------------------------------------
table = empty("Coffee_Table", (0.15, -0.95, 0))
box("Table_Top", (0, 0, 0.42), (1.2, 0.6, 0.05), M["wood"], 0.01, table)
for sx in (-1, 1):
    for sy in (-1, 1):
        cylinder("Table_Leg", (sx * 0.52, sy * 0.24, 0.2), 0.022, 0.4, M["brass"], parent=table)
cylinder("Mug", (0.3, 0.05, 0.495), 0.045, 0.1, M["ceramic"], parent=table)
box("Book_1", (-0.25, -0.02, 0.46), (0.32, 0.24, 0.035), M["book1"], 0.004, table)
bk = box("Book_2", (-0.23, 0.0, 0.493), (0.28, 0.21, 0.03), M["book2"], 0.004, table)
bk.rotation_euler.z = math.radians(12)

# Floor lamp (right of couch)
lamp = empty("Floor_Lamp", (1.65, 0.9, 0))
cylinder("Lamp_Base", (0, 0, 0.02), 0.18, 0.04, M["metal"], parent=lamp)
cylinder("Lamp_Pole", (0, 0, 0.8), 0.015, 1.6, M["brass"], parent=lamp)
cylinder("Lamp_Shade", (0, 0, 1.62), 0.26, 0.34, M["shade"], r2=0.17, parent=lamp)

# Plant (left of couch)
plant = empty("Plant", (-1.75, 0.95, 0))
cylinder("Pot", (0, 0, 0.22), 0.2, 0.44, M["pot"], r2=0.24, parent=plant)
for i in range(14):
    a = random.uniform(0, math.tau)
    r = random.uniform(0.05, 0.22)
    h = random.uniform(0.6, 1.3)
    leaf = sphere("Leaf", (math.cos(a) * r, math.sin(a) * r, h), (0.16, 0.06, 0.28), M["plant"], plant, 16)
    leaf.rotation_euler = (random.uniform(-0.6, 0.6), random.uniform(-0.6, 0.6), a)

# ---------------------------------------------------------------------------
# The Speaker (stylized seated character)
# ---------------------------------------------------------------------------
SEAT_Z = 0.58
person = empty("Speaker", (-0.45, 0.55, SEAT_Z))   # hip centre, sits on left cushion

# Pelvis & torso
pelvis = sphere("Pelvis", (0, 0, 0.02), (0.19, 0.14, 0.1), M["pants"], person)
torso = empty("Torso_pivot", (0, 0, 0.03), (math.radians(-6), 0, 0), person)  # slight lean back
cylinder("Torso", (0, 0, 0.27), 0.17, 0.5, M["blazer"], r2=0.21, parent=torso)
sphere("Chest", (0, 0, 0.5), (0.21, 0.13, 0.08), M["blazer"], torso)
box("Shirt_V", (0, -0.12, 0.42), (0.11, 0.02, 0.18), M["shirt"], parent=torso).rotation_euler.x = math.radians(-8)
sphere("Lav_Mic", (0.05, -0.135, 0.43), (0.012,) * 3, M["metal"], torso)
cylinder("Neck", (0, 0, 0.6), 0.055, 0.14, M["skin"], parent=torso)
sphere("Collar", (0, -0.02, 0.54), (0.09, 0.08, 0.03), M["shirt"], torso)

# Head
head = empty("Head_pivot", (0, 0, 0.66), parent=torso)
sphere("Head", (0, 0, 0.13), (0.105, 0.115, 0.135), M["skin"], head)
sphere("Jaw", (0, -0.02, 0.06), (0.085, 0.09, 0.07), M["skin"], head)
hair = sphere("Hair", (0, 0.015, 0.175), (0.112, 0.12, 0.11), M["hair"], head)
sphere("Hair_Back", (0, 0.05, 0.12), (0.105, 0.08, 0.11), M["hair"], head)
for s in (-1, 1):
    sphere(f"Ear_{s}", (s * 0.105, 0.0, 0.12), (0.015, 0.03, 0.035), M["skin"], head)
nose = cylinder("Nose", (0, -0.12, 0.11), 0.018, 0.05, M["skin"], rot=(math.radians(90), 0, 0), r2=0.004, verts=16, parent=head)

eyes = []
for s in (-1, 1):
    eye = sphere(f"Eye_{s}", (s * 0.038, -0.098, 0.14), (0.017, 0.012, 0.017), M["eye"], head, 16)
    sphere(f"Iris_{s}", (0, -0.85, 0), (0.6, 0.3, 0.6), M["iris"], eye, 16)
    brow = box(f"Brow_{s}", (s * 0.04, -0.105, 0.175), (0.038, 0.01, 0.008), M["hair"], 0.003, head)
    brow.rotation_euler.y = math.radians(-8 * s)
    eyes.append((eye, brow))

mouth = empty("Mouth_pivot", (0, -0.103, 0.065), parent=head)
sphere("Mouth_Inside", (0, 0, 0), (0.03, 0.01, 0.012), M["mouth"], mouth, 16)
upper_lip = sphere("Upper_Lip", (0, -0.004, 0.009), (0.032, 0.008, 0.006), M["lips"], mouth, 16)
lower_lip = sphere("Lower_Lip", (0, -0.004, -0.009), (0.03, 0.008, 0.007), M["lips"], mouth, 16)

# Legs (thighs forward along -Y, shins down)
leg_ends = []
for s in (-1, 1):
    thigh, knee = limb(f"Thigh_{s}", person, (s * 0.1, 0.0, 0.0),
                       (math.radians(-88), 0, math.radians(s * 4)), 0.44, 0.085, 0.07, M["pants"])
    shin, ankle = limb(f"Shin_{s}", knee, (0, 0, 0), (math.radians(80), 0, 0), 0.47, 0.065, 0.05, M["pants"])
    shoe = box(f"Shoe_{s}", (0, -0.06, -0.03), (0.1, 0.24, 0.07), M["shoe"], 0.025, ankle)
    shoe.rotation_euler.x = math.radians(8)

# Arms
arms = {}
for s in (-1, 1):
    shoulder, elbow_e = limb(f"UpperArm_{s}", torso, (s * 0.23, 0.0, 0.5),
                             (math.radians(-20), math.radians(s * 12), 0), 0.3, 0.06, 0.05, M["blazer"])
    forearm, wrist = limb(f"Forearm_{s}", elbow_e, (0, 0, 0), (math.radians(-75), 0, 0),
                          0.27, 0.048, 0.04, M["blazer"])
    cylinder(f"Cuff_{s}", (0, 0, -0.005), 0.042, 0.02, M["shirt"], parent=wrist)
    hand = sphere(f"Hand_{s}", (0, 0, -0.06), (0.04, 0.022, 0.06), M["skin"], wrist)
    sphere(f"Thumb_{s}", (s * -0.03, -0.01, -0.035), (0.012, 0.012, 0.03), M["skin"], wrist)
    arms[s] = (shoulder, forearm, wrist)

# ---------------------------------------------------------------------------
# Animation: talking, blinking, head motion, gestures
# ---------------------------------------------------------------------------
# Mouth open/close (speech) - keyed with noise so it looks like syllables
for f in range(1, FRAME_END + 1, 3):
    # Short pauses between "sentences"
    pause = (f % 72) > 60
    openness = 0.0 if pause else random.uniform(0.25, 1.0)
    lower_lip.location.z = -0.009 - 0.012 * openness
    lower_lip.keyframe_insert("location", index=2, frame=f)
    mouth.scale = (1.0 - 0.15 * openness, 1, 1.0 + 1.6 * openness)
    mouth.keyframe_insert("scale", frame=f)

# Blinks
for f in (20, 85, 140, 151, 205):
    for eye, brow in eyes:
        for df, sz in ((-2, 0.017), (0, 0.002), (2, 0.017)):
            eye.scale.z = sz
            eye.keyframe_insert("scale", index=2, frame=f + df)

# Eyebrows raise on emphasis
for f in (1, 30, 36, 44, 110, 116, 124, 180, 186, 194):
    raise_ = 0.01 if f in (36, 116, 186) else 0.0
    for _, brow in eyes:
        brow.location.z = 0.175 + raise_
        brow.keyframe_insert("location", index=2, frame=f)

# Head: base nods + organic noise
for f, (rx, rz) in {1: (0, 0), 40: (-6, 8), 80: (4, -4), 120: (-3, 12), 160: (5, 0),
                    200: (-4, -10), FRAME_END: (0, 0)}.items():
    head.rotation_euler = (math.radians(rx), 0, math.radians(rz))
    head.keyframe_insert("rotation_euler", frame=f)
add_noise(head, "rotation_euler", 0, 0.08, 6)
add_noise(head, "rotation_euler", 1, 0.05, 10)
add_noise(head, "rotation_euler", 2, 0.06, 8)

# Breathing / torso sway
for f, rx in ((1, -6), (60, -4), (120, -7), (180, -4), (FRAME_END, -6)):
    torso.rotation_euler.x = math.radians(rx)
    torso.keyframe_insert("rotation_euler", index=0, frame=f)
add_noise(torso, "rotation_euler", 2, 0.03, 20)

# Hand gestures: (shoulder X, shoulder Y, elbow X, wrist X) in degrees
REST = (-20, 12, -75, 10)
GESTURES = [
    (1,   REST, REST),
    (24,  (-45, 25, -60, -20), REST),                 # right hand explains
    (48,  (-55, 35, -45, -30), (-30, 15, -80, 0)),
    (72,  REST, (-50, 30, -55, -25)),                 # left hand joins
    (96,  (-60, 30, -50, -35), (-60, 30, -50, -35)),  # both hands open
    (120, (-40, 20, -70, 0), (-35, 18, -70, 0)),
    (150, (-65, 15, -30, -40), REST),                 # pointing / emphasis
    (180, REST, (-55, 30, -55, -20)),
    (210, (-50, 30, -55, -25), (-45, 25, -60, -20)),
    (FRAME_END, REST, REST),
]
for f, right, left in GESTURES:
    for s, pose in ((1, right), (-1, left)):
        shoulder, forearm, wrist = arms[s]
        sx, sy, ex, wx = pose
        shoulder.rotation_euler = (math.radians(sx), math.radians(sy * s), 0)
        forearm.rotation_euler = (math.radians(ex), 0, 0)
        wrist.rotation_euler = (math.radians(wx), 0, 0)
        for o in (shoulder, forearm, wrist):
            o.keyframe_insert("rotation_euler", frame=f)
for s in (-1, 1):
    shoulder, forearm, wrist = arms[s]
    add_noise(shoulder, "rotation_euler", 0, 0.05, 12)
    add_noise(forearm, "rotation_euler", 0, 0.06, 9)

# ---------------------------------------------------------------------------
# Lighting
# ---------------------------------------------------------------------------
def area_light(name, loc, energy, size, color, target):
    data = bpy.data.lights.new(name, "AREA")
    data.energy = energy
    data.size = size
    data.color = color
    obj = bpy.data.objects.new(name, data)
    scene.collection.objects.link(obj)
    obj.location = loc
    direction = Vector(target) - Vector(loc)
    obj.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
    return obj

face = (-0.45, 0.45, 1.3)
area_light("Key_Light", (1.4, -2.2, 2.4), 170, 1.6, (1.0, 0.92, 0.82), face)
area_light("Fill_Light", (-2.4, -1.8, 1.6), 45, 2.5, (0.8, 0.88, 1.0), face)
area_light("Rim_Light", (-1.6, 1.3, 2.6), 160, 0.8, (1.0, 0.85, 0.7), face)
lamp_pt = bpy.data.lights.new("Lamp_Bulb", "POINT")
lamp_pt.energy = 60
lamp_pt.color = (1.0, 0.7, 0.4)
lamp_pt.shadow_soft_size = 0.15
lp = bpy.data.objects.new("Lamp_Bulb", lamp_pt)
scene.collection.objects.link(lp)
lp.location = (1.65, 0.9, 1.6)

world = scene.world or bpy.data.worlds.new("World")
scene.world = world
world.use_nodes = True
bg = world.node_tree.nodes.get("Background")
bg.inputs["Color"].default_value = (0.05, 0.05, 0.06, 1)
bg.inputs["Strength"].default_value = 0.25

# ---------------------------------------------------------------------------
# Camera (gentle push-in)
# ---------------------------------------------------------------------------
target = empty("Camera_Target", (-0.3, 0.4, 0.95))
cam_data = bpy.data.cameras.new("Camera")
cam_data.lens = 40
cam_data.dof.use_dof = True
cam_data.dof.focus_object = head
cam_data.dof.aperture_fstop = 2.8
cam = bpy.data.objects.new("Camera", cam_data)
scene.collection.objects.link(cam)
con = cam.constraints.new("TRACK_TO")
con.target = target
con.track_axis = "TRACK_NEGATIVE_Z"
con.up_axis = "UP_Y"
scene.camera = cam
cam.location = (1.3, -3.6, 1.25)
cam.keyframe_insert("location", frame=1)
cam.location = (0.9, -3.0, 1.2)
cam.keyframe_insert("location", frame=FRAME_END)

# ---------------------------------------------------------------------------
# Render settings
# ---------------------------------------------------------------------------
scene.render.engine = "CYCLES"
scene.cycles.samples = 96
scene.cycles.use_denoising = True
scene.render.resolution_x = 1920
scene.render.resolution_y = 1080
scene.view_settings.view_transform = "AgX" if "AgX" in [i.identifier for i in
    scene.view_settings.bl_rna.properties["view_transform"].enum_items] else "Filmic"
scene.frame_set(48)

# ---------------------------------------------------------------------------
# Save / preview when run from the command line
# ---------------------------------------------------------------------------
if bpy.app.background and OUT_DIR != "//":
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT_DIR, "speaker_couch_scene.blend"))
    if os.environ.get("SKIP_PREVIEW") != "1":
        scene.render.filepath = os.path.join(OUT_DIR, "speaker_couch_preview.png")
        bpy.ops.render.render(write_still=True)
print("Speaker-on-couch scene built.")
