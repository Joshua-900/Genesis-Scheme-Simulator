---
Area: Implementation
datetime_stamp: 2026-11-02T00:00:00-06:00
status: prototype
confidence: tested
tags:
  - artificial-life
  - generative-art
  - physarum
summary: Independent Physarum art studio with modular simulation, presentation and controls.
---

# Physarum Studio — Artificial Life Art Lab

The user authorized this separate simulator after rejecting the previous torus
presentation as a cosmetic detour. The immediate goal is compelling visual
complexity, elegant motion and experimental control. Possible Genesis analysis
comes later; the original engines and theory records remain intact.

Run `.\launch_physarum.ps1` from the repository root. Try Silk, Estuary and
Filigree; Gather and Release blend the nodal-attraction field over simulation
ticks. Current strength controls a separate authored curl field. Drag to stir,
wheel to inspect, right-drag to pan. Palettes and exposure are presentation only.

The [module guide](../../../src/physarum_lab/README.md) is authoritative for
controls, numerical conventions, architecture and extension points. It also
explains the distinction between this model and physical cymatics or fluid
simulation. The directory follows Clean Architecture's inward dependency
principle, using a small domain/application/adapters structure without an
additional framework.

Exports contain a full-field PNG, validated numerical snapshot, RNG state,
transition progress and provenance. Loading is paused and supports continued
simulation. No previous experiment, source baseline or Genesis evidence was
replaced.

Evidence is in [the run directory](../../../results/physarum_lab_2026-11-02/).
The behavior GIF samples actual evolving model states, time-compressed. It is
not an animation of the camera or a generated illustration.


## Live formula fields

Formula editor accepts typed scalar expressions and two-expression currents.
Responses include zero contours, peaks, repelling peaks and vector motion.
Spatial scale, time speed, strength, draft previews and examples are available.
Expressions are interpreted by the restricted domain AST interpreter; unsupported
constructs and numerical failures produce messages rather than Python execution.

Draft previews and invalid applies preserve state. Runtime singularities pause
before the invalid tick. Formula configuration is saved in v2 bundles, while v1
bundles still load. The [module guide](../../../src/physarum_lab/README.md) lists
the language, units and numerical response rules. All 104 tests pass; native
scalar/vector application and exact snapshot continuation were checked. See
[formula QA](../../../results/physarum_formulas_2026-11-02/qa.json).
