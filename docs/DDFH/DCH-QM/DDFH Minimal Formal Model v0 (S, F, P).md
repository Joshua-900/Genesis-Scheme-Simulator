Date: Oct. 31st, 2025

---

Deterministic Dimensional Flow Hypothesis (DDFH) — Minimal Model v0 (S, F, P)

A compact axiomatization of the deterministic substrate (S, F) and the projection/measurement map (P) that reproduces the Born rule and Bell/CHSH correlations without signaling.

---

1. Notation
    

Angles on the circle .

= fractional part in .

CHSH settings ; .

Lebesgue measure .

Projection maps substrate states → spacetime observables.

---

1. State Space and Measure (S, μ)
    

Single system

S_1=\mathbb{T}_\phi\times[0,1)_\alpha.

Bipartite singlet

S_2=(\mathbb{T}_{\phi_A}!\times![0,1)_{\alpha_A})  
\times(\mathbb{T}_{\phi_B}!\times![0,1)_{\alpha_B})  
\times[0,1)_u\times[0,1)_v.

: qubit-like substrate angle.

: integrate-to-threshold residue.

: shared entanglement cell—adjacent on the 2-D substrate.

: product Lebesgue measure, invariant under F.

Measurement independence: settings sampled independently of .

---

1. Substrate Dynamics (F)
    

Between measurements, each phase evolves by a measure-preserving rotation:

F:(\phi,\alpha)\mapsto(\phi+\omega,\alpha)\pmod{2\pi,1}.

is constant between measurements (offset residue).

The shared cell remains fixed until consumed by a joint measurement.

---

1. Projection / Measurement Family (P)
    

Deterministic maps from substrate → outcomes; statistics taken w.r.t. .

3.1 Single Two-Outcome Measurement (Born)

Given basis angle ,

r(\phi,\theta)=\cos^2!\Big(\tfrac{\phi-\theta}{2}\Big).

increments and ; when an accumulator reaches 1 it fires and resets by 1 (tie-rule fixed).  
The offset ensures frequency stationarity.

Theorem (Born frequencies)

\Pr(A=+1)=r(\phi,\theta)=\cos^2!\Big(\tfrac{\phi-\theta}{2}\Big).

---

3.2 Bipartite Singlet (Bell/CHSH)

For settings and shared :

p_{\text{same}}(\Delta)=\frac{1-\cos\Delta}{2},  
\quad  
\mathrm{corr}(u;\Delta)=  
\begin{cases}  
+1,&u<p_{\text{same}}(\Delta),\  
-1,&u\ge p_{\text{same}}(\Delta).  
\end{cases}

A(v)= \begin{cases} +1,&v<\tfrac12,\ -1,&v\ge\tfrac12, \end{cases} \qquad A=A(v),\quad B=\mathrm{corr}(u;\Delta),A(v). 

No-signaling

P(A=+1|x,y)=P(B=+1|x,y)=\tfrac12.

Quantum correlation

E[AB|x,y]=-\cos\Delta.

CHSH / Tsirelson bound

S=|E(a,b)+E(a,b')+E(a',b)-E(a',b')|  
=2\sqrt2,\quad S\le2\sqrt2.

---

1. Composition and Update
    

Sequential single-party: after firing, subtract 1 from the triggered accumulator; the residual keeps long-run frequencies stationary.

Entanglement consumption: a joint measurement consumes ; fresh entanglement requires a new shared cell.

---

1. Hilbert Bridge (Minimal Sketch)
    

Map substrate angle → Bloch-circle qubit:

|\psi(\phi)\rangle  
=\cos\tfrac{\phi}{2}|0\rangle  
+\sin\tfrac{\phi}{2}|1\rangle.

\Pr(\uparrow)  
=\langle\psi|E_\uparrow(\theta)|\psi\rangle  
=\cos^2!\Big(\tfrac{\phi-\theta}{2}\Big).

---

1. DDFH Reading (Geometry)
    

Spatially distant sites may be adjacent on the substrate through the shared cell .  
Projection discards the sign information linking them, preserving correlations while preventing signaling.

---

1. Relativity Axioms (R1–R4)
    

R1 (Poincaré-equivariance of projection)  
For each Lorentz transform there exists on S such that .  
→ Predictions transform covariantly; no preferred frame.

R2 (Atemporal outcome rule)

(A,B)=G(\lambda,x,y),\quad  
\lambda=(\phi_A,\alpha_A,\phi_B,\alpha_B,u,v),

R3 (No-signaling)  
, (verified above).

R4 (Lorentz-invariant correlators)  
Correlation depends only on the invariant relative angle between measurement directions: .

Frame-neutrality lemma.  
Exchanging the time order of spacelike leaves marginals and E unchanged since G is atemporal and E depends only on .

---

1. KS / PBR Posture
    

Kochen–Specker (Contextuality):  
DDFH is contextual by design. For POVM ,

p_i(\phi,\Theta)  
=\langle\psi(\phi)|E_i(\Theta)|\psi(\phi)\rangle,

Pusey–Barrett–Rudolph (PBR):  
Adopt ψ-ontic mapping .  
Distinct pure states → disjoint substrate supports; joint preparations factorize across , satisfying preparation independence and evading ψ-epistemic contradictions.

Assumptions summary

Kept Dropped

Determinism · Measurement independence · Operational no-signaling · Born/POVM statistics · Atemporal rule Strict 3-D locality (replaced by nonlocal adjacency on substrate)

---

1. What’s Met vs Open
    

Met  
Determinism · Born statistics · Bell/CHSH (−cos Δ) · No-signaling · Measurement independence · Relativity axioms stated · Contextual & ψ-ontic stance.

Open  
Full Bloch-sphere () generalization · Arbitrary POVMs and sequences · Lorentz-covariant substrate dynamics · Many-body / QFT extension · Finite-substrate corrections (testable signatures).

---

1. Tags & Links
    

# DDFH #MinimalModel #BornRule #BellTheorem #Determinism #QuantumFoundations #Contextuality #PBR

See also: [[Born Rule Deterministic Proof]] · [[Bell Theorem Ddfh Proof]] · [[Born & Bell on the Bloch Sphere (S²) — Deterministic Thresholding]]

---

This version keeps your math intact, clarifies independence and measure invariance, fixes numbering, and aligns link names with the dashboard. It’s ready to drop straight into your Obsidian vault.