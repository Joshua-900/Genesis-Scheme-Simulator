---
Area: Experiments
datetime_stamp: 2026-10-11T00:00:00-05:00
status: draft
confidence: tentative
tags:
  - experiments
  - higher-order-objects
  - measurement
  - headless
links:
  - "[[Experiments Index]]"
  - "[[Current Direction]]"
  - "[[Genesis Engine v1 recap]]"
  - "[[Genesis Mathematics]]"
summary: Operational definition and first measurement plan for identifying higher-order objects in Genesis simulations.
canonical: false
---

# Higher-Order Object Detection Spec

## Purpose

This note defines a higher-order object as an empirical designation. It does not claim that a visual pattern, a simulation result, or a measured object establishes a metaphysical conclusion.

The first target is a vortex-antivortex pair. It is chosen because the v1 engine already detects defects and tracks their identity through time. Other candidates, such as coherent compressed domains, must be assessed against the same criteria rather than accepted by appearance.

## Operational Definition

A higher-order object candidate is a localized, repeatably detectable configuration with attributes that remain meaningful over time. A candidate becomes a supported object type only after its attributes are measured across runs and its identity survives the stated matching and perturbation checks.

The required attribute families are:

| Family | Question | First v1 measurement |
| --- | --- | --- |
| Identity | Can this instance be distinguished from others? | Persistent tracker ID and constituent defect IDs |
| Extent | Where is it and how large is it? | Midpoint, endpoints, orientation, and pair length |
| Internal state | What describes its organization? | Topological charges, line coherence, compression, and relational activity |
| Persistence | Does it continue beyond one observation? | Birth frame, last-seen frame, age, and observation count |
| Dynamics | Does it change in a describable way? | Closing speed and length history |
| Relations | Does it have structured interaction with its environment? | Opposite-charge pairing, compression along the relation, and lifecycle events |
| Robustness | Is it reproducible rather than a one-off artifact? | Multi-seed prevalence and later small-perturbation comparison |

A candidate is not called an autonomous object merely because it persists. Autonomy requires a later, explicit test that its coarse attributes predict its short-term behavior better than a generic local-field baseline.

## First Headless Experiment: Pair Census

`genesis_object_census.py` runs the current v1 rule pipeline without a visual interface. At a fixed sampling interval it:

1. detects topological defects;
2. assigns persistent defect identities;
3. constructs conservative, opposite-charge pair candidates;
4. records the attributes above for every observed pair; and
5. writes a JSON report suitable for comparison across seeds and parameter sets.

The default recognition threshold is deliberately modest: a pair must survive for a configured number of frames and be observed repeatedly. Passing it means only **persistent candidate**, not confirmed autonomy or a new physical entity.

## Questions This Can Answer

- Are pair candidates recurrent across random initial conditions?
- What lifetime, size, coherence, compression, and closing-speed distributions do they have?
- Which parameter settings make persistent candidates more or less prevalent?
- Do apparent objects survive when their definition is applied without visualization?

## Questions It Cannot Yet Answer

- Whether the candidate has causal autonomy.
- Whether it is a natural kind rather than a convenient detector output.
- Whether any observed behavior validates the Genesis metaphysics.
- Whether a result generalizes beyond the square lattice and this specific v1 model.

## Acceptance Criteria For This Milestone

The initial census milestone is complete when at least one multi-seed run reports:

1. the exact model parameters and random seeds;
2. raw per-observation attributes and lifecycle summaries;
3. a declared recognition threshold;
4. prevalence and lifetime distributions; and
5. a written limit statement separating observation from interpretation.

The next experiment after that is a controlled perturbation test: restart matched states with a small, documented change and compare object matching, lifetime, and attribute trajectories.

## First Detector Control

Before a perturbation test, run `genesis_object_sensitivity.py`. It holds the
v1 dynamics and seeds fixed while varying only sampling interval and the
maximum opposite-charge pairing distance. Its result answers a narrower but
necessary question: do the prevalence and lifetime distributions remain
recognizably similar when the detector configuration changes?

It is a distributional robustness check. One-to-one identity across detector
settings requires a later continuity-aware matching experiment. The control
must adjust its observation-count requirement by sample interval so that every
condition represents the same elapsed-time persistence threshold.
