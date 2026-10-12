# Local P Rotation Did Not Produce a Candidate-Specific Far-Field Response

## Design

Thirty fixed-seed P/A bridge runs were burned in for 1,000 frames. For each
selected pair candidate, a 90-degree rotation was applied to P in a radius-5
disk. An equal-radius background disk was tested from the same starting state.
Each perturbed branch and an untouched copy then ran in lockstep for 250
frames. Measurements excluded a radius-10 disk around the intervention, so
they describe only far-field differences.

## Results

At 250 frames, the paired medians were:

| Far-field response | Candidate perturbation | Background perturbation | Paired two-sided Wilcoxon `p` |
|---|---:|---:|---:|
| P angle difference | `1.00e-9` | `1.65e-9` | 0.00046 |
| A angle difference | `2.11e-5` | `2.15e-5` | 0.655 |
| Tension difference | `8.58e-6` | `8.98e-6` | 0.382 |
| Compression difference | `9.63e-7` | `1.19e-6` | 0.516 |

The corresponding values at 25 and 100 frames were still smaller. The direct
far-field P difference remained near numerical precision throughout. The
candidate/background difference in P difference is statistically resolved but
extremely small in absolute magnitude and does not have matching A, tension,
or compression effects.

## Interpretation

This experiment does not support a candidate-specific far-field influence from
the tested local P rotation. It also does not overturn the field-level audit:
P-to-A coupling measurably changes aggregate tension and vortex population.
The two results delimit the present bridge: its current P dynamics act at the
system level, but have not yet supplied a locally propagating structural role
for a tracked candidate.

## Next Test

Predeclare a P-to-A coupling-strength dose-response sweep against V1 parity.
Measure the same field observables and strict local continuation across fixed
strengths before altering the form of P dynamics or adding any further rule.
