pattern.png records the selected fixed-scale view. fields.npz stores all fields in float64.
recipe.json records presets, seed, update count, brush edits and source fingerprints.
Replay from the repo root:
.venv\Scripts\python.exe -B -m src.genesis_sandbox --replay "C:\Users\joshu\Source\Repos\Genesis-Scheme-Simulator\results\vacancy_lab_2026-11-01\exports\20261101T204324915995Z_seed7_u1000\recipe.json"
Replay requires matching dynamics sources; the saved field snapshot remains available independently.
