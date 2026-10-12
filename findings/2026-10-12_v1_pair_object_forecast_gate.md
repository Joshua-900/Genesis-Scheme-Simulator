# V1 Pairs Show Replicated Relational Forecast Value but Do Not Clear the Object-Level Gate

## Predeclared Gate

The experiment tests whether a tracked vortex-antivortex pair's relational
state predicts strict constituent-ID survival over 200 future frames better
than generic local-field statistics measured at the same midpoint. Both ridge
models receive pair age. The field baseline receives local orientation
coherence, tension mean and spread, and compression mean and spread. The
relational model instead receives pair length, closing speed, line unity, line
compression, and accumulated relational activity.

The gate was set before running:

1. at least 5% pooled held-out Brier-error reduction over the local-field
   baseline; and
2. a lower Brier error in at least 7 of 10 held-out seeds.

## Two Independent 10-Seed Cohorts

| Cohort | Forecast records | Field Brier | Relational Brier | Reduction | Held-out wins | Gate |
|---|---:|---:|---:|---:|---:|---|
| Seeds 1-10 | 5,043 | 0.1165 | 0.1122 | 3.72% | 9 / 10 | Not passed |
| Seeds 11-20 | 5,248 | 0.1210 | 0.1153 | 4.74% | 10 / 10 | Not passed |
| Combined descriptive total | 10,291 | 0.1188 | 0.1138 | 4.25% | 19 / 20 | Not passed |

The replication is important: relational state beats the equal-information
local-field baseline in 19 of 20 held-out seeds. But the specified 5% pooled
improvement was not met in either independent cohort. The threshold is not
relaxed after inspection.

## Claim Boundary

The v1 results now support a **reproducible relational candidate class**:
vortex-antivortex relations are repeatedly detected, have persistent
constituent identity under the tracker, exhibit a local causal structural
dependence, and contain modest out-of-seed predictive information beyond a
generic local field summary.

They do **not** yet support the stronger claim of an autonomous higher-order
object. The current relational description has not cleared the stated
predictive-sufficiency gate, and no coarse-grained state has been shown to
close its own dynamics independently of the underlying field.

## Next Test

Do not tune features or lower the gate. Test a distinct requirement: whether a
coarse pair state supports a short-horizon transition model for position,
length, and survival that transfers across seeds better than an equally sized
local-field transition model. This tests dynamical closure rather than merely
another survival score.
