# 2026-10-11 - Initial v2 baseline collapses P/A distinction

**Source:** `genesis_v2_measure.py --N 64 --frames 2000 --seeds 5`
**Status:** confirmed negative result
**Owner:** Joshua

## Headline

The first v2 prototype passes the structural non-relabeling intervention test,
but its unperturbed dynamics collapse potentiality and actuality into near
perfect alignment. The prototype therefore does not yet provide a sustained
co-primitive P/A regime suitable for v2 object experiments.

This is a successful measurement outcome: it identifies a concrete failure of
the first update design before visual complexity or object detectors obscure it.

## Results

Late-time means across five seeds:

| Metric | Mean across seeds | Between-seed std | Mean temporal tail std |
| --- | ---: | ---: | ---: |
| Actual order | 0.1883 | 0.0817 | 0.0067 |
| Potential strength | 0.7048 | 0.0058 | 0.0044 |
| Potential-actual alignment | 0.9996 | 0.0001 | 0.0001 |
| Relation strength | 0.9708 | 0.0030 | 0.0019 |

At frame 20, P/A alignment was only 0.36-0.40 and relation strength was
0.38-0.39. By frame 2,000, every seed had P/A alignment near 0.9997 and
relation strength near 0.97.

## Interpretation

The current direct `A -> P` attraction makes potentiality converge toward a
memory-smoothed copy of actuality. The relational update reinforces this
convergence. The fields remain technically separate and causally coupled, but
their unperturbed dynamics erase the distinction that v2 was introduced to
model.

The seed-dependent actual-order values show that not all spatial structure has
collapsed to a globally uniform orientation. The failure is specifically the
loss of an independently meaningful potentiality field.

## Design Constraint for the Next V2 Revision

Potentiality must not be updated as imitation of actuality. Actualization
should instead alter potentiality through a distinct mechanism, such as:

1. local depletion and replenishment of available alternatives;
2. redistribution of a potential distribution after actualization; or
3. a higher-dimensional potential state whose alternatives cannot be
   represented by the single actual orientation.

The next design must include a measurable **distinction persistence**
criterion. It should demonstrate that P/A remain non-identical in an
unperturbed regime while still passing both paired counterfactual directions.

## What Does Not Follow

- V2 as a research direction is not refuted.
- The paired-intervention calibration remains valid for the implemented
  scaffold.
- No conclusion follows about metaphysical potentiality or actuality.

## Related Files

- `src/genesis_v2/core.py`
- `genesis_v2_measure.py`
- `results/v2_baseline.json`
- `findings/2026-10-11_v2_intervention_calibration.md`
