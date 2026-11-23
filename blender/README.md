# Speaker on a couch (Blender)

| File | What it is |
|---|---|
| `speaker_couch_scene.py` | Builds the living-room set with a cartoon speaker (10 s talking animation). |
| `speaker_couch_scene.blend` | The saved result of that script. |
| `avatar_speaker.py` | Replaces the cartoon with a realistic rigged avatar and lip-syncs it to a voice recording. |

## Put a real person on the couch

> Only use the face and voice of yourself or of someone who has agreed to it,
> and label published videos as animated or AI-generated recreations.

1. **Make the avatar** (any rigged humanoid in `.fbx`, `.glb` or `.gltf`):
   - **Character Creator 4 + Headshot**: build a realistic head from one photo, then export as FBX (Blender preset) with facial expressions or visemes.
   - **KeenTools FaceBuilder for Blender**: build a head from a few photos, put it on an MPFB/MakeHuman body, then rig it with Mixamo.
   - Any **Mixamo**-rigged character also works.
2. **Record the voice** as `.wav`, `.mp3`, `.m4a` or `.flac`.
3. **Run the script:**

```bash
blender --background --python blender/avatar_speaker.py -- --avatar person.fbx --audio voice.wav --out speaker_avatar.blend
```

Add `--render speaker.mp4` to render the video with sound. Add `--seat right` to sit on the other cushion. Add `--height 1.68` to set the person's real height in metres.

### What the script does
- **Removes the cartoon speaker** and imports the avatar. It turns the avatar to face the camera, scales it to human size and seats it on the cushion.
- **Recognises common skeletons**: Mixamo, Character Creator (`CC_Base_*`), Rigify, VRM, and generic names like `LeftArm` or `upper_arm.L`.
- **Lip-syncs to the recording**, frame by frame:
  - With mouth shape keys (ARKit `jawOpen`, Oculus `viseme_*`, CC `V_Open`, VRM `Fcl_MTH_*`), it uses them for open, wide and round mouth shapes.
  - Without them, it rotates the jaw bone instead.
- **Animates the rest of the body**: blinks (if blink shape keys exist), nods on stressed syllables, head drift, breathing, and hand gestures that start and stop with each spoken phrase.
- **Adds the audio to the timeline** and sets the animation length to match it.

The lip-sync follows the loudness and tone of the recording, not the actual words. For exact mouth shapes per sound, run the result through a phoneme-based tool afterwards (e.g. the Rhubarb Lip Sync add-on), or use facial capture (e.g. iPhone ARKit / Live Link Face).
