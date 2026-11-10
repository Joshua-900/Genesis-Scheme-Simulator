---
Area: Governance
datetime_stamp: 2026-10-31T00:00:00-05:00
status: complete
confidence: vetted
tags:
  - governance
  - audit
  - provenance
links:
  - "[[Audit Ledger]]"
  - "[[Engineering Quality Gates]]"
  - "[[V1 Baseline Audit — 2026-10-31]]"
summary: Preserve closed, versioned audit coverage so later reviews inherit unchanged evidence and examine explicit deltas.
canonical: true
---

# Cumulative Audit Protocol

The user's standing instruction is to preserve Genesis V1 and V2 and make audits cumulative. A new chat, elapsed time, or a new speculative direction is not a reason to restart an unchanged baseline audit.

## Scope is the unit of closure

A closed audit records:

1. A unique audit ID, date, and parent audit where applicable.
2. Exact reviewed source and dependency files, SHA-256 hashes, environment, and presets.
3. Claims checked, evidence artifacts and hashes, commands, tests, computed results, and interpretations.
4. Reporting discrepancies, known limitations, untested mechanisms and unresolved questions.
5. A coverage decision for each claim, with links to the relevant evidence.

Closure means that the stated checks have been completed for the stated snapshot. It does not mean all science concerning that snapshot has been proven or every possible defect excluded. An explicitly untested issue remains open; it must not be presented as covered merely because another part was audited.

## Reuse before re-audit

Read [[Audit Ledger]] first. Compare source/evidence fingerprints and relevant dependency versions. If they match, inherit the listed coverage; cite the existing audit instead of repeating its experiments or statistics.

The lightweight verifier performs file and environment comparisons without re-running experiments:

```powershell
& .\.venv\Scripts\python.exe -B -m src.genesis_audit.verify results/v1_baseline_audit_2026-10-31/manifest.json
```

Matching hashes establish input identity, not scientific completeness. Check that the question and preset actually fall within the audit's scope.

## Subsequent work stacks as a delta

A later audit names its parent, lists changed or newly introduced files/claims, and states which inherited conclusions remain applicable. Re-test the affected dependency paths and necessary regressions; do not repeat unrelated closed coverage by default.

Examples:

- A new analysis module needs its own validation; it does not automatically reopen unchanged V1 dynamics.
- A changed tracker can affect identity claims and forecasts without changing the field dynamics.
- A new parameter regime needs evidence for that regime; it cannot inherit an old quantitative effect size automatically.
- A new numerical or statistical dependency can require a focused reproduction check.
- New evidence of a concrete flaw may reopen the affected old claim. Document the reason and correction; do not erase the earlier record or restart everything without a dependency-based reason.

## Preserve provenance

Closed raw audit directories are not overwritten. A correction is a new addendum or child audit linked from the ledger. Historical narrative can receive an explicitly dated pointer to the correction; original data and wording remain available.

Legacy experiments without producer-source hashes remain historical evidence with a provenance limitation. Hashing them now freezes their present contents; it cannot retroactively identify the code that originally generated them.

## Engine preservation

Audits and experiments live in separate modules, scripts, and result directories. They may call V1/V2 through adapters. They do not silently alter either engine to satisfy an interpretation or repair a scientific claim. Any proposed changed dynamics must be named, isolated, and compared against the preserved model.
