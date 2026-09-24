Repo: F:/PoCs/blender-video — code-first Blender videos. Plans: docs/SAMURAI_PLAN.md (worker protocol, conventions), docs/PRODUCTION_PLAN.md.

Environment
- Blender 5.2.2 (F:/blender/blender.exe), Python 3.13 inside Blender. Blender scripts may use only the standard library, bpy, bmesh, mathutils. numpy/soundfile only in tools/audio.py.
- You cannot run anything. The supervisor runs checks and sends you the output when something fails.

Code rules
- Type hints, short docstrings, 4-space indent. Prints only as tagged lines, e.g. print("[rig] built", flush=True).
- No bpy.ops except object.mode_set, wm.save_as_mainfile, render.render, import_scene.gltf (only in kit/sets.py) and the mesh.primitive_* calls inside studio/core.py. Build meshes with studio/core.py helpers or bmesh.
- Character-local space: +X = the character's right, +Y = forward, +Z = up. Units metres; public angles in degrees.
- Frame numbers are named constants in the project script, never magic numbers inside functions.

Blender 5.2 facts
- Set image_settings.media_type = "VIDEO" before file_format = "FFMPEG" (C.render_settings does it).
- Actions are slotted: never use action.fcurves; use C.fcurves(obj).
- hide_render does not propagate to children: use C.visible(obj, frame, on); always key frame 1 first.
- arm.matrix_world is stale until bpy.context.view_layer.update() after moving/rotating an object.
- Objects parented to bones sit at the bone TAIL: always use kit.rig.attach().
- ffmpeg 9: no glob input, -vsync is -fps_mode, -filter_script is gone (use -/vf <file>).

Owner rules
- Never overwrite or delete anything in output/ (every render is a new output/vN).
- No synthesized audio, ever: sounds come only from assets/sfx_bank.json, music from licensed files.
- Every downloaded asset needs a licence entry in assets/library/LICENSES.md.
