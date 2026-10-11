---
Area: Governance
datetime_stamp: 2026-10-11T00:00:00-05:00
status: complete
confidence: vetted
tags:
  - governance
  - quality
  - engineering
  - verification
links:
  - "[[Rules]]"
  - "[[Genesis Scheme Home]]"
summary: Quality gates for changing the Genesis Scheme theory, implementation, experiments, and supporting documentation.
canonical: true
---

# Quality Gates

## Theory changes

Before treating a theoretical change as canonical:

- State the claim, definitions, and scope clearly.
- Identify which existing claim it refines, replaces, or conflicts with.
- Separate derivation from intuition and speculation.
- Record confidence honestly.
- Link related mathematics, operators, invariants, and consequences.

## Implementation changes

Before treating an implementation change as complete:

- Identify the theoretical concept it represents or tests.
- State where the implementation is an approximation, prototype, or known divergence.
- Run the relevant checks or experiments.
- Record observable limitations and unexpected behavior.
- Keep implementation claims subordinate to canonical theory unless the theory is explicitly revised.

## Experimental claims

Before using an experiment as evidence:

- Record parameters, procedure, and environment.
- Preserve raw outputs where practical.
- Distinguish observation from interpretation.
- State what the experiment can and cannot establish.
- Link the result to the claim it supports or challenges.

## Documentation changes

Before committing a milestone:

- Validate frontmatter and links.
- Review the diff for accidental generated files, secrets, or unrelated edits.
- Confirm the note's status, confidence, and canonical flag still agree with its content.
- Prefer one coherent change over scattered partial updates.
