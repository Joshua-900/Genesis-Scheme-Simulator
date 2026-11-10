---
Area: Experiments
datetime_stamp: 2026-11-01T00:00:00-05:00
status: complete
confidence: vetted
tags:
  - genesis-scheme
  - binding-response
  - dynamic-probe
  - calibration
links:
  - "[[Structural Binding Response — Milestone]]"
  - "[[Structural Binding Response — Relocation Calibration]]"
  - "[[Experiments Index]]"
  - "[[Audit Ledger]]"
summary: All 16 temporary-probe cases pass safety checks, but only8 resolve the requested paired movement; no shared level calibrates every mode, and the two sampled pairs show no grid-resolved recoil after release.
canonical: false
---

# Structural Binding Response — Dynamic Probe Calibration

## Outcome

The temporary probe avoids the earlier resampling damage. It is a clean angular
intervention under its numerical safety checks, with structural state evolving
naturally. It does not reliably reposition both cores in all requested modes.
Neither fixed level passes the entire calibration, so no confirmatory Stage C
study is launched.

| State | Lower level 0.05, movement passes | Higher level 0.10, movement passes |
| --- | ---: | ---: |
| Seed 1005 | 2/4 | 4/4 |
| Seed 3001 | 0/4 | 2/4 |
| Total | 2/8 | 6/8 |

All 16 driven cases pass safety checks. Both untouched references reproduce the
archived selected-core trajectories. All 60 repository tests pass.

## Method and frozen criteria

`src/genesis_binding/dynamic_probe.py` supplies an isolated temporary torque:

\[
T_{\rm probe}(i,k)=-\frac{v}{h}E(k)
\sum_a W_a(i)\,\operatorname{clip}
\left(d_a\cdot\nabla_{\rm wrapped}\theta_i,-1,1\right).
\]

Here h=0.05 is the existing angular update multiplier, v is the nominal input
level 0.05 or 0.10, W is a fixed radius 3 cosine disk centered on each initial
core, and E(k)=sin²(pi(k+0.5)/80) during updates 0–79 and zero afterward.
The wrapped centered phase gradient uses the current theta. Native compression
locking multiplies the total torque; there is no lock compensation, core pursuit
controller, resampling or direct structural-state modification. All structural
fields respond through their original update rules.

The same two archived full-state snapshots, seeds1005/3001, supply method cases.
Four direction prescriptions at each level: stretch, compress, common positive
and negative translation along the dominant Cartesian separation axis. There
are 80 forced and80 unforced updates. Positions, winding census, tracked births
and field activity are recorded every update. Complete field frames are float32
every 5 updates, with float64 initial/release/final checkpoints.

Before collection, the protocol fixed support, envelope, both levels, duration,
tracking and all criteria. Safety requires selected identities throughout the
pulse, no excess winding census or cumulative tracker births over reference,
finite fields, bounded direct external angular increments, and exact cutoff.
These are conservative tracker observations, not physical creation/destruction
measurements. The peak direct external angular increment is about 0.0434/0.0869
radians for the lower/higher level, below the respective 0.05/0.10 bounds.

Effectiveness requires both cores to move at least 0.5 cell along their own
requested directions relative to the untouched reference at cutoff. Relative
arms must change separation in the requested direction by at least 0.5 cell;
common arms must have differential movement no greater than 1 cell. Equal nominal
input is not equal delivered torque or equal realized movement.

A level qualifies only if every mode on both states passes both categories.
The lower qualifying level would be selected, or none if both fail. No level
qualifies. The higher level's two failures are the same seed 3001 core resisting
negative axial motion under both relative stretch and common translation.

## Observations after input removal

All selected core positions remain at their release locations at every one of
the 80 subsequent updates in all 16 cases. No grid-resolved recoil is observed
within this window. This descriptive observation does not establish absent
binding generally, an asymptotic equilibrium, or a failure of Genesis.

The four prescriptions also permit holding one core's nominal input direction
fixed while changing the partner's. Every one of the16 resulting comparisons
has an identical tracked trajectory over the full 160 updates. This is consistent
with individual directional mobility/pinning at the available resolution; it
does not prove that field interactions vanish. Delivered torque can differ
because local phase gradients and compression change during each arm.

Global fields continue changing after release. The mean phase-aligned theta
phasor RMS change is about 0.00586–0.00669 per 5-update interval, computed from saved
frames. Per-update raw theta activity includes global rotation; the separate
aligned descriptor removes the best common rotation. Neither global activity
measure establishes internal dynamics of a particular higher-order object.

## Decision and limits

Keep the probe as an exploratory instrument. Do not call it a universally
calibrated displacement operation or run the proposed confirmatory restoration
study at a retrospectively chosen level. The full calibration outcome remains
negative under the declared movement requirement. This is a distinct result
from the failed spatial resampling procedure.

No bound assembly or collective restoring behavior has been demonstrated. A
next investigation should identify a plausible mechanism of collective cohesion
and a way to distinguish it from individual responses, using the inherited
analyses and these traces first. More dose escalation or indiscriminate candidate
search is not commissioned by this result.

There are only two old development states in a dense surrounding field. The
80-update release window and plaquette-center positions cannot exclude slower
or sub-grid interaction. No geometry-off causal comparison or fresh-seed
confirmation was collected. Previous V1/V2 sources, archived evidence, and
failed relocation limits are preserved. The temporary input is an experimental
poke, not spontaneous autonomous activity or a new physical fuel budget.

## Evidence

- [Detailed finding](../../../findings/2026-11-01_binding_dynamic_probe.md).
- [Frozen protocol](../../../results/binding_probe_calibration_2026-11-01/protocol.json).
- [Calibration report](../../../results/binding_probe_calibration_2026-11-01/report.json).
- [Post-collection descriptive analysis](../../../results/binding_probe_calibration_2026-11-01/descriptive_release.json).
- [Probe and release plot](../../../results/binding_probe_calibration_2026-11-01/probe_release.png).
- [Field activity](../../../results/binding_probe_calibration_2026-11-01/field_activity.png).
- [Tests](../../../results/binding_probe_calibration_2026-11-01/test_log.txt).
- [Manifest](../../../results/binding_probe_calibration_2026-11-01/manifest.json).

Reproduce with `GENESIS_USE_CUPY=False`, `OPENBLAS_NUM_THREADS=1`, and
`.venv\Scripts\python.exe -B -m src.genesis_binding.calibrate_probe --output
results/binding_probe_replay`. Render separately with
`.venv\Scripts\python.exe -B -m src.genesis_binding.render_probe results/binding_probe_replay`.
Existing result directories are protected from overwrite.
