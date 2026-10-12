# Relation Memory Raises Tension but Does Not Stabilize V2 Bridge Candidates

## Headline

Adding remembered edge incompatibility to the V1-derived P/A bridge increased
stored tension and pair-line compression slightly, but did not improve tracked
vortex-pair persistence. At the tested strength, relation memory is not a
stabilization mechanism.

## Comparison

Both conditions used the first P-to-A bridge substrate over five `N=64`,
2,000-frame runs, sampled every 25 frames. The intervention added only:

- relation-memory rate `0.30`;
- relation-memory decay `0.05`;
- relation-memory contribution to tension `0.20`.

Vortex-pair candidates were observed by the existing read-only defect and
pair-line trackers. A persistent candidate had a tracked pair age of at least
100 frames.

## Median Final Measurements

| Condition | P/A alignment | Mean tension | Relation memory | Persistent pairs | Pair-line compression |
|---|---:|---:|---:|---:|---:|
| P-to-A bridge | 0.2733 | 0.1019 | 0.0000 | 117 | 0.000018 |
| + relation memory | 0.2679 | 0.1166 | 0.1484 | 117 | 0.000028 |

The median candidate maximum age remained 25 frames in both conditions.

## Interpretation

The intervention was causally active: relation memory accumulated, P/A stayed
distinct, and inherited structural tension increased. Yet the candidate
population did not become more persistent. This rules out the claim that this
single passive-memory link, at the specified regime, supplies the missing
stabilization.

## Next Test

Do not add another mechanism or tune toward a preferred result. First run a
predeclared, modest sweep of relation-memory tension strength with fixed seeds
and all other parameters fixed. It must report both loss of P/A distinction and
candidate persistence, so a superficially long-lived regime cannot hide a
collapse into ordinary alignment.
