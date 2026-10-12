# V1 Geometry/Compression Does Not Yet Explain Pair-Candidate Persistence

## Headline

In a five-seed, 2,000-frame V1 geometry ablation, changing the geometry
coupling `kappa` changed compression strongly at `0.1` but did not materially
change tracked vortex-pair persistence or median pair age. Current evidence
does not support treating the V1 compression path as the cause of candidate
persistence.

## Design

The run held alignment, tension gain, curvature, locking, shell feedback,
seeds, grid size (`N=64`), and the census-compatible three-rule pipeline fixed.
Only `kappa`, the tension-to-geometry coupling, varied. Candidates were tracked
every 25 frames; persistent status required pair age of at least 100 frames.

## Median Final Measurements

| `kappa` | Mean compression | Persistent pairs | Median pair age | Pair-line compression |
|---:|---:|---:|---:|---:|
| 0.000 | 0.00000011 | 118 | 25 | 0.00000003 |
| 0.025 | 0.00000011 | 120 | 25 | 0.00000029 |
| 0.050 | 0.00000012 | 122 | 25 | 0.00002235 |
| 0.100 | 0.06600671 | 123 | 25 | 0.01523435 |

## Interpretation

The ablation worked: `kappa=0` removed the deformation-derived compression,
and `kappa=0.1` produced a large compression increase. Yet the persistence
metric shifted only from 118 to 123 candidates and the median pair age stayed
25 frames. This small count difference is not evidence that compression
stabilizes candidates.

This does not prove compression is dynamically irrelevant. It limits the
specific claim tested here: under these settings and this population metric,
compression is not enough to explain persistence. A later test may perturb the
core of matched individual candidates in a regime where compression is high,
but that requires a predeclared intervention and comparison control.

## Consequence for V2

Do not import V1 geometry/compression into V2 as a validated object mechanism.
It remains a structural state worth studying, but its causal role is unproven.
