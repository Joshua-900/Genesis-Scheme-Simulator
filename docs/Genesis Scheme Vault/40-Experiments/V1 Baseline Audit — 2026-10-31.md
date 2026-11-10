---
Area: Experiments
datetime_stamp: 2026-10-31T00:00:00-05:00
status: complete
confidence: vetted
tags:
  - genesis-scheme
  - v1
  - audit
  - evidence
links:
  - "[[Audit Ledger]]"
  - "[[Cumulative Audit Protocol]]"
  - "[[Current Direction]]"
  - "[[Higher-Order Object Detection Spec]]"
  - "[[Genesis Multiscale Organization Audit Results]]"
summary: Closed snapshot audit reconciling V1 object and local-structure evidence, documenting equation semantics, provenance limits and inherited coverage.
canonical: false
---

# V1 Baseline Audit — 2026-10-31

## Conclusion

**The user's recollection was substantially correct: V1 already has evidence that local structural state causally affects strict continuation of tracked vortex-pair relations.** The question should not have been reintroduced as though that effect had never been tested.

The stronger question of a quantitative, transferable, history-dependent interaction law is different and remains open. No new vortex interaction experiment was performed in this audit.

This audit is closed for the named scope below. Future audits inherit this coverage when the relevant files, evidence, environment and preset match. See [[Cumulative Audit Protocol]] and [[Audit Ledger]].

## Scope and frozen record

Audit ID: `v1_baseline_audit_2026-10-31`.

Reviewed: the current three-rule V1 structural preset used by the object studies; relevant archived structural, vortex and pair-forecast evidence; exact update semantics; original V2 regression coverage and isolated audit regressions. The audit replayed archived measurements and forecast fits, and executed small equation probes. It did not rerun the old simulation cohorts.

- [Manifest: source and evidence hashes, environment and scope](../../../results/v1_baseline_audit_2026-10-31/manifest.json)
- [Machine-readable calculations and probes](../../../results/v1_baseline_audit_2026-10-31/report.json)
- [Regression test log](../../../results/v1_baseline_audit_2026-10-31/test_log.txt)
- [Audit runner](../../../src/genesis_audit/v1_baseline.py)
- [Read-only fingerprint verifier](../../../src/genesis_audit/verify.py)

All 53 V1/V2 Python engine sources and the reviewed producers/tests were fingerprinted. All 10 selected evidence artifacts were hashed and unchanged after replay. All 18 regression tests passed. V2 is preserved, not comprehensively scientifically audited here.

Legacy experiment artifacts do not contain producer-source hashes. Their data can be checked now, but today's sources cannot be cryptographically identified as their historical producers. This is a recorded limitation, not an excuse to erase the evidence or rerun it indefinitely.

## Claims ledger

| ID | Claim | Audited conclusion |
| --- | --- | --- |
| V1-C01 | Individual vortices form a persistent topological object class | Archived census supports it within the operational definition |
| V1-C02 | The tested smooth core perturbation generally destroys vortex identity | Not supported; documented identity continuation remains consistent with robustness, not formal statistical equivalence |
| V1-C03 | Local structural state causally affects strict selected-pair continuation | Supported in the documented 30-seed high-compression intervention |
| V1-C04 | The model stores history in structural variables | Explicitly present in the recurrence equations |
| V1-C05 | Relational pair state contains replicated forecast information | Supported, but original stronger object gate remains not passed |
| V1-C06 | Vortices have a transferable history-dependent interaction law | Not established by these studies; distinct from C03–C05 |
| V1-C07 | Nested scale summaries earn a bulk interpretation | Not supported by the 2026-10-31 prediction audit |

These IDs support precise inheritance: a later study should say which claim it extends, rather than treating “V1 audited” as an unlimited statement.

## Evidence replay

### Local structural causality: retained, with a numerical reporting correction

The merged 30-seed archive exactly matches the three ten-seed batch files. Its raw branch records agree with its stored summary:

| Branch | Median continuation samples | End survival |
| --- | ---: | ---: |
| Untouched | 21 | 10/30 |
| Candidate-associated neighborhood weakened | 4.5 | 6/30 |
| Matched background weakened | 21 | 10/30 |

Candidate weakening gives lower continuation in 20 seeds, equal continuation in 9, and higher continuation in 1. Background continuation matches untouched in every seed. The minimum periodic midpoint-to-background distance in these archived records is about 12.82 sites, above twice the radius-5 intervention. The implementation's background selection uses an ordinary coordinate-distance exclusion rather than a periodic one; the archived midpoint separation check does not reveal overlap, but it does not reconstruct every constituent-site exclusion.

For paired target versus background continuation, using SciPy 1.16.3, `zero_method='wilcox'`, `correction=False`, and the asymptotic (`method='approx'`) test:

- Two-sided p-value: **0.0002127560**.
- One-sided `alternative='less'` p-value: **0.0001063780**.

