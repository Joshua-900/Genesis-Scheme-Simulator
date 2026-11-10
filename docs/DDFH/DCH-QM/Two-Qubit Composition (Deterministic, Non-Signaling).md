#   
Two-Qubit Composition (Deterministic, Non-Signaling) — DDFH

## Overview

A deterministic outcome rule for **two qubits** that reproduces **all quantum projective statistics** for a given state $\rho$: correct **local marginals**, **joint correlators**, and **no-signaling**. It generalizes the singlet construction and keeps DDFH’s atemporal, nonlocal substrate stance.

---

## 1) Quantum targets (what we must match)

For a two-qubit state $\rho$, define

```latex

r_A \in \mathbb{R}^3,\quad r_B \in \mathbb{R}^3,\quad T \in \mathbb{R}^{3\times 3},
```

```latex

(r_A)_i=\mathrm{Tr}\!\big[\rho\,(\sigma_i\!\otimes\!\mathbb{I})\big],\quad
(r_B)_j=\mathrm{Tr}\!\big[\rho\,(\mathbb{I}\!\otimes\!\sigma_j)\big],\quad
T_{ij}=\mathrm{Tr}\!\big[\rho\,(\sigma_i\!\otimes\!\sigma_j)\big].
```

Given axes $m\in S^2$ (Alice) and $n\in S^2$ (Bob):

```latex

\alpha(m)=\mathbb{E}_\rho[A\mid m]=r_A\!\cdot\! m,\qquad
\beta(n)=\mathbb{E}_\rho[B\mid n]=r_B\!\cdot\! n,\qquad
C(m,n)=\mathbb{E}_\rho[AB\mid m,n]=m^{\!\top}T\,n,
```

---

## 2) Substrate variables (per pair)

Shared substrate cell carries $\lambda=(v,w)\in[0,1)^2$ (fixed per pair, settings-independent). Settings $(m,n)$ are independent of $\lambda$ (measurement independence).

---

## 3) Deterministic outcome rule (atemporal, nonlocal)

**Step 1 (Alice marginal).**

```latex

p_A(m)=\frac{1+\alpha(m)}{2},\qquad
A=\begin{cases}
+1,& v<p_A(m),\\
-1,& v\ge p_A(m).
\end{cases}
```

**Step 2 (Bob conditional).** Let $p=p_A(m)$ and define

```latex

b_{+}(m,n)=\frac{\beta(n)+C(m,n)}{2p}\quad(p>0),\qquad
b_{-}(m,n)=\frac{\beta(n)-C(m,n)}{2(1-p)}\quad(p<1).
```

```latex

B=\begin{cases}
+1,& A=+1\text{ and }w<\tfrac{1+b_{+}}{2},\\
+1,& A=-1\text{ and }w<\tfrac{1+b_{-}}{2},\\
-1,& \text{otherwise.}
\end{cases}
```

**Edge cases.** If $p=1$ ($\alpha=+1$) set $\mathbb{E}[B\mid A=+1]=\beta+C$. If $p=0$ ($\alpha=-1$) set $\mathbb{E}[B\mid A=-1]=\beta-C$. (Physical $\rho$ ensures $b_\pm\in[-1,1]$.)

---

## 4) Guarantees (lemmas)

**Marginals.**

```latex

\mathbb{E}[A\mid m,n]=\alpha(m),\qquad
\mathbb{E}[B\mid m,n]=\beta(n)\quad\Rightarrow\quad\text{no-signaling.}
```

**Correlator.**

```latex

\mathbb{E}[AB\mid m,n]=C(m,n)=m^{\!\top}T\,n.
```

**Determinism, atemporality.** For fixed $(\lambda,m,n)$, $(A,B)$ is fixed; no time order/foliation is referenced.

---

## 5) Recovery of known cases

- **Singlet:** $r_A=r_B=0$, $T=-\mathbb{I}$. Then $\alpha=\beta=0$, $C=-m!\cdot! n$, $p=\tfrac12$, $b_{+}=C$, $b_{-}=-C$; standard CHSH reaches $2\sqrt{2}$.
- **Product states:** $T=r_A r_B^{!\top}$; outcomes factorize with correct local biases.

---

## 6) Sequential measurements (local Lüders behavior)

After Alice measures along $m$ with outcome $A$, update local substrate direction $n_A\leftarrow A,m$ and keep accumulator residues. Next axis $m'$ yields Born/Lüders frequencies as in the single-qubit model. (Bob symmetric.)

---

## 7) Notes on validity & scope

- **Deterministic, non-signaling** sampler for all two-qubit projective measurements.
- **Contextual by design** (conditional uses full context $(m,n)$ via $C$).
- **Relativity-friendly**: atemporal rule; predictions depend only on dot-product invariants.

---

## 8) Simulation recipe (plain text, no code)

1. Draw $(v,w)\sim\text{Unif}[0,1)^2$.
2. Compute $\alpha=r_A!\cdot! m$, $\beta=r_B!\cdot! n$, $C=m^{!\top}Tn$, and $p=(1+\alpha)/2$.
3. Set $A=+1$ if $v<p$, else $-1$.
4. If $A=+1$: set $b=(\beta+C)/(2p)$ (or its $p\to1$ limit).
5. If $A=-1$: set $b=(\beta-C)/(2(1-p))$ (or its $p\to0$ limit).
6. Set $B=+1$ if $w<(1+b)/2$, else $-1$.
7. Repeat for trials; estimate means to compare with QM.

---

## 9) Outlook to $3+$ qubits (sketch)

Use a hierarchical atemporal chain: sample $A_1$ from its marginal; choose $\mathbb{E}[A_2\mid A_1]$ to match target $\mathbb{E}[A_2]$ and $\mathbb{E}[A_1A_2]$; then $\mathbb{E}[A_3\mid A_1,A_2]$ to match all pair/triple correlators (GHZ/W tensors); continue likewise. No-signaling is preserved by construction of marginals at each stage.

---

## Links

[[Born & Bell on the Bloch Sphere (S2) - Deterministic Thresholding]] · [[Born Rule via Deterministic Thresholding (DDFH Context)]] · [[Bell's Theorum Reinterpretation (Formal)]]