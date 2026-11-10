
## Overview

This note formalizes a **deterministic mechanism** that yields the **Born rule** within the **Deterministic Dimensional Flow Hypothesis (DDFH)**. The result shows that squared-amplitude statistics can **emerge** from deterministic substrate dynamics plus a thresholding projection, rather than being fundamental randomness.
  

---
 

## 1) Setup

- **State:** an angle $\phi \in [0,2\pi)$ on the substrate.

- **Measurement basis:** an angle $\theta$.

- **Overlap (“intensity”)**:

  $$

  I_{\uparrow}(\phi,\theta) \;=\; \cos^2\!\Big(\tfrac{\phi-\theta}{2}\Big),

  \qquad

  I_{\downarrow}(\phi,\theta) \;=\; 1 - I_{\uparrow}(\phi,\theta).

  $$

- **Deterministic integrate-to-threshold mechanism (two channels):**

  - Two accumulators $(A_{\uparrow},A_{\downarrow})$ start with offsets in $[0,1)$ (take $A_{\uparrow}(0)=\alpha$, $A_{\downarrow}(0)=\beta$; any choice works).

  - On each discrete tick, update

    $$

    A_{\uparrow}\leftarrow A_{\uparrow}+I_{\uparrow},\qquad

    A_{\downarrow}\leftarrow A_{\downarrow}+I_{\downarrow}.

    $$

  - If an accumulator reaches or exceeds threshold $T=1$, that channel **fires** (emits the outcome), and we subtract $1$ from it (carry):

    $$

    A_{i}\leftarrow A_{i}-1.

    $$

  - If both cross on the same tick, use a fixed tie-break (e.g., choose “up”). Ties are measure-zero for irrational increments and at most $O(1)$ effect otherwise.

  

---

  

## 2) Lemma (Born frequencies)

**Claim.** Let $U_N$ be the number of “up” firings in the first $N$ detected events. Then

$$

\lim_{N\to\infty}\frac{U_N}{N}

\;=\;

I_{\uparrow}(\phi,\theta)

\;=\;

\cos^2\!\Big(\tfrac{\phi-\theta}{2}\Big).

$$

  

**Proof sketch.**

1. Let the up-accumulator have initial offset $\alpha\in[0,1)$. Define the rotation sequence

   $$

   z_n \;=\; \big\{\, \alpha + n\,I_{\uparrow}\,\big\} \in [0,1),

   $$

   where $\{x\}$ is the fractional part.

2. On tick $n$, “up” fires iff $z_n + I_{\uparrow} \ge 1$, which is equivalent to the binary increment

   $$

   a_n \;=\; \big\lfloor \alpha + (n+1)I_{\uparrow} \big\rfloor

            \;-\; \big\lfloor \alpha + n I_{\uparrow} \big\rfloor

            \;=\; 1.

   $$

3. The number of up-firings after $N$ events is

   $$

   U_N \;=\; \sum_{n=0}^{N-1} a_n

       \;=\; \big\lfloor \alpha + N I_{\uparrow} \big\rfloor - \big\lfloor \alpha \big\rfloor.

   $$

4. Divide by $N$:

   $$

   \frac{U_N}{N}

   \;=\;

   \frac{ \lfloor \alpha + N I_{\uparrow}\rfloor - \lfloor \alpha\rfloor }{N}

   \;\longrightarrow\; I_{\uparrow}

   \qquad (N\to\infty),

   $$

   since $N I_{\uparrow} - 1 < \lfloor \alpha + N I_{\uparrow}\rfloor - \lfloor \alpha\rfloor \le N I_{\uparrow} + 1$.

5. Symmetrically, the down frequency tends to $1 - I_{\uparrow}$.

  

Therefore the long-run frequencies **exactly match the Born rule**. ∎

  

---

  

## 3) Deterministic POVMs (multi-outcome generalization)

For outcomes $i=1,\dots,k$ with target probabilities $p_i(\phi,\Theta)\ge 0$ and $\sum_i p_i = 1$:

  

- Maintain $k$ accumulators $A_i$ with initial offsets in $[0,1)$.

- Each tick: $A_i \leftarrow A_i + p_i(\phi,\Theta)$ for all $i$.

- While any $A_i \ge 1$, **fire** the $i^\*$ with maximal $A_i$ (fixed tie rule), then set $A_{i^\*} \leftarrow A_{i^\*} - 1$; repeat until all $A_i<1$.

  

**Lemma (asymptotic fairness).** After $N$ firings, the counts $N_i$ satisfy

$$

\big|\,N_i - N\,p_i\,\big| \;\le\; 1 \quad \text{for all } i,

$$

hence $N_i/N \to p_i$ as $N\to\infty$.

  

*Sketch.* One checks the invariant $A_i - N_i \in [0,1)$ by induction: adding $p_i$ and subtracting $1$ exactly when $i$ fires preserves the bound. Thus $N_i = N p_i - (A_i - N_i)$ with the bracketed term in $[0,1)$, yielding the stated error bound.

  

**POVM application.** Take $p_i(\phi,\Theta) = \langle \psi(\phi)\,|\,E_i(\Theta)\,|\,\psi(\phi)\rangle$. The deterministic integrator realizes arbitrary **finite POVM** statistics asymptotically.

  

---

  

## 4) Sequential projective measurements (Lüders-style update)

For a two-outcome projective measurement along $\theta$:

  

- If the outcome is $+1$ (“up”): set $\phi \leftarrow \theta$.

- If the outcome is $-1$ (“down”): set $\phi \leftarrow \theta + \pi$.

- Keep accumulator residues (fractional parts).

  

**Proposition.**

1. **Repeatability:** Immediate re-measurement along $\theta$ yields the same outcome with probability $1$.

2. **Next basis $\theta'$:** Using the updated $\phi_{\text{post}}$, the frequency of “up” is

   $$

   \cos^2\!\Big(\tfrac{\phi_{\text{post}} - \theta'}{2}\Big),

   $$

   i.e., Born-consistent and in line with Lüders’ rule for rank-1 projectors.

  

---

  

## 5) Notes & implications for DDFH

- The construction is **fully deterministic**; apparent probabilities arise from thresholded integration (a coding of circle rotations; cf. Sturmian/Beatty sequences).

- The proof holds for any threshold $T>0$ after rescaling increments by $1/T$.

- Together with a Bell-compatible nonlocal mapping (handled separately), this shows DDFH can **reproduce Born statistics** without intrinsic randomness.

  

---

  

## Tags

#DDFH  #BornRule  #Determinism  #QuantumFoundations

  

**See also:** [[Ddfh Bell Born Models]] · [[Bell Theorem Ddfh Proof]]