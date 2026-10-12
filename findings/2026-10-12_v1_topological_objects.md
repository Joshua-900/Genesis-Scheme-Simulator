# V1 Supports a Reproducible Class of Topological Emergent Objects

## Operational Claim

Under the project’s stated operational definition, the individual `+1` and
`-1` vortices in V1 are supported higher-order **topological objects**. This is
a model-level claim about the V1 lattice dynamics, not a claim of autonomy,
natural kinds, or metaphysical validation.

## Evidence

The individual-vortex census used ten fixed V1 seeds, a `64 x 64` periodic
lattice, `kappa = 0.1`, and 3,000 frames per seed. It found 8,756 tracked
vortices. Of those, 763 persisted for at least 500 frames; their median age
was 1,550 frames. Each run ended with zero net winding, as required on the
periodic domain.

Vortices have a localized plaquette position, an integer winding charge, a
persistent tracker identity, velocity, local structural attributes, and a
finite lifecycle. Unlike the former pair candidate, their identity does not
depend on a greedy opposite-charge pairing rule.

## Matched Robustness Test

For each of 20 fixed seeds, the oldest tracked vortex after 1,000 burn-in
frames was selected. The exact state was cloned into untouched, selected-core,
and distant equal-shaped background branches. The intervention was a smooth
finite angular twist (`0.5` radians, Gaussian width `3` cells), so it did not
insert an opposite charge or impose a discontinuity. Branches then ran for
1,000 frames with strict tracker-ID-and-charge continuation.

| Branch | Median continuation samples | End survival |
|---|---:|---:|
| Untouched | 38.5 / 40 | 9 / 20 |
| Selected core twist | 39 / 40 | 10 / 20 |
| Background twist | 38.5 / 40 | 9 / 20 |

The selected-core result was not distinguishable from untouched (`p = 0.733`,
paired two-sided Wilcoxon). The background branch matched untouched exactly.
Thus the tested smooth local deformation did not destroy the selected vortex’s
strict topological identity or continuation.

## What Has and Has Not Been Shown

The evidence supports a reproducible, localized, quantized, persistent, and
smooth-deformation-robust object class in V1: topological vortices.

It does not establish that vortices are autonomous agents, that their dynamics
close independently of the field, or that the Genesis metaphysics follows from
the model. Vortex-antivortex **pairs** remain relational candidates, not
supported objects under the stronger pair-level gate.
