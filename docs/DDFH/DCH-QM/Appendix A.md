
---

Appendix A — Λ → Madelung → Schrödinger (Derivation)

> Goal: Derive the Madelung system (continuity + HJ with quantum potential) from the Λ-action and recombine it into the Schrödinger equation; fix the Fisher coefficient .

A1. Λ-Action (stochastic/local flat limit)

We work where Λ fluctuates around a coherent mean so that locally (keep full covariance notes for App. B/C). Use

S[\Lambda,\rho,\theta]=\int d^4x,\sqrt{|\Lambda|},\Big[\tfrac{1}{2\kappa}\mathcal R[\Lambda]  
+\rho,\Lambda^{\mu\nu}\partial_\mu\theta,\partial_\nu\theta-\mathcal V(\rho)  
+\alpha,\frac{\Lambda^{\mu\nu}\partial_\mu\rho,\partial_\nu\rho}{\rho}-\mathcal U(\Lambda)\Big].

A2. Variation w.r.t. → Continuity

\partial_\mu!\big(2\rho,\Lambda^{\mu\nu}\partial_\nu\theta\big)=0  
;\Rightarrow;  
\partial_t\rho+\nabla!\cdot!\Big(\rho,\tfrac{\hbar}{m}\nabla\theta\Big)=0,

A3. Variation w.r.t. → HJ + Quantum Potential

From

\mathcal L_\rho=\rho,\Lambda^{\mu\nu}\partial_\mu\theta,\partial_\nu\theta-\mathcal V(\rho)  
+\alpha,\frac{\Lambda^{\mu\nu}\partial_\mu\rho,\partial_\nu\rho}{\rho},

\partial_t\theta+\frac{(\nabla\theta)^2}{2m}+V-\frac{\hbar^2}{2m},\frac{\nabla^2\sqrt\rho}{\sqrt\rho}=0,

\boxed{;\alpha=\frac{\hbar^2}{8m^2};}

.

(Quick check: . Match coefficients with to fix .)

A4. Recomposition → Schrödinger

With :

i\hbar,\partial_t\psi=\Big(-\frac{\hbar^2}{2m}\nabla^2+V\Big)\psi.

A5. Assumptions & units

Regime: local stochastic Λ (coherent corrections higher order in ).

Units: .

BCs: decay/periodic so surface terms vanish.

A6. Covariant form (note for completeness)

Replacing , gives

\Lambda^{\mu\nu}\partial_\mu\theta,\partial_\nu\theta-\mathcal V'(\rho)-4\alpha,\frac{\Box_{\Lambda}\sqrt\rho}{\sqrt\rho}=0,\quad  
\nabla^{(\Lambda)}_\mu(\rho,\Lambda^{\mu\nu}\partial_\nu\theta)=0,

A7. Consistency checks

Unitarity: ✓ (continuity).

Linearity: ✓ (recomposition).

No-signaling at projected level (local ): ✓

Link to GR limit handled in Appendix B (coherent Λ).

A8. Takeaway

From the Λ-action, QM emerges via the Fisher term with fixed . This anchors the quantum limit of DDFH within the same variational framework that yields GR in the coherent limit.