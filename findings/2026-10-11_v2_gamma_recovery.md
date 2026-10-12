# 2026-10-11 - V2-gamma boundary weakening partially recovers but does not return to control by 1,000 frames

**Source:** `genesis_v2_gamma_recovery.py --N 64 --cutoff 0.75 --seeds 6 --recovery-frames 1000`
**Status:** preliminary long-horizon recovery result
**Owner:** Joshua

## Headline

After direct weakening, a gamma candidate's perimeter boundary partially
rebuilds over 1,000 frames but remains below the untouched control in all six
seeds. The fixed initial mask loses identity overlap even in the control by the
end of the horizon, so this experiment does not establish recovery of the
candidate as a continuing individual.

## Protocol

The candidate-boundary weakening and exact-shape background-weakening controls
from the causal study were followed for 1,000 frames rather than 400. The
candidate's original mask remained the reference for this first long-horizon
pass.

## Median Trajectory

| Frames after intervention | Control boundary | Weakened boundary | Background-weakened boundary | Control overlap | Weakened overlap | Background-weakened overlap |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 0 | 0.307 | 0.046 | 0.307 | 1.000 | 0.498 | 1.000 |
| 100 | 0.289 | 0.073 | 0.289 | 0.809 | 0.481 | 0.783 |
| 400 | 0.239 | 0.116 | 0.239 | 0.480 | 0.380 | 0.475 |
| 700 | 0.208 | 0.138 | 0.207 | 0.252 | 0.230 | 0.251 |
| 1000 | 0.194 | 0.154 | 0.193 | 0.081 | 0.081 | 0.080 |

Final weakened/control boundary ratios ranged from `0.655` to `0.852` across
the six seeds. Thus the boundary gap narrows but does not close over the
observed horizon.

## Interpretation

1. Gamma shows partial structural restoration of a weakened boundary, but not
   demonstrated return to the control trajectory.
2. The causal identity penalty is strongest early and becomes unmeasurable by
   1,000 frames because the untouched control no longer overlaps its original
   mask either.
3. This exposes a measurement limit, not evidence that the candidate has
   necessarily ceased: an object can move or transform while preserving
   identity. A fixed-mask overlap cannot distinguish that from loss.
4. The next experiment must use motion-aware, consecutive-sample region
   tracking in each branch. It should report track survival, area trajectory,
   centroid displacement, and boundary trajectory after candidate versus
   background weakening.

## Related Files

- `genesis_v2_gamma_recovery.py`
- `genesis_v2_gamma_boundary_causality.py`
- `src/genesis_v2_beta/objects.py`
- `results/v2_gamma_recovery.json`
