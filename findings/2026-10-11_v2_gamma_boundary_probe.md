# 2026-10-11 - V2-gamma creates persistent relation-bounded components, not yet an object class

**Source:** `genesis_v2_gamma_measure.py --N 64 --frames 2000 --seeds 3` and `genesis_v2_gamma_domains.py --N 64 --frames 2000 --seeds 5`
**Status:** preliminary structural result
**Owner:** Joshua

## Headline

V2-gamma adds one explicit state variable: edge-boundary strength. Sustained
P/A difference raises a boundary, and the boundary lowers relation
permeability across that edge. In the low P-to-A coupling regime, the new
mechanism maintains a distinct P/A field and produces relation-bounded
components that can be matched across samples.

This is evidence of **segmentation and persistence under a declared observer**.
It is not yet evidence for a stable object class, autonomy, or a metaphysical
claim.

## Baseline Gate

At `N=64`, `2000` frames, `P -> A = 0.05`, relation gain `0.55`, boundary rate
`0.18`, and boundary decay `0.04`, the three seed tail means were:

| Seed | P/A alignment | Boundary mean | Boundary standard deviation |
| ---: | ---: | ---: | ---: |
| 1 | 0.1827 | 0.2445 | 0.2940 |
| 2 | 0.2860 | 0.2368 | 0.2925 |
| 3 | 0.4198 | 0.2395 | 0.2907 |

The boundary field is both nonzero and heterogeneous, while P/A alignment
remains well below the beta collapse band.

## Domain Census

The census sampled every 100 frames, required an area of at least 24 cells,
and called a track persistent after five matched samples. It swept the
relation-permeability cutoff rather than selecting one favorable value.

| Cutoff | Persistent tracks across five seeds | Largest persistent component fraction by seed |
| ---: | --- | --- |
| 0.55 | 10-16 | 0.971-0.982 |
| 0.60 | 26-33 | 0.937-0.966 |
| 0.65 | 33-40 | 0.866-0.919 |
| 0.70 | 30-40 | 0.598-0.864 |
| 0.75 | 31-39 | 0.071-0.260 |

At `0.75`, the median persistent track had eight samples, maximum area 68
cells, coherence 0.93, and boundary contrast 0.61. Some medium components
persisted for 13-19 of 20 samples, but their scale varied markedly by seed.

## Interpretation

1. The gamma boundary rule is doing more than beta's coherence rule: it makes
   relation-bounded partitions observable and trackable.
2. The result is cutoff-sensitive. Low cutoffs recover one dominant component;
   high cutoffs break it into components of variable number and scale.
3. Therefore gamma has cleared a **boundary-and-identity scaffold** gate, but
   has not cleared a **stable individuation** gate. Calling these components
   higher-order objects would be premature.
4. The next discriminating test is not another visualization. It should test
   whether candidate domains have an observer-robust scale and whether a
   localized perturbation leaves their identity, boundary, or recovery
   behavior distinguishable from the surrounding field.

## Localized Perturbation Follow-Up

At frame 1200, the largest relation-bounded component at cutoff `0.75` was
selected in each of five seeds. A radius-four patch centered inside it received
a `pi/2` actuality-orientation perturbation. An otherwise identical clone was
the unperturbed control, and both were run a further 400 frames.

| Seed | Initial component area | Control overlap | Perturbed overlap | Inside delta | Outside delta |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | 90 | 0.422 | 0.441 | 0.492 | 0.005 |
| 2 | 148 | 0.705 | 0.655 | 0.166 | 0.003 |
| 3 | 89 | 0.478 | 0.483 | 0.364 | 0.005 |
| 4 | 66 | 0.482 | 0.426 | 0.378 | 0.004 |
| 5 | 124 | 0.349 | 0.349 | 0.004 | 0.000 |

The perturbation remained spatially localized in four seeds: after 400 frames,
the inside difference was 33-166 times the outside difference. The matched
component's overlap was usually close to the control's natural overlap, though
the control itself was only moderately stable.

This is **not** evidence that the selected component protects itself. Relation
coupling alone may localize a disturbance. The next required control applies
the same patch just outside a selected component and compares containment,
recovery, and identity continuity. Only a difference between inside and
outside perturbations would support an object-specific interpretation.

## Related Files

- `src/genesis_v2_gamma/core.py`
- `src/genesis_v2_beta/objects.py`
- `genesis_v2_gamma_measure.py`
- `genesis_v2_gamma_domains.py`
- `genesis_v2_gamma_perturb.py`
- `results/v2_gamma_baseline_smoke.json`
- `results/v2_gamma_domains.json`
- `results/v2_gamma_perturbation.json`
