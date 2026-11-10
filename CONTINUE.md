# Continue — Physarum Studio (2026-11-02)

The user rejected the torus as a cosmetic detour and clarified that the objective
is visually compelling complexity as art. They authorized a separate
Physarum-inspired artificial-life simulator with optional cymatic guidance,
modular design and quality code. Genesis implementations and research remain
preserved. Do not conflate the new simulator with validation of Genesis.

Run `.\launch_physarum.ps1`. Default Silk has 90,000 agents on a 512-square
periodic field, with a short deterministic warmup, then continuous playback.
Estuary produces broader plumes; Filigree has no authored currents. Use Gather
and Release, change wave modes, stir by dragging, wheel to inspect and right-drag
to pan. The current field can be adjusted independently. Palettes/exposure are
presentation-only. PNG/state exports and paused restoration are implemented.

Read [the module guide](src/physarum_lab/README.md) for architecture, numerical
conventions, controls, CLI usage and extension points. Domain model and
mathematical fields are independent of Qt, files and graphics. Session manages
playback/guidance by ticks. Adapters handle display, storage and Qt controls.
Simulation is CPU-based; display is GPU-based, with a software fallback.

Use `.venv\Scripts\python.exe -B`, `OPENBLAS_NUM_THREADS=1`, and
`GENESIS_USE_CUPY=False` for the legacy full test suite. Native UI tests use
`QT_QPA_PLATFORM=offscreen`; normal launch uses `windows`. All 104 tests pass; see `results/physarum_formulas_2026-11-02/test_log.txt`.
Native QA covers the actual GPU framebuffer, reference agreement, palette,
zoom/pan, guidance, save/restore and measured update rate.

Evidence: `results/physarum_lab_2026-11-02/`: behavior GIF (real model evolution,
time-compressed), flow/gather/release PNGs and resumable states, native screenshot,
QA JSON/script and manifest. Full-sized guidance reduces the mean squared wave
amplitude sampled at agents from ~0.122 to ~0.011, rising again to ~0.066 after
release. This quantifies this recorded run; it is not a general biological claim.

The current field is authored analytic advection, not emergent fluid physics.
Wave guidance is a designed nodal-attraction formula, not a vibrating-plate
solver. Gathering quiets currents as well as adding nodal attraction. Aesthetic
quality remains for the user to judge; do not oversell screenshots or promise
open-ended evolution. The older Field Lab and torus remain separately runnable.

The working tree contains extensive earlier changes. No commit was made.
Preserve unrelated files and environment changes. The prior handoff is archived
at `results/physarum_lab_2026-11-02/previous_handoff.md`.


## Live formulas added

The desktop **Formula editor…** accepts scalar formulas or two velocity
expressions. Preview is non-mutating; Apply live switches the field and sets
a blended strength target. Response modes: zeros, peaks, repel peaks, vector
flow. Spatial scale, time speed, examples, and restoration to wave modes exist.
Core expression interpreter: `domain/formulas.py`; no eval, Python compilation,
attributes, imports or arbitrary calls. Applied fields are checked before each
tick; invalid drafts do not replace the active formula. Step and playback
both handle numerical errors. Numerical failure does not consume RNG or
advance guidance for the failing tick. Formula snapshots are v2; v1 loads.

See README's Live formula editor section for language, coordinate/time units,
response coefficients and limits. Native scalar/vector application, previews,
invalid input and exact saved continuation were checked on Windows/GPU.
Artifacts and QA: `results/physarum_formulas_2026-11-02/`. The module guide is
the authoritative usage reference. Existing open windows do not hot-reload;
new windows use the updated code. Do not close an older window with unsaved
user work simply to replace it.
