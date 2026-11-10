---
Area: Research
datetime_stamp: 2026-10-31T00:00:00-05:00
status: draft
confidence: tentative
tags:
  - genesis-scheme
  - generative-system
  - visual-review
links:
  - "[[Research Index]]"
summary: Existing visual provenance and comparison cautions for a bounded generative review, without physics or novelty claims.
canonical: false
---

# Generative Review — Existing Evidence

Genesis is being reviewed here as a generative system. Physics interpretations remain personal speculation. This inventory reads existing scripts, findings, and images only; it runs no experiments and changes no engine.

The subsequent fixed comparison and gallery are recorded in
[[Genesis Generative Review — 2026-10-31]]. This inventory remains its source
provenance, not a replacement for those new observations.

## What the seven existing figures represent

The directory is [findings/figures](../../../findings/figures), containing seven PNGs; there is no separate figures7 directory.

- `dash_primer` and `structure_ladder` are explanatory drawings produced by [the primer](../../../genesis_v2_dash_primer.py) and [ladder](../../../genesis_v2_structure_ladder.py). Their schematic objects are illustrations, not generated examples.
- `v2_visual_story`, `theta_process_plate`, `theta_field_explainer`, and `v2_coarsening_explainer` use **V2-zeta**, not current V1 or V2-integrated. [Visual story](../../../genesis_v2_visual_story.py) and [process plate](../../../genesis_v2_theta_process_plate.py) supply exact provenance: seed 1, N64, snapshots at 2,000 and 8,000 updates, P-to-A 0.05, relation gain 0.55, refractory production 0.020, suppression gain 0.90. The process plate and visual story were visually inspected for this review.
- [Field guide](../../../genesis_v2_field_guide.py) compares delta, epsilon, and zeta at update 2,000, plus late zeta at 8,000. Its header broadly says every panel is at 2,000; the explicit late-panel label and source override that simplification.

These show early/intermediate orientation regions and later coarsening. Dashed outlines come from relation-domain detection, not independently simulated particles or solid walls. The [zeta finding](../../../findings/2026-10-11_v2_zeta_refractory_benchmark.md) records delayed merger but no sustained renewal cycle in the tested long run. This is a temporal result for those conditions, not a verdict on generative usefulness.

## Distinct generative families

**Minimal current V1:** the [three-rule preset](../../../genesis_v1_compression_ablation.py) combines alignment, compression/deformation, curvature, and post-locking without phase wells or triad templates. Existing [vortex evidence](../../../findings/2026-10-12_v1_topological_objects.md) supports recurring, sometimes long-lived localized winding patterns in tested runs. It does not demonstrate perpetual visual novelty.

**Legacy full monolithic:** [genesis_fields_pretty.py](../../../genesis_fields_pretty.py) defaults to N40, dt0.05, alignment0.3, tension0.015, geometry0.015, four-well0.6, dipole0.3, triads0.8, curvature0.4. Other defaults are tension decay0.02, geometry decay0.05, triad sigma0.8, compression sigma0.25, lock0.75, triad amplification3, phase amplification2.5, shell0.08. Four preferred orientations and absolute-angle L-shaped triad templates are explicit design ingredients. Their visual effects remain valid generative output, but are not discoveries of those preferences.

Legacy extraction must preserve mixed boundaries: alignment wraps, dipole/triad loops clip. Compression uses forward differences; curvature uses pre-shell displacement and epsilon1e-6. Current V1 instead uses centered compression, post-shell curvature, epsilon1e-8. Merely matching parameter names does not match engines.

**V2-integrated:** preserves a V1 comparison path and adds P/A/R state. Its [dose-response evidence](../../../findings/2026-10-11_v2_coupling_dose_response.md) supports changes in alignment, tension, compression, and vortex population with coupling. The seven images above do not visualize that integrated experiment.

## Comparison discipline

Use common initial theta, stated auxiliary initialization, common rendering scales, and labeled update counts. Equal seeds across different constructors need not mean equal theta. Equal update counts across engines need not imply equal effective dynamical time. Cross-engine differences are descriptive comparisons, not isolated causal effects.

Show sequences or motion: a rich screenshot cannot establish sustained activity, and a nearly static final frame does not erase an interesting transient. Record distinct aims such as pattern diversity, deformation, motion, persistence, and response to disturbance. Avoid a single success/failure ranking.

Rendering matters: legacy phase colors are quantized; contours of wrapped theta can create seam-like features; symmetric dashes conceal arrow direction; per-frame normalized tension changes scale. Overlays and schematic arrows must remain distinguishable from simulated state. None of these cautions requires a physics claim or an additional object-validation campaign.
