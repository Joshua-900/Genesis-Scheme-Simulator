# Continue — Creative Field Lab (2026-11-01)

The user shelved the Genesis research programme and redirected work to making
the sandbox visually engaging and experimental. The sandbox is now the primary
deliverable. Preserve the old engines, theory and evidence; resume research
only if the user explicitly requests it. The previous handoff is archived in
`results/vacancy_lab_2026-11-01/research_handoff_before_pivot.md`.

## Ready to use

Run `.\launch_sandbox.ps1`. Open Drop / add and click Flicker + Play.
See [Field Lab — Vacancies and Turnover](docs/Genesis%20Scheme%20Vault/30-Implementation/Field%20Lab%20%E2%80%94%20Vacancies%20and%20Turnover.md).

- Default GPU 3D torus, with orbit/zoom, real surface picking/painting, and
  optional coordinate seams. View controls are above the canvas. Right-drag
  orbits; wheel zooms; left-drag paints. Camera movement never advances the model.
- Flat luminous dashes and classic heatmap remain available; flat 2×/4× zoom.
- True missing nodes: absent bonds/triads and cleared retained state; fresh random
  angles and zero retained state on return. Holes use no-flux geometry edges.
- Manual visible Drop one / Add one, larger dropout/refill, and erase/add brushes.
- Independent constant per-tick probabilities; expected occupied fraction is
  p_in/(p_in+p_out). Preset 0.2% out/0.6% in gives expected 75% occupancy.
- Optional matched geometry comparison, phase/compression/activity views.
- Exports include torus camera/seams or flat style/zoom, full snapshots and version2 replay recipes.
  Version1 classic recipes remain supported.

## Code and checks

`src/genesis_sandbox/model.py` and `src/genesis_gallery/legacy.py` remain unchanged.
`lab_model.py` subclasses the classic model; `vacancies.py` adds the experimental
kernel. All-present states call the historical step exactly. `render.py` supplies
procedural dash pixels; `ui.py`, `export.py` and `__main__.py` expose the experiment.

All 76 tests pass, including five torus geometry/picking/export/UI contracts. The N64 demo
replays every saved field and mask exactly. Archived research baseline and
classic dynamics fingerprints match. See `results/vacancy_lab_2026-11-01/` for
preview, screenshots, QA, tests, exports and manifest.

The working tree has extensive older edits. No commit was made; preserve
unrelated edits and tracked environment files. Use PowerShell,
`.venv\Scripts\python.exe -B`, `GENESIS_USE_CUPY=False`, and
`OPENBLAS_NUM_THREADS=1`. Native tests use `QT_QPA_PLATFORM=offscreen`; normal
interactive launch uses the Windows platform. A Field Lab window may be open.

Torus renderer: `torus_gl.py` is an optional VisPy GPU raymarcher; `torus.py`
is the NumPy/Pillow reference for exports and automatic software fallback.
Native Windows GPU capture and interaction QA is in
`results/torus_view_2026-11-01/verify_native.py`; preview is `orbit.gif` (camera
motion only, paused field at update 1000). See the QA JSON and manifest there.
Alignment/geometry are periodic in both axes; legacy dipole/triad interactions
are clipped at edges. The torus visualizes periodic coordinates without changing
those historical boundary rules. It is a display embedding, not emergent 3D physics.
