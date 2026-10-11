---
Area: Governance
datetime_stamp: 2026-10-11T00:00:00-05:00
status: complete
confidence: vetted
tags:
  - governance
  - rules
  - knowledge-base
links:
  - "[[Frontmatter Standard]]"
  - "[[Canonical Values]]"
  - "[[Genesis Scheme Home]]"
summary: Vault-wide rules for organizing Genesis Scheme knowledge and distinguishing theory from implementation.
canonical: true
---

# Vault Rules

## Purpose

This vault is the durable knowledge base for the Genesis Scheme. It preserves the theory, its mathematical development, its implementation, and the experiments used to evaluate it.

The theory is primary. Implementation notes explain a current representation of the theory. Experimental notes record evidence and observations. Research and session notes preserve context and may be promoted when their claims are reviewed.

## Authority model

- **Canonical theory** states the current authoritative concepts, definitions, mathematics, and invariants.
- **Implementation** describes how the current software expresses or tests the theory. It cannot silently redefine the theory.
- **Experiments** record procedures, parameters, results, and limitations. Results can support, challenge, or revise a theoretical claim, but they do not become theory merely by existing.
- **Research and session notes** preserve exploration, alternatives, and provenance. They are not authoritative unless explicitly promoted.

When sources conflict, prefer the most recent reviewed canonical theory note. If the conflict is unresolved, record it rather than hiding it through duplicated edits.

## Required note properties

Every Markdown note must include:

- `Area`
- `datetime_stamp`
- `status`
- `confidence`
- `tags`
- `links`
- `summary`
- `canonical`

Use the field names and values defined by [[Frontmatter Standard]] and [[Canonical Values]]. Update `datetime_stamp` after a substantive review or change.

## Canonical handling

- `canonical: true` means the note is an authoritative standard or current statement of the project.
- `canonical: false` means the note is exploratory, historical, provisional, or subordinate.
- Do not mark a note canonical just because it is old, polished, or interesting.
- Prefer one canonical note per concept. Link to it rather than copying its authority into several notes.

## Organization

Use folders to communicate primary purpose. Keep governance, theory, operators, implementation, experiments, research, and archival material distinguishable. A note may link across areas, but it should have one primary home.

## Agent and editor behavior

- Preserve provenance when editing imported or session material.
- Do not upgrade confidence without evidence or review.
- Do not invent new lifecycle or confidence values.
- Repair missing metadata before relying on a note as a source of truth.
- Prefer links and explicit supersession over silent duplication.
- Keep code behavior and theoretical claims explicitly distinguished.
