---
Area: Implementation
datetime_stamp: 2026-10-11T00:00:00-05:00
status: in-progress
confidence: tentative
tags:
  - implementation
  - v2
  - potentiality
  - actuality
  - relation
links:
  - "[[Genesis Commitments and Bridge Principles]]"
  - "[[Implementation Index]]"
  - "[[Current Direction]]"
summary: Experimental v2 engine scaffold with distinct coupled potentiality, actuality, and relation fields.
canonical: false
---

# Genesis V2 Coupled-Field Scaffold

`src/genesis_v2/` is a separate, experimental engine registered as
`genesis-v2`. Its state has three distinct roles:

- `P = (px, py)`: latent directional potentiality;
- `A = theta`: actualized orientation;
- `R = (rx, ry)`: dynamic horizontal and vertical relational edge weights.

The engine exists to test the constraint in [[Genesis Commitments and Bridge
Principles]], not to replace v1. Its first paired intervention passed the
implementation-level non-relabeling check: a potential-only intervention later
changed actuality, and an actuality-only intervention later changed
potentiality.

The first three-seed, three-size intervention calibration also passed: both
directions diverged for every tested condition, with larger affected regions
producing larger median effects. The next task is unperturbed v2 baseline
measurement. Object detection and visual polish come after v2 has a
characterized field-level baseline.

`genesis_v2_measure.py` is the corresponding headless harness. It records
actual order, potential strength, potential-actual alignment, and relation
strength, then summarizes each run's late-time tail separately from
between-seed variation.

## First Baseline Result

The five-seed baseline found a design failure worth preserving: P/A alignment
rose from about 0.38 to 0.9997 and relation strength rose to about 0.97. The
current direct actuality-to-potentiality attraction turns `P` into a smoothed
copy of `A`. The engine remains an experimental scaffold, not a v2 candidate
for object experiments, until potentiality has its own sustained dynamics.

See `findings/2026-10-11_v2_baseline_collapse.md`.

## Beta Revision

`src/genesis_v2_beta/` preserves alpha as a recorded failed scaffold and
introduces named relation, potential, and actuality rules. Beta's potential
field has independent source restoration and a bounded availability reservoir;
actualization consumes availability and relational difference replenishes it.
The first baseline and paired intervention checks pass, but beta remains a
prototype until a parameter-regime study identifies whether it supports
coherent persistent structures without erasing P/A distinction.

See `findings/2026-10-11_v2_beta_rule_gates.md`.
