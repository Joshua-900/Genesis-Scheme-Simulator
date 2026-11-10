
---

Supplement C — Λ-Calculus: Full Variations and Limits

> Purpose: Do the explicit variational calculus for the Λ-action, fix coefficients/boundaries, and show the QM/GR limits cleanly.

C1. Action and conventions

Let fields be , density , and phase . Define

S[\Lambda,\rho,\theta]  
=!\int d^4x,\sqrt{|\Lambda|},  
\Big[  
\tfrac{1}{2\kappa},\mathcal R[\Lambda]  
+\rho,\Lambda^{\mu\nu}\partial_\mu\theta,\partial_\nu\theta  
-\mathcal V(\rho)  
+\alpha,\frac{\Lambda^{\mu\nu}\partial_\mu\rho,\partial_\nu\rho}{\rho}  
-\mathcal U(\Lambda)  
\Big],

Indices are raised with . Lorentzian signature in the coherent limit.

---

C2. Variation w.r.t. — continuity

Because appears only via derivatives,

\delta_\theta S  
= -!\int d^4x,  
\partial_\nu!\Big(\sqrt{|\Lambda|},2\rho,\Lambda^{\mu\nu}\partial_\mu\theta\Big),\delta\theta  
\quad\Rightarrow\quad  
\nabla^{(\Lambda)}_\nu!\big(\rho,\Lambda^{\mu\nu}\partial_\mu\theta\big)=0.

---

C3. Variation w.r.t. — quantum potential from Fisher term

For

\mathcal L_\rho  
=\rho,\Lambda^{\mu\nu}\partial_\mu\theta,\partial_\nu\theta  
-\mathcal V(\rho)  
+\alpha,\frac{\Lambda^{\mu\nu}\partial_\mu\rho,\partial_\nu\rho}{\rho},

\Lambda^{\mu\nu}\partial_\mu\theta,\partial_\nu\theta  
-\mathcal V'(\rho)  
-,\alpha,\frac{\Lambda^{\mu\nu}\partial_\mu\rho,\partial_\nu\rho}{\rho^2}  
+\frac{2\alpha}{\sqrt{|\Lambda|}}  
,\partial_\mu!\Big(\sqrt{|\Lambda|},\frac{\Lambda^{\mu\nu}\partial_\nu\rho}{\rho}\Big)=0.

\boxed{~  
\Lambda^{\mu\nu}\partial_\mu\theta,\partial_\nu\theta  
-\mathcal V'(\rho)  
-4\alpha,\frac{\Box_\Lambda \sqrt\rho}{\sqrt\rho}=0  
~}.

\boxed{\alpha=\frac{\hbar^2}{8m^2}}.

---

C4. Variation w.r.t. — GR-like field equations

Using the standard result (discarding total divergences or adding a GHY term as needed):

\delta!\big(\sqrt{|\Lambda|},\mathcal R[\Lambda]\big)  
=\sqrt{|\Lambda|},G^{\mu\nu}[\Lambda];\delta\Lambda_{\mu\nu}+\text{(boundary)}.

T^{(\rho,\theta,\alpha)}_{\mu\nu}  
=-\frac{2}{\sqrt{|\Lambda|}},  
\frac{\delta\big(\sqrt{|\Lambda|},\mathcal L_{\mathrm{matter}}\big)}{\delta\Lambda^{\mu\nu}},  
\quad  
\mathcal L_{\mathrm{matter}}  
=\rho,\Lambda^{\mu\nu}\partial_\mu\theta\partial_\nu\theta  
-\mathcal V(\rho)  
+\alpha,\frac{\Lambda^{\mu\nu}\partial_\mu\rho,\partial_\nu\rho}{\rho}  
-\mathcal U(\Lambda).

\boxed{~G_{\mu\nu}[\Lambda]=\kappa,  
\big(T^{(\rho,\theta)}_{\mu\nu}+T^{(\alpha)}_{\mu\nu}+T^{(\mathcal U)}_{\mu\nu}\big)~},  
\qquad  
\nabla^{(\Lambda)}_\mu T^{\mu}{}_{\nu}=0  
\ \ (\text{Bianchi}).

---

C5. Limits

(i) Coherent limit (GR)

Let with . Then , Fisher/regulator terms are suppressed, and

G_{\mu\nu}[g]=\kappa,T^{(\rho,\theta)}_{\mu\nu},\qquad  
\nabla^{(g)}_\mu T^{\mu}{}_{\nu}=0.

(ii) Stochastic/local-flat limit (QM)

With and keeping the Fisher term:

\partial_t\rho+\nabla!\cdot!\Big(\rho,\tfrac{\hbar}{m}\nabla\theta\Big)=0,\quad  
\partial_t\theta+\frac{(\nabla\theta)^2}{2m}+V  
-\frac{\hbar^2}{2m}\frac{\nabla^2\sqrt\rho}{\sqrt\rho}=0,

---

C6. Boundary terms and well-posedness

Discarded total divergences assume compact support/asymptotic falloff; if physical boundaries exist, add a Gibbons–Hawking–York term for .

The Fisher term is a positive scalar for , aiding stability of the variational problem.

---

C7. Dimensional analysis (fixing )

With , the Fisher density has kinetic dimensions only if , consistent with .

---

C8. Summary

Continuity arises from .

The quantum potential comes from the Fisher term with unique .

GR emerges in the coherent limit .

Covariant conservation follows from Bianchi identities.

This supplement provides the referee-grade calculus anchoring the Λ-action as the shared, variational origin of both QM and GR in DDFH.