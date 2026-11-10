---
Area: Experiments
datetime_stamp: 2026-11-01T00:00:00-05:00
status: complete
confidence: vetted
tags:
  - genesis-scheme
  - binding-response
  - calibration
  - method-limitation
links:
  - "[[Structural Binding Response — Milestone]]"
  - "[[Experiments Index]]"
  - "[[Audit Ledger]]"
summary: All eight nonsham relocations preserve intended charges but exceed the declared displacement roundtrip error budget; the response study is not run, and no binding conclusion is drawn.
canonical: false
---

# Structural Binding Response — Relocation Calibration

## Result in plain language

**We can move the vortex cores, but this method distorts their retained
structural neighborhoods too much to interpret a binding response.**

Both zero-movement shams pass. All eight nonsham cases fail the displacement
error budget, despite exact expected charge maps, correct grid-resolved core
movement and essentially exact protected core-corner transport. Stage C was
not run. This is a method limitation, not a negative result about Genesis's
ability to bind structures.

## What was tested

The fixed seed 1005/3001 archives from the preflight supply full minimal-V1
states. Five arms per state: sham, relative stretch/compression, and common
translation in both directions. Every nonsham core moves one cell along the
dominant Cartesian pair axis. A rigid inner radius1 and cosine taper to radius3
define an invertible periodic displacement map with Lipschitz bound pi/4.
Fields are sampled bilinearly; theta uses complex phasors. No state evolves.

The protocol was persisted before evaluating the ten cases. Tests cover
periodic integer sampling, exact sham, winding-map relocation, core-state
transport, periodic seam crossing, detection of a sharp-feature artifact and
rejection of invalid maps. Existing trackers and engines are unchanged; new
tracker IDs are explicitly assigned at validated destination locations.

## Numerical outcome

| Quantity | Range over eight nonsham cases | Declared limit |
| --- | ---: | ---: |
| Support roundtrip theta phasor RMS | 0.0330–0.0529 | 0.35 |
| Support roundtrip tension relative L2 | 14.5%–32.6% | 25% |
| Support roundtrip displacement relative L2 | 26.0%–51.4% | 25% |
| Support roundtrip compression relative L2 | 15.8%–47.7% | 50% |
| Maximum protected core-corner error | <4.5e-16 | 1e-10 |
| Winding-map mismatches | 0 | 0 |

All eight fail displacement preservation; two also fail tension preservation.
Outside-support values remain bitwise unchanged. All input/output fields are
finite and retain the declared tension/compression bounds. Inverse residual,
phase interpolation norm, tracker assignment and arm geometry checks pass.

Roundtrip means relocating the data and sampling it back using the original
map's forward coordinates. The result measures numerical resampling distortion,
not energy consumption, physical dissipation or spontaneous relaxation. A
25% limit is a declared calibration budget, not a physical constant; it was
not relaxed after seeing these results. Only radius3 neighborhoods were moved;
transport of a complete extended wake was never established.

## Consequence for the object milestone

No binding response was measured. The model's higher-order capacity remains
unresolved. A return after this operation could combine binding, individual
pinning and relaxation of resampling damage. Moving the defects cleanly is
not enough when the structural field is part of the candidate mechanism.

The next method proposal should avoid resampling retained structure or justify
a representation-preserving intervention. A temporary dynamical probe, with
structural fields evolving under the existing rules, is one possible alternative.
It would need a new frozen calibration and pinning controls; it must not be
reported as spontaneous generation or as the already validated relocation
procedure. No new method campaign or permanent dynamical ingredient has been
added here. Neither a tolerance sweep nor a binding-response run was performed.

## Evidence and reproduction

- [Detailed finding](../../../findings/2026-11-01_binding_relocation_calibration.md).
- [Protocol](../../../results/binding_calibration_2026-11-01/protocol.json).
- [Report](../../../results/binding_calibration_2026-11-01/report.json).
- [Error-budget figure](../../../results/binding_calibration_2026-11-01/error_budget.png).
- [Local comparison](../../../results/binding_calibration_2026-11-01/relocation_detail.png).
- [Tests](../../../results/binding_calibration_2026-11-01/test_log.txt).
- [Manifest](../../../results/binding_calibration_2026-11-01/manifest.json).

Run `.venv\Scripts\python.exe -B -m src.genesis_binding.calibrate --output
results/binding_calibration_replay` with `GENESIS_USE_CUPY=False` and
`OPENBLAS_NUM_THREADS=1`. Rendering is separate:
`.venv\Scripts\python.exe -B -m src.genesis_binding.render_calibration
results/binding_calibration_replay`. Existing output directories are protected
from overwrite. All 54 tests pass. The closed V1/V2 baseline and inherited motion
archives retain their fingerprints.
