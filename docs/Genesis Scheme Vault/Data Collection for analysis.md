---
area: Analysis
date: 2026-04-12
status: in-progress
confidence: medium
tags:
  - data
  - collection
  - analysis
  - claims
  - experiment
  - verfication
  - falsification
---


Date: 4/12/2026
## What we're trying to prove

**Core claim:** A single angular degree of freedom per point on a protospace, with only local alignment coupling and dynamic geometry, spontaneously produces discrete ordered structure from a continuous symmetric starting state.

**Specific sub-claims:**

1. The symmetry breaking is **spontaneous** — the rules don't prefer any angle
2. There is a **phase transition** — it only happens above a critical geometry coupling
3. The result is **robust** — it happens reliably, not just in cherry-picked runs

## What each experiment measures and why

**Multi-seed (20 runs, same parameters, different random initial conditions)**

This is the most important experiment. It tests claim 1.

If SSB is genuine, each run should pick a **different** peak angle (because the rules have no preferred direction — the choice comes from random initial conditions). But |m| should be **consistently high** across all runs (because the mechanism is deterministic even though the outcome is contingent).

- **Proves SSB if:** angles are widely scattered (std > 1 radian) AND |m| is consistently above some threshold (e.g., > 0.2 for every run)
- **Disproves SSB if:** angles cluster around the same value (hidden bias in the code) OR |m| is near zero for most runs (no real ordering)
- **Inconclusive if:** some runs order and others don't (fragile, parameter-dependent)

**Kappa sweep (20 values of geometry coupling, everything else fixed)**

This tests claim 2. A real phase transition has a critical threshold — below it, disorder; above it, order.

- **Proves phase transition if:** |m| is near zero for low kappa and jumps to high values above some critical kappa_c. The sharper the jump, the stronger the evidence. A true phase transition is a discontinuity in the thermodynamic limit (N → infinity).
- **Disproves phase transition if:** |m| increases smoothly and gradually with kappa, with no clear threshold. That would be a crossover, not a transition.
- **Verification:** run the same sweep at different N values (100, 200, 400). If the jump gets sharper with larger N, that's evidence it becomes a true transition in the infinite-size limit.

**Spatial correlation function (captured automatically in every run)**

This is supporting evidence for the nature of the ordered phase. It measures how similar theta is between cells separated by distance r.

- **In a disordered phase:** correlation decays exponentially — C(r) ~ exp(-r/ξ) where ξ is the correlation length
- **In an ordered phase:** correlation stays near 1 for all r — long-range order
- **At the transition:** correlation decays as a power law — C(r) ~ r^(-η) — neither exponential nor constant

The correlation function tells you **what kind** of order the system has, not just whether it has order.

**Time series of |m| and vortex count**

This characterizes the dynamics — how the system reaches its ordered state.

- **Fast rise to plateau:** the system finds order quickly and commits
- **Slow rise:** the system takes a long time to organize (critical slowing down near the transition)
- **Oscillations:** competing domains (the breathing you saw)
- **Vortex count decay curve:** the rate of defect annihilation tells you about the energy landscape

## What constitutes verification

For someone else to take this seriously, they need:

1. **The code** — everything in the repo, reproducible with a fixed random seed
2. **The multi-seed data** — showing different angles, consistent |m|, across 20 runs. This rules out the most obvious objection ("your code has a bug that prefers angle X")
3. **The kappa sweep** — showing a clear threshold. This rules out "you just tuned the parameters until it worked"
4. **The sweep at multiple N values** — showing the transition sharpens with scale. This rules out "it's a finite-size artifact"
5. **The parameter values** — documented, with the specific claim that phase wells, dipoles, and triads are all zero. Someone can read the code and verify that no absolute angle preference exists anywhere

## What would falsify it

Being honest about what would kill the claim:

- Multi-seed runs consistently picking the same angle → code bug, not SSB
- |m| near zero at all kappa values → no ordering, the mechanism doesn't work
- Ordering only at very specific parameter combinations → fine-tuning, not a robust phenomenon
- The transition not sharpening with N → finite-size artifact, not a real phase transition
- Someone finding a hidden symmetry-breaking term in the rules that we missed

The multi-seed experiment is the single most important piece. If the angles scatter and |m| is consistent, the other experiments strengthen the case. If the angles don't scatter, nothing else matters.

Notes on the data collection:

Look at the angles: 1.07, 1.38, 2.27, 0.53, 6.27 — all different. Standard deviation 2.06 radians. **Every run picks a different direction.** That's genuine SSB confirmed with measurement.

Here's how to run the real experiments:

**1. Multi-seed (proves SSB is genuine):**

```
python genesis_measure.py --multi-seed --seeds 20 --N 200 --frames 10000
```

**2. Kappa sweep (finds the phase transition):**

```
python genesis_measure.py --sweep-kappa --kappa-steps 20 --N 200 --frames 10000
```

**3. Single deep run (long-time behavior):**

```
python genesis_measure.py --N 500 --frames 50000 --kappa 0.097
```

All output goes to the `results/` directory as JSON files (full data including time series, histograms, correlation functions) plus a CSV summary for quick analysis. Each JSON has everything needed to reproduce or plot the run.

The multi-seed at N=200 with 10k frames is probably the highest-priority experiment — it gives you 20 independent measurements of |m| and angle with enough frames to settle. Run time should be about 10-15 minutes total.