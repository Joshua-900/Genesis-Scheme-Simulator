# Live torus view

Default creative Field Lab view: GPU-rendered torus with directional luminous
marks, phase tint, surface lighting, activity and arrival/departure highlights.
Right-drag orbits; wheel zooms; left-drag paints/erases/restores actual visible
nodes. Flat views remain selectable. Both comparison panels share the camera.

Simulation dynamics were preserved byte for byte, including legacy mixed
boundary conventions. Alignment/geometry are periodic; dipoles/triads are
clipped. Optional seam lines expose those boundaries. The display embedding
adds no physical degrees of freedom, simulated curvature, or inter-node forces.

76 tests pass. Native Windows GPU rendering, camera orbit, state isolation and
surface erasing pass. Old V2 demo replay passes; archived V1 fingerprints match.
The software renderer supports export and graphics fallback. Export records
camera/seams. GPU and reference rendering have slightly different glow.

`orbit.gif` shows CAMERA movement around a PAUSED field at seed 7, update 1000.
It is not evidence of continuing model evolution. `window.png` is the native
app; `gpu_surface.png` is its actual framebuffer. `verify_native.py` reproduces
those checks from the repository root.

Latest reference export: `results/torus_view_2026-11-01/exports/20261101T211218011139Z_seed7_u1000/recipe.json`.
Launch that recipe with `.venv\Scripts\python.exe -B -m src.genesis_sandbox
--replay "path/to/recipe.json"`. New sessions use `.\launch_sandbox.ps1`.
