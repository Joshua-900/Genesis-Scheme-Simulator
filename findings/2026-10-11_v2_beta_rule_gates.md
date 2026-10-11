# 2026-10-11 - V2-beta passes first distinction and intervention gates

**Sources:** `genesis_v2_beta_measure.py --N 64 --frames 2000 --seeds 5`; `genesis_v2_beta_intervention.py --N 64 --steps 300 --seeds 3`
**Status:** preliminary prototype result
**Owner:** Joshua

## Headline

The rule-based v2-beta revision corrects the alpha prototype's immediate P/A
collapse while preserving bidirectional counterfactual consequences. It is the
first v2 version with both an explicit rule layer and a non-collapsed
unperturbed P/A baseline.

This is a model-development gate, not evidence of higher-order objects or
metaphysical truth.

## Beta Rule Layer

1. **Relation rule:** relational weights rise around combined actual and
   potential difference, then relax toward a baseline rather than saturating.
2. **Potential rule:** a latent directional substrate has independent source
   restoration and transport. Availability is replenished by unresolved
   relational difference and depleted by actualization. It never copies `A`.
3. **Actuality rule:** realized orientation responds to both local relations
   and currently available potential.

The rule order is relation, potential, then actuality.

## Baseline Result

Across five unperturbed 64 x 64 runs of 2,000 frames:

| Metric | Tail mean across seeds | Between-seed std |
| --- | ---: | ---: |
| Actual order | 0.1236 | 0.0344 |
| Potential availability | 0.5029 | 0.0057 |
| P/A alignment | 0.8774 | 0.0227 |
| Relation strength | 0.2294 | 0.0021 |
| Availability spatial std | 0.0881 | 0.0086 |

The alignment remains substantial, but it no longer collapses toward the
alpha result of 0.9996. Availability retains spatial variation and relation
strength remains near its regulated baseline rather than saturating.

## Paired Intervention Result

Three matched-seed runs at 64 x 64 for 300 steps, with a 12% central region
rotated by pi/2:

| Direction | Final divergence, min / median |
| --- | ---: |
| Change only P; measure later A | 0.031795 / 0.035639 |
| Change only A; measure later P | 0.011895 / 0.012185 |

The untouched component had exact zero distance before every intervention.

## Interpretation

Beta clears the first two implementation gates:

- **distinction persistence:** P and A do not collapse into near identity in
  the measured baseline;
- **bidirectional consequence:** isolated changes in either component produce
  later change in the other.

It has not yet demonstrated a nontrivial regime, stable higher-order objects,
or superiority to v1. The next disciplined task is to map beta's parameter
regimes and identify whether any preserve distinction while supporting
coherent, persistent structure.

## Related Files

- `src/genesis_v2_beta/core.py`
- `genesis_v2_beta_measure.py`
- `genesis_v2_beta_intervention.py`
- `results/v2_beta_baseline.json`
- `results/v2_beta_intervention.json`
