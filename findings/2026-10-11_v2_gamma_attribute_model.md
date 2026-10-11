# 2026-10-11 - V2-gamma simple attributes do not robustly improve held-out persistence prediction

**Source:** `genesis_v2_gamma_attribute_model.py --sizes 64 96 --cutoffs 0.70 0.75 0.80 --seeds 6`
**Status:** preliminary negative result
**Owner:** Joshua

## Headline

Gamma candidate masks forecast their own identity better than background, but
the current simple attributes do not materially improve held-out forecasts of
*how much* identity a candidate retains beyond lattice size, observer cutoff,
and area.

This is a useful constraint. It prevents us from treating coherence, boundary
contrast, and perimeter permeability as established object attributes merely
because they are measurable.

## Protocol

The dataset contains 285 candidate observations from six seeds, lattice sizes
64 and 96, cutoffs 0.70, 0.75, and 0.80, and four checkpoints per condition.
The target is 200-frame future identity overlap. Entire seeds were held out,
so test rows came from unseen system evolutions.

The fixed ridge models were:

| Model | Features |
| --- | --- |
| Baseline | Area fraction, lattice size, cutoff |
| Full | Baseline plus coherence, boundary contrast, perimeter permeability |

## Held-Out Results

| Model | MAE | RMSE | Pooled held-out R2 |
| --- | ---: | ---: | ---: |
| Baseline | 0.1454 | 0.1790 | 0.2268 |
| Full | 0.1443 | 0.1785 | 0.2314 |

The full model improves pooled RMSE by only `0.0005` (about 0.3%). Its fold
results are mixed: the full model is better in seeds 1 and 3, but worse in
seeds 2, 4, and 6. Both models fail to beat a training-mean reference on held
seed 5.

## Interpretation

1. The current candidates have discriminable persistence relative to
   background masks, but their currently measured attributes do not yet form a
   robust explanatory model of persistence.
2. Size, cutoff, and area carry most of the weak predictive signal presently
   available.
3. Adding more correlational features without a new mechanism would be
   fishing. The next legitimate experiment is causal: selectively weaken or
   strengthen a candidate's boundary relations and compare its identity and
   recovery against the same intervention applied to an equal-sized background
   region.
4. A causal boundary effect would support the claim that the boundary is an
   active constraint in the candidate's continuation. It would still not prove
   autonomy or metaphysical validity.

## Related Files

- `genesis_v2_gamma_attribute_model.py`
- `src/genesis_v2_gamma/probes.py`
- `results/v2_gamma_attribute_model.json`
