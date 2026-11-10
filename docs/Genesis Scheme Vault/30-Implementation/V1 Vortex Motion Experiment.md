---
Area: Implementation
datetime_stamp: 2026-10-31T00:00:00-05:00
status: complete
confidence: vetted
tags:
  - genesis-scheme
  - v1
  - vortex-motion
  - measurement
links:
  - "[[Implementation Index]]"
  - "[[V1 Vortex Motion Results — 2026-10-31]]"
  - "[[V1 Discrete Update Convention]]"
  - "[[Audit Ledger]]"
summary: Isolated periodic tracking, matched structural interventions, visual encounter replay and fresh-seed forecasts for the preserved V1 structural preset.
canonical: false
---

# V1 Vortex Motion Experiment

## Purpose and preservation

This is new experimental coverage of vortex motion and compact forecasts, inheriting the closed baseline rather than repeating its historical evidence audit. The implementation is entirely in `src/genesis_motion/`. It calls the existing V1 adapter without modifying that adapter, the historical tracker, V1 or V2. The runner verifies the parent audit fingerprints before collection and all 53 preserved engine source hashes after it.

This tests one naturally generated opposite-charge pair per seed in a populated field. “Controlled encounter” means controlled counterfactual branches of the same state; it does not mean an isolated two-body system.

## Components

- [Experiment](../../../src/genesis_motion/experiment.py): frozen protocol, selection, cloned branches, trajectory/forecast records and artifacts.
- [Observations](../../../src/genesis_motion/observations.py): separate conservative periodic tracker, smooth structural reset and local descriptors.
- [Evaluation](../../../src/genesis_motion/evaluation.py): fixed ridge predictors and held-out cohort gates.
- [Rendering](../../../src/genesis_motion/render.py): saved-data plots and animation; does not simulate or fit.
- [Tests](../../../tests/test_vortex_motion.py): periodic matching, ambiguity termination, intervention locality, same-θ branches, feature capacity and cohort isolation.

## Frozen default protocol

Use the preserved three-rule V1 preset at N=64 and `dt=0.05`. All durations are model updates under [[V1 Discrete Update Convention]], not physical seconds.

- Burn in for 800 updates; observe the final 100 burn-in updates to initialize tracking.
- Training seeds 1001–1008; test seeds 2001–2008; replication seeds 3001–3008.
- At the fixed burn-in endpoint, select an opposite-charge pair with both observed ages at least 50 updates and separation 3–16 sites. Maximize current radius-5 midpoint compression, then age. Do not inspect its future.
- Clone into untouched, selected-neighborhood structural reset and distant-background structural reset branches.
- Reset τ, ux, uy and C together with a compact radius-5 cosine taper, while preserving θ exactly. The background uses the periodic antipode and the same taper. Removed state magnitude is not matched.
- Follow for 400 updates, observed every 5. Forecast displacement and strict observed continuation 100 updates ahead.
- The first eligible training seed, chosen without future inspection, supplies the visual replay.

The model continues to use only present state; the structural reset is a counterfactual intervention on that present state. It does not establish that two naturally occurring histories would realize the same compared θ configurations.

## Identity and displacement

The original tracker is preserved. This experiment's tracker uses periodic mutual-nearest matching within each winding charge, maximum match distance 2.5 sites and an ambiguity margin 0.25 sites. It ends identity immediately when no acceptable match exists. There is no missed-frame bridging or identity resurrection.

Displacement accumulates shortest periodic increments along an uninterrupted identity track, avoiding a spurious long jump at an edge. Ambiguity or a missed observation can end a track; this does not automatically establish physical annihilation.

## Forecast inputs and fair controls

Every model receives current object age, charge, past observed velocity and the selected partner's relative position/distance/observation flag. No model receives absolute position, branch label, elapsed frame or future values.

The structural predictor adds eight local θ descriptors and eight structural descriptors. The matched field predictor adds sixteen θ descriptors instead. Both have 24 scalar features, the same radius-5 neighborhood and ridge penalty 10. Kinematic-only and smaller local-field references are also reported.

The shuffled-structure comparator has the same inputs and feature count as the structural predictor, but permutes only the structural descriptors within each seed and branch. Training and evaluation cohorts are shuffled separately; no data crosses seed splits. Zero-displacement persistence and the training-mean forecast are additional references.

Motion is evaluated only where the same identity is observed at both anchor and forecast horizon. The continuation forecast uses all observed anchors. They are separate targets; motion results do not establish behavior of disappeared identities. Repeated frames, both charges and all intervention branches remain clustered by independent seed for uncertainty.

## Gates declared before the main run

The motion predictor must beat matched field, shuffled structure and zero-motion persistence in **each** unseen cohort with:

1. At least 5% mean-loss reduction.
2. A positive paired-seed 95% bootstrap lower limit, using 2,000 draws.
3. Wins in at least ceil(0.7 × cohort size), or 6/8 seeds here.

Each seed needs at least five eligible motion records and each cohort at least 10% nonzero (>0.1 site) motion records. Strict-continuation Brier error uses analogous comparisons as a secondary gate, requiring both outcome classes.

An independent descriptive counterfactual endpoint measures pair position divergence from untouched at update +100, comparing selected and background resets only where both identities are observed in all arms. Its coverage and paired-seed interval are reported. It does not silently score missing identities as zero movement or generalize conditional motion to all objects.

## Reproduction

From the repository root:

```powershell
$env:GENESIS_USE_CUPY = 'False'
$env:OPENBLAS_NUM_THREADS = '1'
& .\.venv\Scripts\python.exe -B -m unittest discover -s tests -v
& .\.venv\Scripts\python.exe -B -m src.genesis_motion.experiment --output results/vortex_motion_new
$env:MPLCONFIGDIR = Join-Path (Get-Location) 'work/matplotlib'
& .\.venv\Scripts\python.exe -B -m src.genesis_motion.render results/vortex_motion_new
```

Existing experiment directories are refused. The renderer can use `--no-movie` to regenerate tables and stills while retaining an existing animation.

## Artifacts and results

[The first run](../../../results/vortex_motion_2026-10-31/summary.md) includes its precollection protocol, source hashes, all initial states, identity trajectories, 8,102 forecast records, exact held-out predictions and an animated encounter. The representative seed archive also retains θ/C frames. Model-training sources remained frozen; a presentation-only renderer revision to show all comparators is fingerprinted separately in `presentation.json` without altering the original protocol, data, fits or metrics.

All 28 tests pass, including the original V1/V2-related regression coverage. The motion and continuation gates were not passed. See [[V1 Vortex Motion Results — 2026-10-31]].
