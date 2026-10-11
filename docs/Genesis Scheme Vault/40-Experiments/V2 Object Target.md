---
Area: Experiments
datetime_stamp: 2026-10-11T00:00:00-05:00
status: draft
confidence: tentative
tags:
  - v2
  - higher-order-objects
  - object-detection
links:
  - "[[Higher-Order Object Detection Spec]]"
  - "[[Genesis V2 Coupled-Field Scaffold]]"
  - "[[Current Direction]]"
summary: Operational target for testing candidate higher-order objects in the low-coupling v2-beta regime.
canonical: false
---

# V2 Object Target

## The Question

Does the distinction-preserving v2-beta regime contain coherent regions that
are bounded, identifiable, and persistent, rather than only textured fields?

## Candidate Contract

A v2 candidate object must satisfy all of the following measurements:

1. **Internal coherence:** its cells exceed a declared local orientation-coherence threshold.
2. **Extent:** it has a connected mask, area, and centroid.
3. **Boundary:** the orientation change across its perimeter exceeds its internal variation.
4. **Identity:** it can be matched to a region in later samples by overlap.
5. **Persistence:** it remains matched for a declared minimum number of samples.

Passing this contract means **persistent coherent-region candidate** only. It
does not establish autonomy, causal closure, natural kinds, or metaphysics.

## First Experiment

Run the read-only detector on the low-coupling beta regime. Record every
region's area, coherence, boundary contrast, birth, last-seen frame, and
persistence. The result determines whether a perturbation test is warranted.
