# 2026-10-11 - V2-gamma candidate boundaries causally constrain identity

**Source:** `genesis_v2_gamma_boundary_causality.py --N 64 --cutoff 0.75 --seeds 10`
**Status:** preliminary causal result
**Owner:** Joshua

## Headline

Directly weakening a selected candidate's stored perimeter boundary reduced its
later identity in all ten matched seeds. The same operation on an exact-shape
translation in the least occupied background location left the selected
candidate at essentially control behavior.

This is the first direct evidence that gamma's boundary is an active model
constraint on the candidate's continuation, rather than only a property the
observer reads after the fact.

## Protocol

After 1200 warmup frames, the largest relation-bounded candidate at cutoff
`0.75` was selected. Five branches were evolved for 400 frames from the same
state:

1. untouched control;
2. candidate perimeter weakened by 85%;
3. equal candidate-shape background perimeter weakened by 85%;
4. candidate perimeter strengthened by 85%; and
5. matched background perimeter strengthened by 85%.

The background mask is an exact translation of the candidate shape chosen to
minimize current domain occupancy. Identity is maximal overlap of the original
candidate mask with later relation domains.

## Results

| Branch | Median final candidate overlap |
| --- | ---: |
| Control | 0.480 |
| Background weaken | 0.475 |
| Candidate weaken | 0.393 |
| Candidate strengthen | 0.475 |
| Background strengthen | 0.480 |

Candidate weakening lowered identity relative to its own control in **10/10**
seeds. The effect ranged from 0.007 to 0.347 lower overlap. Background
interventions differed from control only by ordinary trajectory variation.

Strengthening had no uniform benefit: it improved identity strongly in some
seeds and reduced it in others. This is evidence that a boundary is a
context-dependent constraint, not a monotonic "more boundary is better" knob.

## Recovery Check

Median perimeter boundary strength was:

| Time | Control | Candidate weakened | Candidate strengthened |
| --- | ---: | ---: | ---: |
| Immediately after intervention | 0.310 | 0.047 | 0.897 |
| After 400 frames | 0.239 | 0.110 | 0.513 |

The weakened boundary partially rebuilt but remained below its control in every
seed (final ratio 0.377-0.608). The model therefore shows causal boundary
dependence, not demonstrated homeostatic recovery.

## Interpretation

1. Gamma candidates now meet a stronger criterion than persistence or
   prediction: selectively altering their boundary changes their future
   identity.
2. This is a model-level causal claim only. It does not establish autonomous
   objects, natural kinds, or a metaphysical conclusion.
3. The next gate is long-horizon recovery: determine whether a weakened
   candidate boundary and its identity converge back toward control, stabilize
   at a changed state, or decay further. Include the matched background
   intervention as the continuing control.

## Related Files

- `genesis_v2_gamma_boundary_causality.py`
- `src/genesis_v2_gamma/core.py`
- `src/genesis_v2_gamma/probes.py`
- `results/v2_gamma_boundary_causality.json`