The original narrative reports medians 22/5/22 and p approximately 0.000106 without sidedness. The archived data support 21/4.5/21, and the old p-value matches the one-sided calculation. The numerical discrepancy is documented rather than silently rewriting the historical finding. Both calculations retain evidence for the narrow intervention effect; the one-sided choice should not be retroactively described as predeclared when the archive does not document it.

The intervention jointly changes tension, displacement and compression, while θ initially remains unchanged. It therefore supports a role for the joint structural state. It does not separately identify compression, tension, deformation, or a force law. Candidate selection favors the most compressed active pair and is not a random sample of all vortices. Strict tracker identity can be lost through transformation or matching changes as well as physical disappearance.

See the original [local structural finding](../../../findings/2026-10-11_v1_local_structure_perturbation.md) and [archived records](../../../results/v1_local_structure_perturbation_30seed.json).

### Individual vortices: census and tested robustness retained

Recounting the archived vortex records reproduces 8,756 tracked vortices, including 763 with maximum age at least 500 frames; their median maximum age is 1,550 frames. All ten census seeds end with zero net winding.

The 20-seed robustness archive reproduces continuation medians 38.5/39/38.5 for untouched/core/background. A two-sided paired Wilcoxon calculation gives p approximately 0.73348 for core versus untouched. The tested perturbation did not yield evidence of reduced continuation; failure to reject a difference is not a formal equivalence proof.

See [the topological object finding](../../../findings/2026-10-12_v1_topological_objects.md).

### Pair forecasts: useful relation, original gate still not passed

Refitting the original ridge models from archived records and holding out the original seeds reproduces:

| Cohort | Records | Brier reduction | Held-out seed wins | Original gate |
| --- | ---: | ---: | ---: | --- |
| Seeds 1–10 | 5,043 | 3.7168% | 9/10 | Not passed |
| Seeds 11–20 | 5,248 | 4.7370% | 10/10 | Not passed |

The combined descriptive reduction is 4.2467%. Relational information is reproducible; the original 5% requirement remains unmet. This is a survival forecast, not a learned law of position, motion, interaction or independent dynamical closure.

See [the pair forecast finding](../../../findings/2026-10-12_v1_pair_object_forecast_gate.md).

## Equation semantics: established facts, not automatic bugs

### Tension stores history of net torque

For the named preset, let

\[
a_i^n=\sum_{j\sim i}\sin(\theta_j^n-\theta_i^n),\qquad
\tau_i^{n+1}=(1-d)\tau_i^n+\gamma|a_i^n|.
\]

With fixed coefficients, the recurrence explicitly gives

\[
\tau_i^n=(1-d)^n\tau_i^0+
\gamma\sum_{k=0}^{n-1}(1-d)^{n-1-k}|a_i^k|.
\]

Thus structural history storage is mathematically explicit in update count. The causal intervention demonstrates consequences of structural state for the selected continuation metric. Neither statement alone proves an autonomous interaction law between objects.

An equation probe gives net-torque magnitude zero while the positive disagreement diagnostic `sum(1-cos(delta_theta))` equals four. Opposing torques cancel. `grad_align` is not total disagreement, a positive bond energy, or a physical energy density merely because of its name.

### Supplied turning direction

The compression rule adds `+0.1*tau` to angular torque. A probe with initial τ=1 and zero source returns +0.098 after tension decay. Nonnegative τ therefore supplies a fixed-sign angular contribution. This must be included in symmetry interpretations; it need not be removed or called a defect without deciding the intended theory.

### Mixed update conventions

The same starting state at half `dt` produces identical one-update τ, ux, uy and C, while θ increments halve, to approximately 9e-16 numerical residual. Structural recurrences are per update; θ explicitly uses `dt`.

No physical-time convergence claim is certified. Before interpreting smaller `dt` as a finer discretization of one continuous-time model, the intended timescale convention must be specified. V1 remains a defined discrete-time system at its fixed preset.

### Compression label

`C=exp(-detF**2/(sigma_c2+1e-8))` emphasizes near-singular deformation. It equals one at determinant zero and about 1.125e-7 at either +1 or -1 for the preset. It is sign-insensitive and is not a general pressure, density or energy measure. No third spatial displacement is present.

## Closed coverage and next action

The archived causal effect should be cited and inherited, not re-proposed as an untested conjecture. The update semantics above should be used when explaining V1. Original engine bytes, archived data, thresholds and negative results remain intact.

This is not a complete audit of all optional rules, numerical limits, or fundamental physical interpretations. Those are explicit open scopes in [[Audit Ledger]], available for future focused work without restarting the completed checks. A new history-dependent interaction experiment would address a new claim and is not authorized or performed by this audit record alone.

Verify the frozen inputs with the ledger's command. A rerun of the audit calculations, if justified, must use a new directory and identify its parent audit; never overwrite this closed record.
