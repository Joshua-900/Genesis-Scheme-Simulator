# (Preprint Sketch) Projection with Missing Scales as a Toy Mechanism for Quantum Probabilities

## Title

**Projection with Missing Scales:** Toy Experiments Showing Law‑Like Effects in 1D/2D Quantum Dynamics

## Authors

Your Name (independent)

## Abstract (draft)

We investigate a toy mechanism in which “dimensional accessibility” is modeled as a projection that hides multiscale components of a quantum state. Using exactly solvable and numerically stable 1D and 2D settings, we (i) establish null baselines where the projection aligns with eigenbases (particle‑in‑a‑box), (ii) demonstrate **structured, reproducible** dependence of observables on an accessibility knob in barrier‑scattering and double‑slit dynamics, and (iii) separate **preparatory spectral filtering** effects from **dynamical** effects by comparing initial‑only vs **continuous** projection. In a 1D rectangular‑barrier line with absorbing boundaries, predicted transmission from analytic plane‑wave formulas **matches** the simulated trend for initial‑only spectral masks, while continuous masking yields **additional suppression**. The same accessibility ordering appears in a 2D double‑slit prototype. These results do not confirm a deterministic substrate but provide **falsifiable signatures** for projection‑type mechanisms that may inform higher‑dimensional or holographic models.

## 1. Motivation

- Hypothesis: Some quantum ‘probabilities’ may reflect **missing or compacted degrees of freedom**; observables depend on an **accessibility** parameter.
- Goal: Build **minimal, falsifiable tests** where accessibility → **prediction** → **simulation** can be compared.

## 2. Projection Maps (Operational Definitions)

- **Wavelet masking (DWT, odd extension)**: keep `keep_levels` finest details; tests localized scale sensitivity.
- **Sine‑basis spectral masking (DST‑I)**: keep lowest `K` Dirichlet modes; eliminates DWT boundary artifacts.
- **Fourier band masks (line geometry)**: keep a band around `k0`; aligns with plane‑wave scattering theory.

## 2.5 Core Model (minimal formalism)

**State & Hamiltonian.** Hilbert space ; ().

**Accessibility knob.** Scalar . Filters act in a chosen basis: Fourier (), DST (keep lowest modes), wavelet (). Hard masks are projectors; soft masks are contractions. Post‑normalize.

**Dynamics.**

- **IPM (stroboscopic):** .
- **CPM (continuous):** or non‑Hermitian with renorm. Limit recovers standard QM.

**Predictions.**

- Initial‑only: logistic/erf‑like step.
- Continuous: from time in inaccessible sector.

**Constraints.** No‑signaling (local generators), energy accounting if , no hidden‑variable claims unless added explicitly.

## 3. Systems & Numerics

- **PIB / finite wells** (sanity/null): Crank–Nicolson (CN), Dirichlet grids.
- **Finite well + barrier**: narrow Gaussian/rectangular barrier; wavepacket dynamics; transmission metrics.
- **Absorbing‑boundary line**: complex absorbing layers; rectangular barrier; compare to analytic .
- **2D double‑slit**: split‑step FFT with absorbing edges and two slits.
- Stability: `dt` sweeps, grid refinements; resonance sweeps in `k0` and barrier height.

## 4. Predictions

- For initial‑only **spectral** masks on the line:
- Expect **monotone** approach to baseline as bandwidth ↑; sharp changes when the band crosses (tunneling threshold/resonances).

## 5. Results (Representative)

- **Null:** PIB with DST projection → no change (projection = eigenbasis).
- **Near‑null:** Finite well + DST → minimal changes.
- **Wavelet + barrier dynamics:** varies **non‑trivially** with `keep_levels`; continuous masking strengthens effect.
- **Absorbing line, tunneling regime:** Initial‑only spectral masks → **predicted vs simulated** curves agree in **shape** and threshold; continuous masking shows **extra suppression** beyond prediction.
- **2D double‑slit:** ordering **baseline > initial‑only > continuous** persists; denser sweep shows systematic dependence on accessibility and cadence.

## 6. Interpretation

- Accessibility acts like a **law‑like control** of outcome statistics (e.g., transmission, screen intensity).
- Continuous masking’s extra effect suggests a **dynamical role** for inaccessibility, not just a prep filter.
- Compatible with—but does not prove—deterministic/holographic/compactified explanations.

## 7. Limitations & Alternatives

- 1D/2D toy models; projection choices are proxies, not literal extra dimensions.
- Quantitative gaps (packet phase/localization) require refined prediction (transfer matrices with phase).
- Finite‑box/absorber details may influence constants; addressed via convergence tests.

## 8. Next Steps

- **Law fitting:** extract an empirical and across parameter grids; report residuals with CIs.
- **2D geometries:** quantum billiards/slits to test geometric sensitivity (in progress).
- **Robustness:** cross‑wavelet families; continuous vs intermittent masking; energy‑resolved diagnostics.
- **Open‑source notebook** with data artifacts for reproducibility (prepared).

## 9. Reproducibility

**Artifacts:**

- `compact_init_vs_band.csv`, `compact_cont_vs_band.csv`, `compact_fitted_laws_params.json`
- `convergence_suite_1d.csv`, `dt_convergence_1d_compact.csv`
- `nconv_init_compact.csv`, `nconv_cont_compact.csv`, `nconv_fit_params_compact.json`
- `doubleslit_2d_minimal.csv`, `doubleslit_2d_denser.csv`

**Notebook:** `DDFH_projection_experiments.ipynb` (Run‑All ready).

## 10. Broader Context (non‑committal)

- Relates to ideas about **information‑theoretic constraints**, **holographic encodings**, and **effective dimensionality** at different scales.
- The toy results highlight where a projection‑style mechanism could leave **empirical signatures** amenable to lab analogs (e.g., photonic waveguides).

## 11. Falsifiers (concise)

- If initial‑only spectral masks fail to match plane‑wave predictions in tunneling across grids/packets, the mechanism is likely mis‑specified.
- If continuous‑masking suppression disappears under convergence (N, dt, runtime) and across geometries, the dynamical interpretation is not supported.
- If a CPTP cannot be constructed without enabling signaling or violating unitarity limits, the model is inconsistent.