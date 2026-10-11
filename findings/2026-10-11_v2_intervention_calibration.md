# 2026-10-11 - V2 bidirectional intervention effect persists across seeds and sizes

**Source:** `genesis_v2_intervention.py --N 64 --steps 300 --seeds 3 --region-fractions 0.06,0.12,0.20`
**Status:** preliminary calibration result
**Owner:** Joshua

## Headline

The v2 coupled-field prototype passed its first multi-seed, multi-size
intervention calibration. For every tested seed and intervention size,
potential-only changes produced later actual divergence and actual-only changes
produced later potential divergence. The median effect increased with the
intervention region.

This establishes the intended implementation behavior. It does not show that
the model produces higher-order objects, superior explanatory power, or a
metaphysical result.

## Configuration

| Setting | Value |
| --- | ---: |
| Grid | 64 x 64 |
| Steps | 300 |
| Seeds | 1-3 |
| Rotation | pi/2 |
| Intervention radii | 6%, 12%, 20% of grid width |

## Results

| Intervention radius | P -> A final divergence, min / median | A -> P final divergence, min / median |
| ---: | ---: | ---: |
| 6% | 0.005121 / 0.005647 | 0.005303 / 0.007647 |
| 12% | 0.015054 / 0.025707 | 0.026204 / 0.028171 |
| 20% | 0.058755 / 0.067593 | 0.067405 / 0.070425 |

All paired runs began with exact zero distance in the component not directly
intervened upon.

## Interpretation

1. `P`, `A`, and `R` have distinct operational roles in this prototype.
2. The paired counterfactual is reproducible across the first three seeds.
3. The intervention response grows with the affected region, as expected for
   a spatial coupled-field model.
4. This is a structural gate, not a discovery of emergent v2 objects.

## Next Experiment

Characterize unperturbed v2 behavior across seeds before adding visual tools
or adapting the object census. Measure actual order, potential strength,
potential-actual alignment, and relation strength over time. Then compare
those distributions against the v1 baseline where comparable.

## Related Files

- `src/genesis_v2/core.py`
- `genesis_v2_intervention.py`
- `results/v2_paired_intervention.json`
- `findings/2026-10-11_v2_paired_intervention_scaffold.md`
