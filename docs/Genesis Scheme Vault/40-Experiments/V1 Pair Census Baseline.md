---
Area: Experiments
datetime_stamp: 2026-10-11T00:00:00-05:00
status: complete
confidence: tentative
tags:
  - experiments
  - higher-order-objects
  - vortex-pairs
  - v1
links:
  - "[[Experiments Index]]"
  - "[[Higher-Order Object Detection Spec]]"
  - "[[Current Direction]]"
summary: Preliminary multi-seed v1 census showing persistent vortex-antivortex pair candidates with explicit detector limits.
canonical: false
---

# V1 Pair Census Baseline

The first headless pair census ran five independent v1 seeds for 10,000 frames each. It observed 5,242 vortex-antivortex pair candidates; 1,440 (27.5%) met the declared persistent-candidate threshold of age >= 100 frames and at least four observations.

The result is sufficient to justify a next-stage identity-robustness experiment. It is not sufficient to call the pairs autonomous objects, a new physical entity, or evidence for a metaphysical claim.

## What Was Observed

- Every seed produced a substantial candidate population: 1,018-1,078 observed and 251-341 persistent candidates.
- 318 persistent candidates lasted at least 1,000 frames; 90 lasted at least 5,000 frames.
- Persistent candidates had a median age of 300 frames and a 90th-percentile age of 2,900 frames.
- Their line-coherence metric was somewhat higher than the full candidate population, while their compression metric was effectively zero.

## Primary Limit

The pair is currently a greedy nearest-opposite-charge relation, not an independently bounded region. Its continuity may depend on the tracker settings. The follow-up must therefore hold v1 dynamics fixed while varying sampling and matching policy.

## Detector Control Result

The first sensitivity control has now run. The raw candidate population varies
with sampling cadence, as expected, but the long-lived tail is stable: every
one of nine detector configurations contained 300-329 candidates lasting at
least 1,000 frames and 88-93 lasting at least 5,000 frames. This supports a
robust population of long-lived v1 relational candidates, while leaving
one-to-one identity and autonomy unresolved.

See `findings/2026-10-11_pair_detector_sensitivity.md` for the full table and
limits.

## Evidence Record

The complete parameters, numbers, interpretation, and limits are recorded in `findings/2026-10-11_pair_census_baseline.md`. The raw output is `results/pair_census.json`.
