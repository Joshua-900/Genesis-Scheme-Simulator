---
Area: Research
datetime_stamp: 2026-10-31T00:00:00-05:00
status: draft
confidence: tentative
tags:
  - genesis-scheme
  - stabilization
  - mathematical-audit
  - v1
links:
  - "[[Research Index]]"
  - "[[Current Direction]]"
  - "[[Genesis Engine v1 recap]]"
summary: Independent code-based bounds and fixed-point checks for the named three-rule V1 preset, distinguishing response slowing from structural maintenance.
canonical: false
---

# V1 Stabilization — Independent Mathematical Check

This is an analytical check of existing code, not a simulation result, new campaign, or change to V1/V2. It checks the named alignment–compression–curvature pipeline in [genesis_v1_compression_ablation.py](../../../genesis_v1_compression_ablation.py), with its locking postprocessor. Comments describing freezing or bistability are not substituted for equations.

## Scope and assumptions

The preset has alpha = 0.30, gamma = 0.01, curvature gain beta = 0.04, locking lambda = 0.96, shell gain s = 0.08, and dt = 0.05. Inherited defaults give tension decay d = 0.02, geometry decay g = 0.05, and sigma_c squared = 0.0625. Phase/triad terms and their amplification gains are zero. Bounds below assume the standard zero tension/displacement initialization, finite arithmetic, the stated ordered rules, and 0 <= kappa <= 0.1 (the default sweep range). Larger custom kappa values require recomputing the no-wrap bound. See [core.py](../../../src/genesis_grid/core.py).

## Exact update structure

For site i, let

$$
a_i=\sum_{j\sim i}\sin(\theta_j-\theta_i),\qquad |a_i|\le4.
$$

The [alignment rule](../../../src/genesis_grid/rules_alignment.py) supplies alpha a_i and stores abs(a_i), not a sum of absolute bond differences. Cancellation is possible. This quantity is not automatically an energy density.

The [compression rule](../../../src/genesis_grid/rules_compression.py) then computes

$$
\tau_i^+=(1-d)\tau_i+\gamma|a_i|,\qquad
v_i=(1-g)u_i+\kappa\tau_i^+ (\cos\theta_i,\sin\theta_i),
$$

$$
C_i^+=\exp\left[-\frac{\det(I+\nabla_c v_i)^2}{\sigma_c^2+10^{-8}}\right],
\qquad u_i^+=v_i+s\nabla_c C_i^+.
$$

Here the centered differences use grid units. Compression is measured **before** the shell displacement. Curvature subsequently uses **after-shell** u-plus; locking uses the previously measured C-plus. Thus stored compression need not equal compression recomputed from the final displacement. The shell may affect the current curvature torque immediately, while its effect on the next compression measurement occurs in a later update.

With L_i the five-point Laplacian vector of u-plus, the [curvature rule](../../../src/genesis_grid/rules_curvature.py) supplies

$$
b_i=\beta(\|L_i\|+\epsilon)
\sin(\operatorname{atan2}(L_{iy},L_{ix})-\theta_i),\quad\epsilon=10^{-8}.
$$

The complete angular update is

$$
T_i=\alpha a_i+0.1\tau_i^++b_i,\qquad
\theta_i^+=\bigl[\theta_i+dt\,q_iT_i\bigr]_{2\pi},\qquad
q_i=1-\lambda C_i^+.
$$

These expressions follow [locking](../../../src/genesis_grid/rules_locking.py) and [step orchestration](../../../src/genesis_grid/core.py).

## Locking slows nonzero torque; it does not exactly freeze this preset

Because 0 <= C <= 1,

$$
0.04\le q_i\le1.
$$

At a given state, maximum compression leaves four percent of the raw angular increment. Apart from rounding or modular aliasing, a nonzero T therefore causes an update. The factor is a state-dependent mobility or response brake. It does not introduce a restoring direction by itself.

This does not imply that attraction, stability, or lifetime cannot change. Changing mobility changes the discrete dynamics and its coupling to evolving auxiliary state. Equal fixed-point sets do not imply equal basins or stability.

## Bounds exclude modular fixed-point aliases in the stated range

Starting at zero tension,

$$
0\le\tau_i\le\frac{4\gamma}{d}=2.
$$

For either displacement component, abs(centered derivative of C) <= 1/2. If U bounds both component magnitudes, the recurrence gives

$$
U^+\le0.95U+2\kappa+0.04,\qquad
U\le40\kappa+0.8\le4.8.
$$

Consequently each Laplacian component is bounded by 8U, and

$$
|T_i|\le1.2+0.2+0.04(8\sqrt2\,4.8+10^{-8})<3.573,
\qquad dt|q_iT_i|<0.179<2\pi.
$$

This holds with locking disabled as well. An unchanged angular coordinate modulo 2pi therefore requires T_i = 0, not a hidden whole revolution.

For comparisons changing only 0 <= lambda < 1, all auxiliary updates are identical functions of the incoming full state and q is positive. Thus the **full-state fixed-point sets are the same** as at lambda = 0 within these bounds. At lambda = 1, q can vanish and this implication fails. At arbitrary dt, kappa, or unbounded initial state, modular aliases must be reconsidered.

## Retention, renewal, and a small implementation artifact

Unforced tension history decays as 0.98 to the n; its half-life is about 34.3 updates. Sustained tension requires renewed abs(a), not merely large pairwise angular differences. Displacement's homogeneous history decays as 0.95 to the n, with half-life about 13.5 updates. However, **the full geometry need not decay monotonically**: residual tension and the nonlinear shell source can continue forcing it. Proving disappearance requires controlling those sources, not just observing decay constants.

At exactly zero Laplacian, the usual backend atan2(0,0) = 0 convention leaves b_i = -beta epsilon sin(theta_i), not zero. The preset's magnitude is at most 4e-10. This is negligible at ordinary measurement scales but breaks exact rotational symmetry and matters for exact fixed-point statements. No repair is proposed here.

## What a discriminating check would need

One cloned-state step with locking switched off necessarily changes angular response from qT to T, with identical auxiliary updates. The resulting larger increment is built into the rule; it is not independent evidence of a novel maintenance mechanism.

A stronger distinction asks whether compression-associated structure renews the sources that sustain its own future persistence, beyond this immediate brake. That requires time-separated causal accounting and matched interventions on structural feedback, not only lock removal. Decay, topology, ordinary alignment, shell forcing, and the brake must remain distinguishable explanations. This note commissions no experiment and makes no finding of self-maintenance, autonomy, or matter emergence.
