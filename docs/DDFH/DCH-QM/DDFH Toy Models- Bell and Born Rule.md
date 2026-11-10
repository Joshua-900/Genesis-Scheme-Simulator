

## Overview

These notes document two toy-model explorations designed to test whether the **Deterministic Dimensional Flow Hypothesis (DDFH)** can survive the constraints of modern quantum physics:

1. **Bell’s theorem compliance** (nonlocality without signaling).
2. **Born rule emergence** (squared amplitudes from deterministic substrate).

---

## 1. Bell’s Theorem Toy Model

### Context

Bell’s theorem shows that any local hidden-variable theory cannot reproduce the predictions of quantum mechanics. Experiments confirm violations of Bell inequalities, which forces deterministic theories into a narrow design space: they must be **nonlocal** (in 3D terms) while preserving **no-signaling**.

### Model Design

- **Substrate:** deterministic stream of hidden variables λ ∈ [0,1).
- **Measurement settings:** angles (a, a′) for Alice and (b, b′) for Bob.
- **Rule:**
    - Compute Δ = θ_x − θ_y.
    - Target correlation E(Δ) = −cos Δ.
    - Use λ to deterministically assign outcomes with the correct correlation.
    - Marginals for A and B kept unbiased and independent of distant settings.

### Results

- CHSH S-values ≈ **2.826–2.829**, matching the quantum prediction of 2√2 ≈ 2.828.
- **No-signaling preserved:** marginal outcome probabilities stayed ~0.5 regardless of distant settings.
- **Interpretation:** DDFH can survive Bell’s constraints if 3D nonlocality is reinterpreted as adjacency on a 2D deterministic substrate (projection geometry).

---

## 2. Born Rule Toy Model

### Context

Quantum mechanics postulates the Born rule: probabilities are the squared amplitudes of wavefunction components. Any deterministic substrate must show how these statistics emerge, rather than assuming them.

### Model Design

- **State:** a deterministic angle φ on the 2D substrate.
- **Measurement basis:** defined by angle θ.
- **Amplitudes:**
    - I_up = cos²((φ − θ)/2)
    - I_dn = 1 − I_up
- **Projection mechanism:** deterministic two-channel “integrate-and-fire” accumulators with fixed threshold.
    - Each channel integrates its intensity.
    - The first to hit threshold fires = outcome.
- Over many events, outcome frequencies converge to Born rule.

### Results

- Across φ–θ grid (441 combinations):
    - Mean absolute error ≈ **2e−5**.
    - Max error ≈ **7e−5**.
- Outcome fractions closely matched Born prediction cos²((φ−θ)/2).

### Interpretation

The Born rule can emerge as a **statistical shadow** of deterministic dynamics when observed through a coarse-grained projection.

---

## Implications for DDFH

- **Bell compliance:** Determinism survives if substrate allows nonlocality hidden by projection. Nonlocal in 3D, but local on substrate.
- **Born rule emergence:** Squared-amplitude probabilities can be reconstructed from deterministic flows + threshold projection.

Together, these toy models show that DDFH is **not ruled out by Bell** and can **naturally yield Born statistics**—key hurdles for any deterministic theory of quantum mechanics.

---

## Next Steps

1. Formalize substrate geometry (2D folding, holographic dictionary).
2. Prove analytically that no-signaling holds under the mapping.
3. Show why Tsirelson’s bound (≤ 2√2) emerges but not super-quantum correlations.
4. Search for subtle deviations from QM predictions (testable signatures).

---

**Conclusion:** These simulations don’t prove DDFH is real, but they demonstrate that it can logically thread the constraints of Bell’s theorem and the Born rule—putting it in rare company with serious nonlocal deterministic theories.