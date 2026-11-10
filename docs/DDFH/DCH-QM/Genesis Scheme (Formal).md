
## Symbols

- **G:** the Ground
- **Δ:** distinction operator
- **Σ:** “something” (presence predicate)
- **N:** “nothing” (absence predicate, i.e., ¬Σ)
- **Λ:** nonempty set of rule-maps (“laws”) on states of G
- **ρ:** recursion = iterated application of Λ
- **S:** a state of G

---

## Axioms (minimal set)

- **A1 (Existence/Totality).** ∃G such that ∀x (x exists ⇒ x ∈ G). (Nothing is outside G.)
- **A2 (Indivisibility/Autonomy).** G has no proper parts on which it depends; all operations are internal to G.
- **A3 (Potentiality).** G admits internal distinctions: ∃Δ with Δ(G) = ⟨Σ, N⟩ where N := ¬Σ. (Fundamental duality: presence/absence.)
- **A4 (Transformability).** The states of G are transformable: ∃S and ∃f with f(S) ≠ S. (Movement is possible.)
- **A5 (Lawfulness).** ∃Λ ≠ ∅ with each λ ∈ Λ a map on states of G, closed under composition (λ∘λ′ ∈ Λ). (Rules exist.)
- **A6 (Closure).** Application of any λ ∈ Λ to any state of G yields a state of G. (No evolution “leaves” G.)

---

## Definitions

- **D1 (Recursion).** ρ on state S₀ is the sequence S_{t+1} := λ_t(S_t), with λ_t ∈ Λ.
- **D2 (Fixed point / cycle).** A state S* with λ(S*) = S* is a fixed point; a finite k-cycle satisfies λ^k(S) = S.
- **D3 (Mediation / Triad).** The triple ⟨G, Δ, Λ⟩ is the minimal generative structure: unity (G), duality (Δ), operation (Λ).

---

## Propositions (from A1–A6)

- **P1 (Triad Emergence).** From A1–A3 (unity→duality) and A5 (operation), ⟨G, Δ, Λ⟩ forms a triad. (Derives the “third” as mediation.)
- **P2 (Continuity / Time-Order).** From D1 and A5, ρ induces an ordered sequence {S_t}; this order is the minimal notion of time.
- **P3 (Self-sustainment).** If ∃S* s.t. λ(S*) = S* or a limit cycle under Λ, then persistence obtains. (Continuity from rules+closure.)
- **P4 (Emergence).** If Λ is nontrivial (A4) and closed (A5–A6), there exist invariant features under ρ (conserved or repeating patterns); interactions of such invariants yield higher-order structure.
- **P5 (Universality—possibility).** If Λ is sufficiently expressive (able to encode composition, memory, and propagation), ρ can realize universal computation within G. (A modal claim: possible, not guaranteed.)

---

## Minimal Runtime (pseudocode)

```
S0 := undifferentiated state of G
⟨Σ, N⟩ := Δ(G)          // fundamental duality (presence/absence)
while evolving:
    pick λ ∈ Λ           // lawful step
    S := λ(S)            // recursion (closure ensures S ∈ G)
```

---

## Reading Guide (one-liners)

- G must exist (A1); nothing is outside it.
- G can draw a first mark (A3): Σ vs N.
- Change is possible (A4) and law-governed (A5).
- Recursion over laws (D1) yields time/continuity (P2), persistence (P3), and emergent structure (P4).
- With rich enough Λ, computation (and thus “world-building”) is possible (P5).

---

## Relations

- Rooted in [[Ground (Formal)]].
- Represented diagrammatically in [[Genesis Ladder]].
- Instantiated in physics by [[DDFH Dashboard Map]].

---

Corrections:
G must be refined to be more accurate and irrefutable:

∀x ( Ex(x) ↔ x = G )  
## Tags

#core/genesis-scheme #formal #axioms #recursion