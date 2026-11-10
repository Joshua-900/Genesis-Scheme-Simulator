# Multiscale organization audit

Classical multiscale representation and held-out perturbation-response prediction only; no spatial bulk, quantum entanglement, physical energy, matter, or holographic duality is established.

Primary gate: **not passed**. V1/V2 engine source hashes unchanged: **True**.

## V1 primary comparison

Positive reduction favors multiscale. Intervals are paired bootstraps of seed losses, not individual records.

| Grid | Held-out cohort | Loss reduction vs planar | 95% interval | Seed wins | Combined cohort gate |
| --- | --- | ---: | --- | ---: | --- |
| 32×32 | test | +3.00% | [-3.60%, +7.21%] | 3/6 | Not passed |
| 32×32 | replication | +0.39% | [-2.44%, +1.88%] | 3/6 | Not passed |
| 64×64 | test | -2.74% | [-7.82%, +1.76%] | 2/6 | Not passed |
| 64×64 | replication | -8.55% | [-14.99%, -3.20%] | 0/6 | Not passed |

## Pipeline comparisons

These comparisons are secondary. Losses are standardized within each dataset; raw normalized losses should not be compared across pipelines.

| Dataset | Track | Test gain vs planar | Replication gain vs planar | Track gate |
| --- | --- | ---: | ---: | --- |
| N32/v1 | theta_only | +3.02% | +2.30% | Not passed |
| N32/v1 | full_state_summaries | +3.00% | +0.39% | Not passed |
| N32/alignment_only | theta_only | -0.21% | -6.03% | Not passed |
| N32/alignment_only | full_state_summaries | -0.21% | -6.03% | Not passed |
| N32/geometry_ablation | theta_only | +0.76% | +0.57% | Not passed |
| N32/geometry_ablation | full_state_summaries | +0.66% | -1.03% | Not passed |
| N64/v1 | theta_only | -0.15% | -2.51% | Not passed |
| N64/v1 | full_state_summaries | -2.74% | -8.55% | Not passed |
| N64/alignment_only | theta_only | +2.42% | -1.81% | Not passed |
| N64/alignment_only | full_state_summaries | +2.42% | -1.81% | Not passed |
| N64/geometry_ablation | theta_only | +1.19% | +1.50% | Not passed |
| N64/geometry_ablation | full_state_summaries | -0.35% | +0.46% | Not passed |

## Interpretation

This is a test of fixed classical summary representations and a fixed ridge predictor. A failure is a limit of this protocol, not a refutation of all multiscale organization or Genesis formulations. Coherence differences from shuffled fields are expected from local alignment and do not establish holography. Even a predictive gain would not establish spatial depth.

## Artifacts

- [Protocol and source hashes](protocol.json)
- [Complete metrics](report.json)
- [Figure](summary.png)
- Each `N<size>/<pipeline>/seed_<seed>.npz` contains input snapshots, feature arrays, event identifiers, and response targets.
- Each `N<size>/<pipeline>/forecasts.npz` retains exact held-out predictions and event arrays.
- Each `organization_records.json` retains descriptive block measurements and Fourier surrogate mismatch.

## Limits recorded before collection

- Exploratory small cohorts and fixed linear ridge model; no optimized model selection.
- Independent angles and spatial permutation are observational controls, not simulated trajectories.
- Fourier phase surrogate is NOT pair-correlation matched after projection to unit angles; spectral mismatch is reported.
- Shuffled context permutes context within seed across times and centers while preserving local inputs.
- No mutual-information estimator is fitted; coherence and winding are descriptive statistics, not entropy or entanglement.
- Nested versus shell summaries are alternative representations of the same input footprint; gains can reflect feature geometry or ridge bias, not new dimensions.
- Gaussian pulse has small nonzero tails at every site; response radius is not a finite-speed or causality measurement.
- No bulk reconstruction, emergent locality, energy conservation or matter claim is tested.
