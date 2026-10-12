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
  - structural-memory
links:
  - "[[Current Direction]]"
  - "[[Genesis V2 Coupled-Field Scaffold]]"
  - "[[Higher-Order Object Detection Spec]]"
summary: The V1-preserving transition contract for a potentiality-actuality Genesis v2 engine.
canonical: false
---

# Genesis V2 Structural Bridge

## Purpose

`src/genesis_v2_integrated/` is the first V2 path that grows from the current
V1 engine instead of replacing it with a disconnected relaxation model. It is
an experimental model, not evidence that higher-order objects have appeared.

## State Mapping

| Model state | Role in the bridge |
|---|---|
| `A = theta` | Presently actualized orientation. |
| `P = (px, py)` | Latent directional possibility, initialized independently of `A`. |
| `R = (rx, ry)` | Edge-level remembered incompatibility between neighbouring P/A configurations. |
| `tau` | Cell-level accumulated relational tension. |
| `ux`, `uy` | Structural displacement caused by accumulated tension. |
| `C` | Compression derived from that displacement. |

The retained V1 sequence is: **relational mismatch -> tension -> deformation
-> compression**. V2 changes the source of relational mismatch: it can include
actual-to-actual disagreement, potential-to-actual mismatch, potential
disagreement across an edge, and remembered relational incompatibility.

## Regression Boundary

Every new V2 coupling defaults to zero. In that state, the integrated engine
must reproduce the three-rule V1 pipeline used by `genesis_object_census.py`
exactly: alignment, compression, and curvature. `tests/test_v2_integrated.py`
enforces this parity. This lets an experiment identify which added causal link,
if any, changes the result.

## Object Claim Boundary

The model does not currently create, or demonstrate, higher-order objects.
A future candidate must be independently measured as bounded, persistent,
trackable, and causally sensitive to a core or boundary intervention. Vortex
pairs and connected regions remain candidates until they meet those tests.

## Next Experiment

Start from a V1 parity run. Enable only independent potential source restoration
and potential-to-actual influence, then test whether P remains distinct from A
while changing the distribution and lifetime of V1 candidate structures. Add
relation-memory tension only after the P/A-only intervention is measured.

Run the first comparison with:

```powershell
.\.venv\Scripts\python.exe genesis_v2_integrated_probe.py
```

It writes `results/v2_integrated_potential_probe.json`. Its measurements are
P/A alignment, mean tension, mean compression, and vortex count. A difference
between conditions means only that the added P-to-A link has changed the
inherited system; it is not an object result.
