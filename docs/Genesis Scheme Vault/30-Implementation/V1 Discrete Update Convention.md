---
Area: Implementation
datetime_stamp: 2026-10-31T00:00:00-05:00
status: complete
confidence: vetted
tags:
  - genesis-scheme
  - v1
  - discrete-dynamics
  - time-convention
links:
  - "[[Implementation Index]]"
  - "[[Audit Ledger]]"
  - "[[V1 Baseline Audit — 2026-10-31]]"
  - "[[Cumulative Audit Protocol]]"
summary: Defines the audited V1 structural preset as a discrete-update model with per-step structural coefficients and an angular update multiplier named dt.
canonical: true
---

# V1 Discrete Update Convention

## Decision and scope

**For the audited three-rule structural preset in `src/genesis_grid/`, one iteration is one model update. Structural coefficients are defined per update. The variable `dt` multiplies the final angular update; it is not established as a common physical-time interval for all processes.**

This is the current implementation convention, authorized in the 2026-10-31 discussion. It describes existing behavior without changing equations, defaults, APIs, engine source, historical outputs, or canonical metaphysical theory. Its authority is limited to the named implementation and preset, not all optional pipelines, legacy engines or V2 dynamics.

The closed [[V1 Baseline Audit — 2026-10-31]] already established the mixed update behavior. This note resolves how to describe that behavior. It does not claim a new numerical-convergence result.

## Plain-language interpretation

The model advances through numbered updates. During each update it accumulates or decays structural state and then changes orientations. `dt` controls the angular response within that update. It is retained under its existing name for compatibility.

An iteration count, observation frame and sampling interval are therefore counts of updates. For example, “1,000 burn-in frames, sampled every 25 frames” means 1,000 calls to the update function, observed at 25-call intervals. These are not calibrated seconds.

## Mathematical contract

Write the full discrete state as

\[
X_n=(\theta,\tau,u_x,u_y,C,\ldots)_n,\qquad
X_{n+1}=F(X_n;\mathbf p,h_\theta),
\]

where \(n\) is update count, \(\mathbf p\) contains the fixed per-update coefficients, and \(h_\theta\) is the existing code variable `dt`. Introducing the notation \(h_\theta\) does not rename the API.

For this preset, the tension recurrence is

\[
\tau_i^{n+1}=(1-d_\tau)\tau_i^n+\gamma|a_i^n|,
\qquad a_i^n=\sum_{j\sim i}\sin(\theta_j^n-\theta_i^n).
\]

The tension decay fraction \(d_\tau\), source coefficient \(\gamma\), displacement decay, displacement response and shell response are per-update coefficients as implemented. The final orientation update is

\[
\theta_i^{n+1}=
\left[\theta_i^n+h_\theta\,\mathcal T_i\right]\bmod 2\pi.
\]

Here \(\mathcal T\) is the summed rule contribution after the configured locking postprocess. It can depend on structural variables already modified during the same update. This is a sequential map, not a simultaneous evaluation of every right-hand side on \(X_n\).

### Order is part of the preset

1. Alignment computes angular contributions and the source for tension from the current θ.
2. The compression rule updates tension and displacement, computes C, and applies any enabled shell displacement. C is computed before that optional shell displacement; no additional recomputation is implied by this documentation.
3. Curvature feedback reads the resulting displacement and contributes to angular turning.
4. Locking modifies the total angular contribution using the configured compression state.
5. The core multiplies that contribution by `dt` and updates θ.

Changing the rule order, adding rules, applying structural coefficients more than once, or recomputing C at a different point can define a different map. It is not merely a reporting change.

Source references: [core step](../../../src/genesis_grid/core.py), [alignment](../../../src/genesis_grid/rules_alignment.py), [structural update](../../../src/genesis_grid/rules_compression.py), [curvature feedback](../../../src/genesis_grid/rules_curvature.py), [locking](../../../src/genesis_grid/rules_locking.py), and [named preset](../../../genesis_v1_compression_ablation.py).

## What changing dt means

Halving `dt` at fixed structural coefficients changes angular response relative to structural response. It is a parameter change to this discrete model.

Doubling the iteration count does not undo that change. For example, with no new tension source, one update retains \(1-d_\tau\) of the tension, whereas two retain \((1-d_\tau)^2\). For \(d_\tau=0.02\), these factors are 0.98 and 0.9604.

Consequently:

- Parameter sensitivity to `dt` can be studied, but must be labeled parameter sensitivity.
- Comparing runs at equal \(n\times\texttt{dt}\) does not by itself compare the same dynamics at equal physical time.
- A plot may show \(n\times\texttt{dt}\) as a clearly defined reporting coordinate, but that convention does not calibrate physical elapsed time or supply common rate scaling.
- Numerical precision, grid-size sensitivity and algorithmic stability are separate questions; this definition does not settle them.

## Reporting requirements

For future claims about this preset, retain:

- Engine/source fingerprint, exact rule list and order, and postprocess.
- Initial-state/RNG convention, grid and boundary conditions.
- All enabled parameters, including `dt`, structural coefficients and optional shell feedback.
- Burn-in, follow-up and observation intervals in updates.
- Whether a comparison varies angular response, structural coefficients, update order, precision, grid, or a newly derived continuous-time convention.

Existing findings remain findings about their recorded presets. This note does not retroactively establish physical units or strengthen any object or fundamental-physics claim.

## A future continuous-time variant

Such a variant would require its own equations, rate-to-step mapping, treatment of derived algebraic quantities such as C, and update-order analysis. Only then could timestep refinement at fixed intended dynamics support a physical-time convergence claim.

It must be implemented separately and compared with preserved V1/V2. Multiplying every line by `dt` is not a justified conversion: state variables, sources, constraints and derived diagnostics have different roles.

## Implications for proto-time

The current sequence supplies an ordering of updates. This neither establishes that nature advances in fundamental discrete ticks nor demonstrates that time emerges. Either interpretation would require an additional theoretical and empirical argument.

## Audit inheritance

This is a documentation-only clarification of the closed baseline. The source/evidence fingerprints and its calculations remain unchanged. [[Audit Ledger]] records this as a child clarification; no baseline experiment is repeated. Physical-time convergence remains an open scope, now with the starting convention explicitly defined.
