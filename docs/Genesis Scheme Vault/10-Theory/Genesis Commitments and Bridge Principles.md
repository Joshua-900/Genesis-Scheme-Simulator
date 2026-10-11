---
Area: Theory
datetime_stamp: 2026-10-11T00:00:00-05:00
status: draft
confidence: speculative
tags:
  - genesis-scheme
  - v2
  - potentiality
  - actuality
  - bridge-principles
links:
  - "[[Current Direction]]"
  - "[[Genesis Scheme — Ontological Framework of Becoming (Formal)]]"
  - "[[Genesis Mathematics]]"
  - "[[V1 Pair Census Baseline]]"
  - "[[Genesis Scheme Prior Art Review]]"
summary: Draft commitments and model constraints for a potentiality-actuality v2 research programme, kept distinct from the canonical v1 theory.
canonical: false
---

# Genesis Commitments and Bridge Principles

## Status and Purpose

This is a draft v2 research contract. It does not replace the canonical
Unity-first formulation or rename v1 variables. Its purpose is to state what
the potentiality-actuality interpretation would have to mean formally and
computationally before it merits a separate engine.

The guiding proposal is not that unity is false. It is that unity need not be
the sole primitive. Potentiality and actuality may be co-primitive, with
differentiation as their irreducible relation. On this proposal, unity is
either undifferentiated potential or achieved coherence among differentiated
terms.

## The Five Terms

| Term | Metaphysical role | Formal role | Model-level implication |
| --- | --- | --- | --- |
| Potentiality | What can become determinate without already being determinate | A state of available or weighted possible transitions | A distinct, evolving state component; not a synonym for noise, an initial condition, or unused parameter range |
| Actuality | What is presently determinate or enacted | A state of realized configuration and history-dependent constraint | A distinct, evolving state component that can be held fixed in a counterfactual test |
| Differentiation | The production or maintenance of non-equivalent determinations | Increasing or sustaining distinguishable state/transition structure | A measurable contrast or partition that arises from coupled dynamics, not merely a display palette |
| Relation | Mutual determination that is not reducible to isolated intrinsic properties | A coupling, adjacency, or constraint that changes what transitions are available | Explicit coupling between potentiality and actuality, and between local sites or entities |
| Achieved unity | Coherence attained among differences, not the erasure of difference | A stable, compressible, predictive coarse description of a differentiated system | A higher-order object or regime whose attributes persist and predict behavior at its own scale |

## V1 Bridge

The current `genesis_grid` v1 engine has an orientation field (`theta`) and
auxiliary fields for tension, deformation, and compression. It already models
local relations and produces measurable, persistent vortex-antivortex
relations. The v1 census therefore supplies a useful empirical baseline for
achieved-unity candidates.

V1 does **not** currently provide a dedicated representation of potentiality
that is distinct from actuality. Its fields can be interpreted philosophically
in many ways, but the code does not establish a separate domain of available
transitions whose differences have independently testable consequences.

Accordingly:

- do not relabel `theta` as actuality and `tau` or `C` as potentiality;
- do not rewrite v1 to fit this draft;
- preserve v1 as the comparison model and reuse its headless measurement
  machinery where the observables remain meaningful.

## First Candidate Model Constraint

A v2 model must have a state that factorizes at minimum as:

\[
S_t = (P_t, A_t, R_t)
\]

where `P` is potentiality, `A` is actuality, and `R` is the relational
structure through which they constrain one another. The representation may be
field-based, graph-based, or hybrid, but all three roles must be operationally
distinct.

The transition must make both directions consequential:

\[
P_{t+1} = f(P_t, A_t, R_t), \qquad
A_{t+1} = g(A_t, P_t, R_t), \qquad
R_{t+1} = h(R_t, P_t, A_t).
\]

These expressions are a constraint schema, not yet an equation. They rule out
a decorative second field that never changes the realized dynamics.

### Non-Relabeling Test

V2 is not warranted unless it passes both counterfactual conditions:

1. Hold `A_t` and `R_t` fixed, vary `P_t`; the subsequent actual trajectory
   must differ in a measurable way.
2. Hold `P_t` and `R_t` fixed, vary `A_t`; the subsequent potential trajectory
   must differ in a measurable way.

In shorthand:

\[
P_t \neq P'_t,\ A_t=A'_t,\ R_t=R'_t \Rightarrow A_{t+k} \neq A'_{t+k}
\]

for some stated horizon `k`, and symmetrically for an actuality intervention
affecting later potentiality. A model that fails either condition has not
implemented co-primitive potentiality and actuality; it has supplied a new
name for a single-state model.

## First V2 Experiment

The first v2 experiment should be a paired intervention, not a visual demo:

1. Initialize two states with identical actuality and relation structure.
2. Change only local potentiality in a documented region.
3. Run matched seeds and compare subsequent actualization, object prevalence,
   and object attributes.
4. Repeat symmetrically by changing actuality while preserving potentiality.

The existing object census can be adapted as an observer, but it must not be
assumed that vortices or pairs are the only v2 object type.

## Engineering Boundary

When this draft is promoted, v2 belongs in a separate engine module and
adapter registered through `GenesisEngine`. It must not alter the v1 rule
pipeline, its results, or its definitions. A v2 implementation begins only
after this note has a chosen state representation, update equations, and
intervention metrics.

## What This Does Not Claim

- It does not prove that potentiality and actuality are metaphysically
  co-primitive.
- It does not establish that v1 objects validate the proposed ontology.
- It does not claim originality for duality, potentiality, actuality, or
  relational process as philosophical themes.
- It does not prescribe a final equation or a final object definition.

## Decision Needed Before Code

Choose the first v2 representation family:

1. coupled continuous fields for `P` and `A` on a shared lattice;
2. a graph of entities with potential and actual node/edge states; or
3. a hybrid field-to-object model.

The choice should be made for explanatory power and falsifiability, not
because it produces the most attractive images.
