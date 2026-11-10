
## Overview

A deterministic outcome rule for **two qubits** that reproduces **all quantum projective statistics** for a given state ρ: correct **local marginals**, **joint correlators**, and **no-signaling**. It generalizes the singlet construction and keeps DDFH’s atemporal, nonlocal substrate stance.

---

## 1) Quantum targets (what we must match)

For a two-qubit state ρ, define the usual Bloch/tensor data:

```latex

r_A \in \mathbb{R}^3,\quad r_B \in \mathbb{R}^3,\quad T \in \mathbb{R}^{3\times 3},
```

```latex

(r_A)_i = \mathrm{Tr}\!\left[\rho\,(\sigma_i\!\otimes\!\mathbb{I})\right],\quad
(r_B)_j = \mathrm{Tr}\!\left[\rho\,(\mathbb{I}\!\otimes\!\sigma_j)\right],\quad
T_{ij} = \mathrm{Tr}\!\left[\rho\,(\sigma_i\!\otimes\!\sigma_j)\right].
```

Given measurement axes $m\in S^2$ (Alice) and $n\in S^2$ (Bob), quantum predictions are:

```latex

\alpha(m)=\mathbb{E}_\rho[A|m]=r_A\!\cdot\! m,\qquad
\beta(n)=\mathbb{E}_\rho[B|n]=r_B\!\cdot\! n,\qquad
C(m,n)=\mathbb{E}_\rho[AB|m,n]= m^{\!\top}T\,n,
```

---

## 2) Substrate variables (per pair)

Let the shared substrate cell carry $\lambda=(v,w)\in[0,1)^2$, distributed by the invariant measure (deterministic but fixed per pair). Settings $(m,n)$ are independent of $\lambda$ (measurement independence).

---

## 3) Deterministic outcome rule (atemporal, nonlocal)

**Step 1 (Alice marginal).** Set:

```latex

p_A(m)=\frac{1+\alpha(m)}{2},\qquad
A = \begin{cases}
+1,& v<p_A(m),\\\\
-1,& v\ge p_A(m).
\end{cases}
```

**Step 2 (Bob conditional).** Let $p=p_A(m)$ and define the conditional expectations for Bob:

```latex

b_{+}(m,n)=\frac{\beta(n)+C(m,n)}{2p}\quad(p>0),\qquad
b_{-}(m,n)=\frac{\beta(n)-C(m,n)}{2(1-p)}\quad(p<1).
```

Then:

```latex

B=\begin{cases}
+1,& \text{if } A=+1 \text{ and } w<\tfrac{1+b_{+}}{2},\\\\
+1,& \text{if } A=-1 \text{ and } w<\tfrac{1+b_{-}}{2},\\\\
-1,& \text{otherwise.}
\end{cases}
```

**Edge cases.**

- If $p=1$ ($\alpha=+1$): $A\equiv+1$ and set $B$ with $\mathbb{E}[B|A=+1]=\beta+C$.
- If $p=0$ ($\alpha=-1$): $A\equiv-1$ and set $B$ with $\mathbb{E}[B|A=-1]=\beta-C$.

(For any physical two-qubit ρ, $(\alpha,\beta,C)$ ensure $b_\pm\in[-1,1]$.)

---

## 4) Guarantees (lemmas)

**Lemma 1 (marginals).**  
$\mathbb{E}[A|m,n]=\alpha(m)$ and $\mathbb{E}[B|m,n]=\beta(n)$ → no-signaling.

**Lemma 2 (correlator).**  
$\mathbb{E}[AB|m,n]=C(m,n)=m^{!\top}T,n$.

**Lemma 3 (determinism, atemporality).**  
For fixed $(\lambda,m,n)$, $(A,B)$ is fixed; no time order or foliation is referenced.

---

## 5) Recovery of known cases

- **Singlet:** $r_A=r_B=0$, $T=-\mathbb{I}$. Then $\alpha=\beta=0$, $C=-m!\cdot! n$, so $p=\tfrac12$, $b_{+}=C$, $b_{-}=-C$. This collapses to the earlier “flip/keep” rule and yields $S=2\sqrt{2}$.
- **Product states:** $T=r_A r_B^{!\top}$ → independent local draws with correct biases.

---

## 6) Sequential measurements (local Lüders behavior)

After Alice measures along $m$ with outcome $A$, set the local substrate direction to the observed eigenvector ($n_A\leftarrow A,m$) and keep fractional residues in the local accumulators. The next axis $m'$ yields Born/Lüders frequencies as in the single-qubit note. (Bob symmetric.)

---

## 7) Notes on validity & scope

- **Deterministic, non-signaling** sampler for all two-qubit projective measurements.
- **Contextual by design** (conditional uses full context $(m,n)$ via $C$).
- **Relativity-friendly**: atemporal rule; predictions depend only on dot-product invariants.

---

## 8) Minimal pseudocode (for simulations)

```python
def two_qubit_outcomes(v, w, m, n, rA, rB, T):
    alpha = rA @ m
    beta  = rB @ n
    C     = m @ (T @ n)
    p = (1 + alpha)/2
    A = +1 if v < p else -1
    if A == +1:
        b = (beta + C)/(2*p) if p > 0 else (beta + C)  # limit case p->1
    else:
        q = 1 - p
        b = (beta - C)/(2*q) if q > 0 else (beta - C)  # limit case p->0
    B = +1 if w < (1 + b)/2 else -1
    return A, B
```

---

## 9) Outlook to 3+ qubits (sketch)

Use a **hierarchical atemporal chain**:

1. Sample $A_1$ from its local marginal (thresholding).
2. Choose $E[A_2|A_1]$ so that both $\mathbb{E}[A_2]$ and $\mathbb{E}[A_1A_2]$ match QM.
3. Choose $E[A_3|A_1,A_2]$ to match all pairwise and triple correlators (GHZ/W tensors).
4. Repeat with shared substrate variables and per-step integrators; at each stage enforce the linear constraints implied by the target QM correlators.

No-signaling is preserved by construction of marginals at each level.

---

## Links

[[Born & Bell on the Bloch Sphere (S²) — Deterministic Thresholding]] · [[Born Rule via Deterministic Thresholding (DDFH Context)]] · [[Bell’s Theorem Reinterpretation (Formal)]]