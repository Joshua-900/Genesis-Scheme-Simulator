# 2026-10-11 - V2-gamma candidates forecast their own identity better than equal-shape background masks

**Source:** `genesis_v2_gamma_forecast.py --N 64 --cutoff 0.75 --seeds 5`
**Status:** preliminary identity-prediction result
**Owner:** Joshua

## Headline

Observer-defined gamma candidates retain substantially more spatial identity
over a 200-frame horizon than equal-shape translations placed in unoccupied
background. Across 22 usable observations, every candidate outperformed its
background comparator.

This establishes a discriminable, temporally predictive candidate phenomenon.
It does not establish autonomous objects, natural kinds, or a complete model
of which candidate attributes determine persistence.

## Protocol

After 1200 warmup frames, the experiment sampled five checkpoints per seed.
At each checkpoint it selected up to three relation-bounded components at
cutoff `0.75`. Each candidate was evolved 200 frames and matched to later
components by maximal mask overlap. Its null comparator was the same mask
translated into the least currently occupied available location.

Recorded candidate attributes were area fraction, internal coherence, boundary
contrast, and mean perimeter relation permeability.

## Results

| Measure | Value |
| --- | ---: |
| Usable candidate observations | 22 |
| Candidate median future overlap | 0.729 |
| Background median future overlap | 0.156 |
| Median identity advantage | 0.558 |
| Candidate wins | 22 / 22 |

The advantage occurred in every seed, ranging from 0.136 to 0.931 across
individual observations.

## Attribute Check

The current sample is insufficient to claim that the measured attributes
predict the *degree* of persistence within the candidate class. Exploratory
Spearman associations with future overlap were weak and non-significant:

| Attribute | Spearman rho | Two-sided p |
| --- | ---: | ---: |
| Area fraction | 0.332 | 0.131 |
| Coherence | -0.246 | 0.271 |
| Boundary contrast | 0.256 | 0.251 |
| Boundary permeability | -0.247 | 0.268 |

This is an honest boundary: the model identifies a region that predicts its
own continuation relative to background, but it does not yet explain which
features make one candidate more persistent than another.

## Interpretation

1. Gamma candidates pass an identity-prediction benchmark that arbitrary
   equal-shape background masks do not.
2. That makes them more than transient visual texture under this observer.
3. The background translation is deliberately placed in low current occupancy,
   so it is a discriminating null rather than proof of a natural kind.
4. The next milestone is an out-of-sample attribute model: collect a larger,
   balanced candidate dataset across seeds, cutoffs, and lattice sizes; fit on
   part of it and test whether region-level features predict persistence on
   held-out data better than simple area or a background-only baseline.

## Related Files

- `genesis_v2_gamma_forecast.py`
- `src/genesis_v2_gamma/probes.py`
- `results/v2_gamma_forecast.json`
