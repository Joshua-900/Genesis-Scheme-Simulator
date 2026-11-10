# V1 Equilibrium Search: No Qualifying Witness; Shell Balance Is the Narrower Mechanism

Date: 2026-10-31. Parent audit: `v1_baseline_audit_2026-10-31`. All V1/V2 source and prior evidence fingerprints remain unchanged.

## Numerical result

A frozen search ran 54 attempts: nine starting families on each periodic grid N=4,6,8, with full curvature and curvature-off pipelines. Twenty attempts met the numerical root criteria, all at or near the ordinary alignment-stationary class. No accepted outcome had RMS net alignment torque >=1e-3. These are not twenty distinct equilibrium types.

Acceptance required raw torque and independent source one-update residuals <=1e-8. Solver “success” alone was insufficient, and many nominal successes were rejected. Some cases stopped in local residual minima or at the fixed budget; the result does not prove nonexistence of other equilibria.

The scheduled uniform/checkerboard stability checks were recorded, but their nonsmooth or neutral directions prevented the protocol's ordinary linear stability certification. No interesting accepted root existed, so witness locking-off and larger-grid checks were not triggered. The full stable-witness gate was not passed.

## Analytical result

For an exact full equilibrium, displacement obeys

\[
u_i=(\kappa/d_u)\tau_i e_i+(\eta/d_u)DC_i.
\]

The orientation-driven part of curvature can be combined with alignment into positive neighbor weights

\[
w_i=\alpha+\beta(\kappa/d_u)\tau_i.
\]

Let S be the curvature torque from the shell displacement and delta the implemented epsilon torque, |delta|<=beta*epsilon. Multiplying the raw equilibrium equations by w_i and summing cancels all neighbor torques, yielding

\[
b\sum_iw_i\tau_i+\sum_iw_iS_i+\sum_iw_i\delta_i=0.
\]

With shell feedback disabled, exact equilibrium therefore requires weighted mean tension <=beta*epsilon/b=4e-9. Ignoring epsilon would force it to zero. Substantial maintained stationary tension requires a negative weighted shell-curvature contribution. This identifies the actual candidate balancing mechanism more narrowly than “curvature creates stability.”

The proof was independently checked by another assistant against source equations; this is not external peer review. Nine constructed-field checks verify algebraic identities without asserting those fields are self-consistent roots. No post-search parameter tuning or shell-off solve was performed. Exact bounds require residual allowances for approximate numerical roots.

## Meaning and limits

This study did not establish the target stable nonzero-torque object. It did establish a conditional torque-budget constraint specific to the current model. A future mathematical study could target the nonlinear shell/compression branch directly, under a new protocol. Geometry-only or dynamically maintained structures remain separate possibilities and cannot be counted retrospectively as successes under this search's witness gate.

All 36 tests pass; 53 preserved engine sources match the inherited baseline. The analysis package is isolated. No old experiment or closed audit was rerun as a replacement.

- [Vault report, full derivation and commands](../docs/Genesis%20Scheme%20Vault/40-Experiments/V1%20Equilibria%20%E2%80%94%20Search%20and%20Shell%20Balance.md)
- [Frozen protocol](../results/v1_equilibria_2026-10-31/protocol.json)
- [All numerical attempts and stability traces](../results/v1_equilibria_2026-10-31/report.json)
- [Summary figure and attempt log](../results/v1_equilibria_2026-10-31/summary.md)
- [Separate shell-balance algebra checks](../results/v1_equilibria_2026-10-31/shell_balance_checks.json)
