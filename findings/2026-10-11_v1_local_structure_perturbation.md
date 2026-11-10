# Local Candidate-Associated Structure Weakening Causally Reduces Strict Pair Continuation

> **Audit addendum, 2026-10-31:** the original narrative below is preserved.
> Replaying the archived 30-seed raw records gives medians **21 / 4.5 / 21**
> (untouched / candidate / background), rather than 22 / 5 / 22. The reported
> p≈0.000106 matches a one-sided `less` Wilcoxon test; the corresponding
> two-sided value is approximately **0.000213**. Sidedness was not specified
> in the original prose. The local causal conclusion is retained within its
> stated regime. See the [closed baseline audit](../docs/Genesis%20Scheme%20Vault/40-Experiments/V1%20Baseline%20Audit%20%E2%80%94%202026-10-31.md)
> for exact settings, hashes, provenance limits and cumulative coverage.

## Headline

Across a fixed 30-seed matched perturbation replication, weakening the
candidate-associated structural neighborhood reduced strict pair continuation
relative to both untouched and equal-radius background controls. This is causal
evidence for local structural state in this V1 regime and strict identity
metric; it is not yet evidence of a higher-order object.

## Design

Each seed ran V1 at `kappa=0.1` for 1,000 burn-in frames. The active pair with
the highest compression history was selected. The exact state was cloned into
three branches: untouched; structural state weakened in a radius-5 neighborhood
around the selected pair midpoint; and the same radius and weakening at a
distant background location. The original constituent-ID pair relation was
followed for 1,000 more frames. Transformations count as loss under this strict
identity measurement.

## 30-Seed Replication

| Branch | End survival | Median continuation samples |
|---|---:|---:|
| Untouched | 10 / 30 | 22 |
| Candidate neighborhood | 6 / 30 | 5 |
| Background | 10 / 30 | 22 |

Candidate-neighborhood weakening was lower than the paired background control
in 20 seeds, equal in 9, and higher in 1. The background branch matched the
untouched branch exactly in all 30 seeds. A paired Wilcoxon test of target
versus background continuation gave `p = 0.000106`.

## Interpretation

The equal-shape background control matching untouched behavior supports the
locality of the intervention. The replicated target effect supports the claim
that this local V1 structural state causally affects strict pair continuation.
The endpoint remains deliberately narrow: constituent-ID transformations count
as loss, and natural loss remains common even in controls. The result does not
establish autonomy, self-maintenance, or a higher-order object.

## Next Test

Use this validated causal lead in the V1-derived V2 bridge. Hold the same
high-compression structural substrate fixed and test whether independent P/A
dynamics alter the same continuation measurement without erasing the local
structural effect.
