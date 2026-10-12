# 2026-10-11 - V2-epsilon resource renewal reaches equilibrium but does not stop coarsening

**Source:** `genesis_v2_epsilon_sweep.py` and
`genesis_v2_epsilon_stationarity.py`
**Status:** preliminary negative renewal result
**Owner:** Joshua

## Headline

V2-epsilon tests a concrete version of the cyclic-renewal intuition. Local
realized coherence consumes potential availability; availability spreads and
replenishes slowly. The rule creates a substantial intermediate population of
domains at 2,000 frames, but it does not produce a sustained cycle or bounded
scale. By frame 8,000, both tested resource balances had coarsened into one
dominant domain.

## Protocol

The calibrated `N=64`, 2,000-frame, three-seed regime map swept coherence
depletion `{0.01, 0.03, 0.08}` and availability replenishment
`{0.015, 0.035, 0.070}`. A middle balance (`depletion=0.03`,
`replenishment=0.035`) and resource-poor edge (`0.08`, `0.015`) were then
sampled through 8,000 frames for seed 1.

## Result

At frame 2,000, all nine mapped settings retained about 23--25 relation
domains; their largest-domain fractions ranged from `0.152` to `0.193`.
The apparent population is therefore a real intermediate-time effect, not a
reporting artifact.

The long runs reject late-time stability:

| Setting | Frame | Resource mean | Domain count | Largest domain fraction |
| --- | ---: | ---: | ---: | ---: |
| middle balance | 2,000 | 0.257 | 32 | 0.104 |
| middle balance | 4,000 | 0.253 | 3 | 0.898 |
| middle balance | 8,000 | 0.252 | 1 | 0.955 |
| resource-poor | 2,000 | 0.079 | 31 | 0.107 |
| resource-poor | 4,000 | 0.077 | 4 | 0.878 |
| resource-poor | 8,000 | 0.076 | 1 | 0.965 |

## Interpretation

1. The resource does not oscillate or renew a population of domains. It
   rapidly reaches a near-constant equilibrium while coarsening proceeds.
2. This is a valuable correction to the intuition that a depletion and
   replenishment term automatically produces cycles. It does not; passive
   negative feedback can simply settle.
3. A genuine cyclic hypothesis needs delayed feedback that directly changes
   the local consolidation process, with a recovery or refractory phase. It
   must be defined as a coupled dynamic mechanism, not imposed as a global
   clock.
4. Such a mechanism resembles a known activator--recovery or
   activator--inhibitor class. That is acceptable as a formal benchmark, but
   it would not itself establish novelty for Genesis Scheme. The relevant
   question is whether the P/A/R interpretation supplies a distinctive,
   testable constraint.

## Related Files

- `src/genesis_v2_epsilon/core.py`
- `genesis_v2_epsilon_sweep.py`
- `genesis_v2_epsilon_stationarity.py`
- `results/v2_epsilon_regime_map.json`
- `results/v2_epsilon_stationarity_seed1.json`
- `results/v2_epsilon_stationarity_low_resource_seed1.json`
