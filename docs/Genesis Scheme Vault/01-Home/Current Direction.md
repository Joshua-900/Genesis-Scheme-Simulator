---
Area: Navigation
datetime_stamp: 2026-10-11T00:00:00-05:00
status: in-progress
confidence: vetted
tags:
  - genesis-scheme
  - current-direction
  - project-compass
links:
  - "[[Genesis Scheme Home]]"
  - "[[Genesis Scheme — Ontological Framework of Becoming (Formal)]]"
  - "[[Genesis Mathematics]]"
  - "[[Genesis Scheme Prior Art Review]]"
  - "[[Theory Index]]"
  - "[[Implementation Index]]"
summary: Authoritative current project direction, active milestone, and return-to-work context for the Genesis Scheme.
canonical: true
---

# Current Direction

## Purpose

This note is the authoritative answer to: where did the project stop, what is currently trusted, and what should happen next? Keep it short enough to read before resuming work and update it whenever the active milestone or a project-level decision changes.

## Current Theory State

The current canonical formulation is Unity-first: the Genesis Scheme describes a progression from unity through distinction, relation, emergence, stabilization, and recursion.

Potentiality-Actuality is a draft v2 research direction. It proposes that potentiality and actuality are co-primitive, with differentiation as their irreducible relation. Under this interpretation, unity is either undifferentiated potential or achieved coherence. This is not yet canonical and has not changed the meaning of existing simulations.

## Current Implementation State

- `src/genesis_grid/` is the current v1 experimental engine.
- The v1 engine models an orientation field with modular rules for alignment, compression, curvature, and optional mechanisms.
- Legacy scalar and reaction-diffusion engines remain baselines and historical prototypes.
- The `GenesisEngine` interface and registry permit a future v2 engine with a different state representation without rewriting v1.

## Current Evidence State

- The square-lattice multi-seed measurement is biased and does not yet establish spontaneous symmetry breaking. See the linked finding below.
- Existing simulations are evidence about their specific models, not evidence for metaphysical claims.
- The core dynamical ingredients have established precedents. See [[Genesis Scheme Prior Art Review]].

## Decisions In Force

1. Preserve v1 theory, code, and findings as the comparison baseline.
2. Do not rename or rewrite v1 merely to fit the v2 interpretation.
3. Treat v2 as a separate research programme until it produces a formal distinction, testable observable, or prediction.
4. Treat metaphysical commitments, formal claims, model behavior, and experimental evidence as separate layers.

## Active Milestone

**V1-to-V2 conceptual mapping and higher-order object measurement.** The first bridge draft now defines the terms below at the metaphysical, formal, and model levels:

- potentiality
- actuality
- differentiation
- relation
- achieved unity

The milestone is complete only when it identifies one specific condition that a v2 model must satisfy and that v1 does not merely satisfy by relabeling.

## Current Supporting Experiment

The first headless object census is now specified in [[Higher-Order Object Detection Spec]]. It treats vortex-antivortex pairs as tracked candidates and records their identity, extent, internal state, persistence, dynamics, and relations. A persistent candidate is not yet an autonomous object or evidence for a metaphysical claim.

## Next Concrete Task

Test the v2-gamma boundary hypothesis for stable individuation. Gamma has
passed a preliminary boundary-and-identity scaffold: relation-bounded
components persist under the current tracker, and an inside-component
perturbation usually remains local. It has not shown an observer-robust
component scale or an object-specific response. First compare the same
perturbation just outside a selected component; then assess those two gates
before adding another dynamical rule. V1 remains the comparison model.

## Evidence and Context

- [[Genesis Scheme — Ontological Framework of Becoming (Formal)]]
- [[Genesis Mathematics]]
- [[Genesis Scheme Prior Art Review]]
- [[Genesis v1 Novelty]]
- [[Data Collection for analysis]]
- [[Experimental Results 4-11-2026]]
- [[V1 Pair Census Baseline]]
- [[Genesis Engine v1 recap]]
- [[Genesis Commitments and Bridge Principles]]
- [[Genesis V2 Coupled-Field Scaffold]]
- [[V2 Gamma Boundary Probe]]

## End-of-Session Discipline

Before ending meaningful work:

1. Update this note if the active milestone, next task, or decisions changed.
2. Record empirical results in `findings/`; do not leave conclusions only in a chat or code comment.
3. Link any new theory or research note from the relevant index.
4. Commit one coherent milestone after reviewing the diff.
