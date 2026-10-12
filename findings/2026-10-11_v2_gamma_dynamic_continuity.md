# 2026-10-11 - V2-gamma tracks survive through change but do not preserve bounded scale

**Source:** `genesis_v2_gamma_dynamic_recovery.py --N 64 --cutoff 0.75 --seeds 10 --recovery-frames 1000`
**Status:** preliminary negative individuation result
**Owner:** Joshua

## Headline

Motion-aware tracking resolves the ambiguity in the fixed-mask recovery test:
gamma candidates usually remain consecutively matchable over 1,000 frames, but
they do not remain bounded at an approximately stable scale. Most tracks grow
substantially, often by merging into much larger relation domains.

Gamma therefore demonstrates causal boundaries and continuity through change,
but not yet stable individuation.

## Protocol

The prior causal branches were followed for 1,000 frames: untouched control,
candidate-boundary weakening, and exact-shape background weakening. A track
was matched to its immediately prior region every 25 frames at IoU at least
0.15, allowing a region to move or transform. Three consecutive missed
matches ended a track.

## Results

| Branch | Active at 1,000 frames | Median initial area | Median final area |
| --- | ---: | ---: | ---: |
| Control | 9 / 10 | 107 | 763 |
| Candidate weakened | 10 / 10 | 107 | 1103 |
| Background weakened | 9 / 10 | 107 | 768 |

In the exceptional seed 8, the control and background tracks ended at frame
700, while the candidate-weakened branch remained traceable and expanded from
117 to 1267 cells. This is not evidence of superior recovery: it illustrates
that continuity can be achieved by merger into a larger region.

## Interpretation

1. Fixed-mask overlap was correctly identifying substantial change, but could
   not tell movement or transformation from disappearance.
2. Consecutive tracking shows that the structures often continue, yet their
   growing area means they are not stable, bounded individuals under the
   current model.
3. Boundary weakening can alter the coarsening path, but it does not establish
   restoration of the original bounded candidate.
4. The present gamma rule set lacks a demonstrated **scale-selection or
   renewal mechanism**. That is the precise model limitation, not a refutation
   of the wider potentiality/actuality research direction.

## Next Hypothesis Discipline

A time-varying or pulsed process is a legitimate next hypothesis only if it
has a defined role: for example, periodic or state-triggered renewal could
oppose indefinite boundary decay and coarsening. A global pulse that merely
creates transient texture would not answer the problem.

Before implementation, state a counterfactual: a proposed renewal mechanism
must produce a reproducible bounded-area distribution and longer bounded-track
survival than gamma under the same observer sweep. Otherwise it is a rejected
specific mechanism, not a rescue parameter.

## Related Files

- `genesis_v2_gamma_dynamic_recovery.py`
- `genesis_v2_gamma_recovery.py`
- `src/genesis_v2_beta/objects.py`
- `results/v2_gamma_dynamic_recovery_batch1.json`
- `results/v2_gamma_dynamic_recovery_batch2.json`
- `results/v2_gamma_dynamic_recovery_batch3.json`
