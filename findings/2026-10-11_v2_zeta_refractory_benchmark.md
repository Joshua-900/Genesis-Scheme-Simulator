# 2026-10-11 - V2-zeta refractory benchmark delays but does not renew bounded domains

**Source:** `genesis_v2_zeta_sweep.py` and
`genesis_v2_zeta_stationarity.py`
**Status:** preliminary negative renewal result
**Owner:** Joshua

## Headline

V2-zeta made the cyclic hypothesis stricter than epsilon: a coherence-driven
refractory field directly suppresses future local alignment, diffuses, and
decays. It improved the intermediate-time domain distribution, but it did not
produce a measured renewal cycle or stable finite scale. The refractory field
rose monotonically toward a near-uniform plateau while one macroscopic domain
formed.

## Protocol

At `N=64`, 2,000 frames, and three seeds, the map swept refractory production
`{0.003, 0.008, 0.020}` and alignment suppression gain `{0.35, 0.65, 0.90}`.
The strongest non-saturating condition (`0.020`, `0.90`) was then sampled to
8,000 frames at 400-frame intervals for seed 1.

## Result

At 2,000 frames, increasing refractory pressure reduced the largest-domain
fraction while preserving domains:

| Production | Gain | Largest domain fraction | Mean domain count |
| ---: | ---: | ---: | ---: |
| 0.003 | 0.35 | 0.216 | 24.33 |
| 0.008 | 0.90 | 0.172 | 27.00 |
| 0.020 | 0.90 | 0.109 | 29.00 |

The long run rejected stationarity. Under the strongest tested condition,
domains progressed from `36` with largest fraction `0.070` at frame 2,000 to
`3` and `0.851` at frame 4,000, then `1` and `0.961` at frame 8,000.
Aggregate refractory mean rose from `0.483` at frame 2,000 to `0.550` at frame
8,000; it did not oscillate or show a recovery phase.

## Interpretation

1. Delayed suppression can materially slow coarsening. That is a model effect,
   not a mere visualization artifact.
2. Scaling the existing alignment drive is still only a brake. It does not
   create a self-renewing local excitation/recovery loop.
3. Across gamma, delta, epsilon, and zeta, the common result is monotonic
   relaxation toward a macroscopic coherent region. Adding fields without a
   different dynamical architecture has repeatedly delayed, not prevented,
   that attractor.
4. The next task is therefore a **dynamical-architecture audit**, not another
   v2 rule. It should identify whether the current system has an implicit
   Lyapunov-like relaxation structure and define a separate, established
   activator--recovery benchmark with explicit local excitation, inhibition,
   and measured cycle criteria.

## Related Files

- `src/genesis_v2_zeta/core.py`
- `genesis_v2_zeta_sweep.py`
- `genesis_v2_zeta_stationarity.py`
- `results/v2_zeta_regime_production003.json`
- `results/v2_zeta_regime_production008.json`
- `results/v2_zeta_regime_production020.json`
- `results/v2_zeta_stationarity_seed1.json`
