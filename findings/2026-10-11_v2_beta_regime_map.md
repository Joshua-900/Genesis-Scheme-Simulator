# 2026-10-11 - V2-beta map isolates a distinction-preserving low-coupling regime

**Source:** `genesis_v2_beta_sweep.py --N 64 --frames 2000 --seeds 3`
**Status:** preliminary regime characterization
**Owner:** Joshua

## Headline

Potential-to-actual coupling is the dominant P/A-collapse control. Low coupling preserves substantial distinction while retaining high local spatial coherence and low global order. High coupling recreates alpha-like collapse.

No condition is yet identified as containing higher-order objects.

## Key Results

| P -> A coupling | Relation gain | P/A alignment | Neighbor coherence | Global order | Availability std |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 0.05 | 0.20 | 0.3598 | 0.9006 | 0.1293 | 0.1479 |
| 0.05 | 0.55 | 0.3217 | 0.9073 | 0.1385 | 0.1477 |
| 0.05 | 0.90 | 0.2885 | 0.9089 | 0.1307 | 0.1479 |
| 0.20 | 0.55 | 0.8789 | 0.9168 | 0.1306 | 0.0870 |
| 0.45 | 0.55 | 0.9941 | 0.9104 | 0.1135 | 0.0524 |

## Interpretation

1. High P -> A coupling is a dead end for the present aim: 0.45 recreates P/A near-identity.
2. The 0.05 band is the first viable exploration band: P/A alignment remains 0.29-0.36 while local coherence remains about 0.91.
3. Low global order combined with high local coherence indicates locally organized but globally varied configurations.
4. The next task is targeted visual inspection and a quantitative coherent-region or boundary detector, not an object claim.

## Related Files

- `genesis_v2_beta_sweep.py`
- `src/genesis_v2_beta/core.py`
- `results/v2_beta_regime_map.json`
