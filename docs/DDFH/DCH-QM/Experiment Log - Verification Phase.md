# Experiment Log — Verification Phase (Updated Aug 9, 2025)

## Status Summary

- We transitioned from ideation to **math + numerics** and now have: 1D & 2D toy models, fitted laws, and convergence checks.
- Current **Verification Gauge:** **58 / 100**.
- Preprint scaffolding is ready: see [[Preprint Sketch — Overview & Instructions]] and [[(Preprint Sketch) Projection with Missing Scales]].
- Reproducible code: `DDFH_projection_experiments.ipynb` (baseline + fits + continuous masking).

## Verification Progress Gauge (snapshot)

**Criteria (10 pts each):**

1. Reproducible projection map, code & data — **10/10**
2. Prediction→simulation agreement in at least one regime — **8/10**
3. Distinct dynamical residual under continuous masking — **6/10**
4. Numerical convergence (N, dt, runtime) — **6/10**
5. Robustness across bases/parameters — **5/10**
6. Law fit + CIs — **6/10**
7. Second geometry replication — **6/10**
8. Falsifiers attempted — **0/10**
9. Compatibility with QM constraints — **0/10**
10. Path to lab analog — **1/10** **Total:** **58/100**

## Key Artifacts (data & code)

- Notebook: `DDFH_projection_experiments.ipynb`
- Initial-only & fits: `compact_init_vs_band.csv`, `compact_fitted_laws_params.json`
- Continuous masking (1D): `compact_cont_vs_band.csv`, `ultra_compact_continuous_sweep.csv`, `extended_continuous_sweep.csv`
- Convergence: `convergence_suite_1d.csv`, `dt_convergence_1d_compact.csv`, `nconv_init_compact.csv`, `nconv_cont_compact.csv`, `nconv_fit_params_compact.json`
- 2D prototypes: `doubleslit_2d_minimal.csv`, `doubleslit_2d_denser.csv`

## Recent Results (high‑value)

- **Initial‑only law (1D):** logistic step . Fits with **R²≈1.0**, stable across N and dt.
- **Continuous masking (1D):** suppression . Parameters consistent across N; cadence controls strength.
- **2D double‑slit:** ordering **baseline > initial‑only > continuous** holds; denser sweep shows systematic dependence on accessibility and cadence.

## What Changed Since Last Log

- Added **dt‑convergence** and **N‑convergence** with **95% CIs** on fitted parameters.
- Introduced a **2D** geometry and verified qualitative agreement with 1D predictions.
- Wrote a **Core Model** (state, , IPM/CPM dynamics, limits), ready to paste into the preprint sketch.

## Next Actions to Reach 60+

1. Finalize convergence figures (overlay N & dt with CIs).
2. Add a compact **falsifiers** section (e.g., cases where IPM/CPM must reduce to QM and how to break it).
3. Outline **lab analog** (photonic waveguides / quantum walks) and expected scaling.
4. Package repo (README, requirements, saved CSVs, figure scripts) for expert review.

## Cross‑Links

- Preprint overview: [[Preprint Sketch — Overview & Instructions]]
- Working draft: [[(Preprint Sketch) Projection with Missing Scales]]
- Core model: see “Core Model (minimal formalism)” note for paste‑ready text.