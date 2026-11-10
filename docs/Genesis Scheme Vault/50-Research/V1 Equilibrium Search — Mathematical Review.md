---
Area: Research
datetime_stamp: 2026-10-31T00:00:00-05:00
status: draft
confidence: tentative
tags:
  - genesis-scheme
  - v1
  - equilibrium
  - stability
links:
  - "[[Research Index]]"
  - "[[V1 Stabilization — Independent Mathematical Check]]"
summary: Code-based review of an exact reduced equilibrium residual and full active-state numerical stability assessment for the preserved V1 preset.
canonical: false
---

# V1 Equilibrium Search — Mathematical Review

This methods review uses local implementation as primary source. It performs no search or simulation and changes no engine. The proposed milestone is a bounded search on periodic N = 4, 6, 8 lattices from predefined starts, comparing curvature gain beta = 0.04 with beta = 0. It cannot establish absence of other equilibria, cycles, metastable structures, or large-domain behavior.

## Source-defined model

The rule order and parameters come from [the named preset](../../../genesis_v1_compression_ablation.py): alignment, compression, curvature, then locking. The active state is (theta,tau,ux,uy); compression C is overwritten each step. Relevant sources are [alignment](../../../src/genesis_grid/rules_alignment.py), [compression](../../../src/genesis_grid/rules_compression.py), [curvature](../../../src/genesis_grid/rules_curvature.py), [locking](../../../src/genesis_grid/rules_locking.py), and [step orchestration](../../../src/genesis_grid/core.py).

Use alpha = 0.3, gamma = 0.01, tension decay d_tau = 0.02, displacement decay d_u = 0.05, shell gain eta = 0.08, locking lambda = 0.96, and angular time increment h = 0.05. Specify kappa explicitly per condition. Tension/displacement recurrences do not multiply their increments by h.

## Exact equilibrium reduction

Let a_i = sum over four periodic neighbors of sin(theta_j-theta_i). At a full equilibrium,

$$
\tau_i^*=\frac{\gamma}{d_\tau}|a_i|=0.5|a_i|.
$$

This elimination is exact for fixed points, not a quasi-static approximation for evolving trajectories. For unknowns (theta,u), calculate

$$
v=(1-d_u)u+\kappa\tau^*e_\theta,
\qquad C^*=\exp\!\left[-\frac{\det(I+D_cv)^2}{\sigma_c^2+10^{-8}}\right],
\qquad u^+=v+\eta D_c C^*,
$$

where e_theta = (cos theta,sin theta), and D_c uses the source's centered grid-unit differences. Calculate curvature R from the five-point Laplacian of **u-plus**, including the source epsilon and atan2 convention. Then

$$
T=\alpha a+0.1\tau^*+R,
\qquad \mathcal R(\theta,u)=\left(T,\frac{u^+-u}{d_u}\right).
$$

This square residual has 3N-squared real components. Dividing displacement residual by d_u changes conditioning and tolerance, not its zeros. No phase/triad amplification is active. Because q = 1-lambda C is positive, T = 0 implies an angular fixed point. This search targets zero-raw-torque equilibria; arbitrary modular whole-turn fixed points are excluded by construction. The earlier bounded-preset analysis explains when those aliases are impossible.

## Acceptance and controls

Solver success flags are insufficient. Require infinity norms of raw T, the specified reduced residual, and the full source one-step residual each at most 1e-8; report all component norms separately. Reconstruct tau-star and C-star, clone state, and apply the unchanged source step. Measure angular differences circularly and test tau, both displacement components, and C. Initializing C from the final after-shell displacement would be the wrong timing.

Classify a root as nontrivial only if rms(a) >= 1e-3. With beta = 0,

$$
T=0.3a+0.05|a|=
\begin{cases}0.35a,&a\ge0,\\0.25a,&a<0.\end{cases}
$$

Thus exact roots require a = 0. A purported interesting beta-zero root indicates residual failure or a model mismatch. This control does not prohibit ordinary alignment stationary patterns, transient motion, or cycles.

Check the necessary periodic balance sum R = -0.1 sum tau-star: sum a vanishes by bond antisymmetry. Balance is necessary, not sufficient for a root or its stability. Deduplicate equivalent roots consistently; do not impose a global angle gauge as an exact symmetry because the curvature epsilon slightly breaks rotational invariance.

## Full active-state stability

Differentiate the source map in all 4N-squared active variables (theta,tau,ux,uy), not the reduced root residual. Eliminating tension removes its transient relaxation modes and can misclassify stability. If C is included, its old input is unused and supplies zero eigenvalues. Inactive allocated arrays such as inhibitor and template memories pass through unchanged in this rule tuple and supply trivial unit eigenvalues; exclude those spectators explicitly from an active-state attraction claim.

The absolute-value source is nonsmooth when a = 0. The curvature epsilon/atan2 expression is problematic at zero Laplacian. Only attempt a smooth finite-difference classification when min abs(a) and min norm(Laplacian u-plus) both exceed 1e-4. Also verify that finite-difference probes do not cross those branches. Otherwise report stability unresolved by this method, rather than unstable or stable.

Use two finite-difference step sizes, circularly lifted angular output differences, and a reported uncertainty margin around spectral radius one. Radius below one supports local asymptotic stability of a differentiable map only when numerical uncertainty is safely smaller than the margin. Two agreeing finite-difference spectra are numerical evidence, not a rigorous interval certificate. Near-unit or inconsistent spectra remain unresolved.

Perturbation trajectories provide an independent finite-amplitude check. Clip only initial tension perturbations as needed to remain physical, record clipping, and preserve the source evolution. Clipping changes the sampled directions. Track unperturbed root drift separately from perturbed-minus-unperturbed separation, with both angle-aware and auxiliary-state norms. Finite-duration recovery does not certify every perturbation direction.

## Larger periodic domain check

Tile an accepted pattern onto a 2N-by-2N periodic grid and first revalidate its source residual. Then reassess active-state stability there: the repeated pattern admits additional perturbation wavelengths absent from the small domain. Stability on the original domain cannot exclude those instabilities. Tiling supplies a domain check, not evidence of a newly generated structure or a continuum limit.

Every outcome should remain attached to its parameter, domain, start, residual, and stability qualification. Failure to find a root is not proof of nonexistence; a root is not automatically an attractor; an attractor is not by itself an autonomous object or matter claim.
