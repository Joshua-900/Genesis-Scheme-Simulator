 

## 1) Setup on S²

- State (qubit) as a unit vector $n \in S^2$ (Bloch vector).

- Projective measurement along unit vector $m \in S^2$.

- Overlap (Born probability):

$$

p_\uparrow(n,m) \;=\; \frac{1 + n\!\cdot\! m}{2} \;=\; \cos^2\!\Big(\tfrac{\gamma}{2}\Big),

$$

where $\gamma$ is the geodesic angle between $n$ and $m$.

  

## 2) Deterministic two-channel integrator

- Two accumulators $(A_\uparrow,A_\downarrow)$ with offsets in $[0,1)$.

- Per tick: $A_\uparrow \!\leftarrow\! A_\uparrow + p_\uparrow$, $A_\downarrow \!\leftarrow\! A_\downarrow + (1-p_\uparrow)$.

- When any $A_i \ge 1$, fire outcome $i$, set $A_i \!\leftarrow\! A_i - 1$ (fixed tie rule).

  

**Theorem (Born on $S^2$).** Long-run fraction of “up” equals $p_\uparrow(n,m)$.  

*Sketch:* identical number-theory argument as the circle case.

  

## 3) Sequential projective measurements (Lüders on S²)

Update rule after an outcome $s \in \{+1,-1\}$ along $m$:

$$

n \;\leftarrow\; s\,m \,.

$$

Then for a next measurement along $m'$,

$$

\Pr(\text{up at } m') \;=\; \frac{1 + (s\,m)\!\cdot\! m'}{2} \;=\; \cos^2\!\Big(\tfrac{\angle(s\,m,m')}{2}\Big),

$$

giving **repeatability** and **Lüders-consistent** statistics.

  

## 4) Bell/CHSH on S² (singlet)

For a bipartite singlet, take measurement axes $m_x, m_y \in S^2$ (Alice/Bob). Use the same deterministic **atemporal** rule as before but with the geometric input

$$

E(x,y) \;=\; -\, m_x \!\cdot\! m_y \,.

$$

This yields no-signaling and CHSH:

$$

S \;=\; |E(a,b)+E(a,b')+E(a',b)-E(a',b')| \;\le\; 2\sqrt{2},

$$

with the standard choice saturating $2\sqrt{2}$.

  

## 5) POVMs on S²

For a finite POVM $\{E_i\}$, set per-tick increments

$$

p_i(n,\Theta) \;=\; \langle \psi(n) | \, E_i(\Theta)\, | \psi(n) \rangle,

\qquad

|\psi(n)\rangle \ \text{the Bloch-sphere qubit for } n,

$$

and run the $k$-channel integrator. Then $N_i/N \to p_i$ with $|N_i - N p_i| \le 1$.

  

## 6) Relativity-friendly phrasing (pointer)

Define the invariant angle via local rest frames; predictions depend only on $m_x\!\cdot\! m_y$ (or its covariant generalization), keeping $E=-m_x\!\cdot\! m_y$ frame-independent.