---
Area: Governance
datetime_stamp: 2026-10-11T00:00:00-05:00
status: complete
confidence: vetted
tags:
  - governance
  - workflow
  - return-to-work
links:
  - "[[Current Direction]]"
  - "[[Genesis Scheme Home]]"
  - "[[Engineering Quality Gates]]"
summary: Repeatable procedure for resuming Genesis Scheme work after a break without reconstructing project context from scratch.
canonical: true
---

# Return Protocol

## Resume Work

1. Read [[Current Direction]] before opening code or changing a note.
2. Read [[Genesis Scheme Home]] and the notes linked from the active milestone.
3. Review the most recent relevant finding and any open research constraint.
4. Start the project from the repository root with `.\launch.ps1` in PowerShell.
5. Complete the named next task, or update [[Current Direction]] before taking a different direction.

## End Work

1. Record a result, decision, or blocker in its proper place.
2. Update [[Current Direction]] when the active milestone or next task changes.
3. Review the diff for unrelated files and generated artifacts.
4. Commit one coherent milestone.

## Source-of-Truth Map

| Need | Source |
| --- | --- |
| Setup and entry point | `README.md` |
| Current focus and next task | [[Current Direction]] |
| Theory and formal commitments | [[Theory Index]] |
| Code organization | [[Implementation Index]] and `architecture.md` |
| Experimental evidence | [[Experiments Index]] and `findings/` |
| Research context and prior art | [[Research Index]] |
