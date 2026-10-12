---
Area: Experiments
datetime_stamp: 2026-10-11T00:00:00-05:00
status: exploratory
confidence: preliminary
tags:
  - v2
  - zeta
  - refractory
  - benchmark
  - coarsening
links:
  - "[[Current Direction]]"
  - "[[V2 Epsilon Renewal Probe]]"
summary: Activator-refractory benchmark testing whether delayed local suppression produces sustained bounded v2 domains.
canonical: false
---

# V2 Zeta Refractory Benchmark

## Question

Does a delayed, diffusing refractory state that directly suppresses local
actual alignment generate genuine renewal and a bounded domain scale?

## Result

At intermediate times, stronger refractory pressure produces more domains and
smaller largest components than earlier v2 variants. The strongest viable
condition still coarsens: from 36 domains and a 7% largest component at frame
2,000 to one 96% component at frame 8,000.

The refractory mean rises toward a steady plateau rather than cycling. Zeta is
therefore another delayed-coarsening result, not a finite-scale or renewal
result.

## Decision

Do not add further v2 state terms until a dynamical-architecture audit has
explained the shared monotonic relaxation across gamma, delta, epsilon, and
zeta. The next comparison should be a deliberately separate, established
activator--recovery benchmark with explicit excitation, inhibition, and
cycle observables. Its purpose is calibration: whether the measurement stack
can recognize finite-scale renewal when it is genuinely present.

## Evidence

- `findings/2026-10-11_v2_zeta_refractory_benchmark.md`
- `results/v2_zeta_regime_production003.json`
- `results/v2_zeta_regime_production008.json`
- `results/v2_zeta_regime_production020.json`
- `results/v2_zeta_stationarity_seed1.json`
