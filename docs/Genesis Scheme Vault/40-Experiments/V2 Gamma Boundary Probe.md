---
Area: Experiments
datetime_stamp: 2026-10-11T00:00:00-05:00
status: in-progress
confidence: preliminary
tags:
  - v2
  - gamma
  - boundaries
  - higher-order-objects
links:
  - "[[V2 Object Target]]"
  - "[[Higher-Order Object Detection Spec]]"
  - "[[Current Direction]]"
summary: Initial boundary and identity probe for the separate v2-gamma hypothesis.
canonical: false
---

# V2 Gamma Boundary Probe

## Question

Can a minimal boundary/permeability mechanism turn the low-coupling v2 field
into persistent bounded components without simply collapsing it into one field
or fragmenting it into noise?

## Result So Far

Gamma produces trackable relation-bounded components across a declared sweep
of permeability cutoffs. Its result is not yet observer-robust: low cutoffs
produce one dominant component, while stricter cutoffs produce multiple
components whose scale varies by seed.

This supports a boundary-and-identity scaffold, not an object claim.

A centered local perturbation usually remained within the selected component
after 400 frames, but the unperturbed component itself has only moderate
continuity. This cannot be attributed to the component without an equal
outside-component control.

The equal outside-component control now shows a location-specific response:
inside perturbations leave a substantially larger residual in the candidate
than outside perturbations, while candidate identity remains near the control.
Both locations can retain local disturbances, so this is a bounded-response
result, not evidence of autonomy.

The response also survives from `N=64` to `N=96` at nearby usable cutoffs.
Candidate scale remains observer-sensitive, although stricter cutoffs yield
similar cell-scale regions across those two lattice sizes.

Candidates now also forecast their own 200-frame identity better than
equal-shape background masks: 22 of 22 observations had higher future overlap.
The larger held-out dataset confirms that the present four attributes do not
materially explain variation within that candidate class beyond size, cutoff,
and area.

Direct boundary intervention now shows that the candidate perimeter is an
active constraint: weakening it reduces later identity in all ten matched
seeds, while matched background interventions leave the candidate near
control. A 1,000-frame follow-up finds partial boundary rebuilding but not
return to control. Fixed-mask overlap becomes inadequate at that horizon
because the unperturbed candidate itself changes location or form.

Motion-aware tracking shows the key limit: candidates often remain traceable
but coarsen into much larger domains. Gamma has causal bounded structure and
continuity, but not stable bounded individuation.

## Next Gate

Before adding any more dynamics, specify a minimal scale-selection or renewal
hypothesis that can oppose coarsening. A pulsed or cyclic mechanism is
admissible only with a defined role and a counterfactual: it must improve the
bounded-area distribution and bounded-track survival under the same observer
sweep. Then test whether candidate domains show both:

1. a scale that is robust across a modest observer sweep; and
2. a distinct response or recovery under a localized perturbation.

Failure on either gate is a result. Do not add a new rule until that failure
identifies a specific missing mechanism.

## Evidence

- `findings/2026-10-11_v2_gamma_boundary_probe.md`
- `findings/2026-10-11_v2_gamma_finite_size.md`
- `findings/2026-10-11_v2_gamma_identity_forecast.md`
- `findings/2026-10-11_v2_gamma_attribute_model.md`
- `findings/2026-10-11_v2_gamma_boundary_causality.md`
- `findings/2026-10-11_v2_gamma_recovery.md`
- `findings/2026-10-11_v2_gamma_dynamic_continuity.md`
- `results/v2_gamma_domains.json`
- `results/v2_gamma_finite_size.json`
- `results/v2_gamma_forecast.json`
- `results/v2_gamma_attribute_model.json`
- `results/v2_gamma_boundary_causality.json`
- `results/v2_gamma_recovery.json`
- `results/v2_gamma_dynamic_recovery_batch1.json`
- `results/v2_gamma_dynamic_recovery_batch2.json`
- `results/v2_gamma_dynamic_recovery_batch3.json`
