---
Area: Experiments
datetime_stamp: 2026-10-31T00:00:00-05:00
status: complete
confidence: vetted
tags:
  - genesis-scheme
  - generative-system
  - visual-review
links:
  - "[[Current Direction]]"
  - "[[Experiments Index]]"
  - "[[Generative Review — Existing Evidence]]"
  - "[[Audit Ledger]]"
summary: A fixed six-configuration visual comparison identifies the historical full recipe's geometry-dependent mosaic formation and late rearrangement, without establishing a globally novel generator or Life-like dynamics.
canonical: false
---

# Genesis Generative Review — 2026-10-31

## What this settles

The user clarified that a distinctive, useful generative system is a worthwhile
objective in itself. Physics remains speculative motivation. This review uses
that objective rather than demanding physical interpretation, autonomous
objects, or an equilibrium theorem from a creative system.

**There is a concrete generative effect worth retaining:** the historical full
recipe changes a fine, nearly frozen mosaic into larger connected patches with
some continuing rearrangement. Removing its geometry bundle removes that
behavior in all three tested seeds. This is an observed contribution of the
existing rules, not a discovery of a new mechanism.

**There is not yet a demonstrated compelling new class of generator.** Minimal
V1 looks broadly like its simpler smoothing controls in this review. V2 gives
a visibly finer texture, but its extra state prevents a single-mechanism
interpretation of that comparison. The historical full recipe is the clearest
lead for a creative demo. Whether its texture is useful or appealing remains
a human judgment; these measurements cannot establish that judgment or global
novelty.

## Look at the outputs

- [Animated six-way comparison](../../../results/generative_review_2026-10-31/comparison.gif).
- [Same-seed progression](../../../results/generative_review_2026-10-31/comparison.png).
- [All three seeds at update 8000](../../../results/generative_review_2026-10-31/all_seeds.png).
- [Matched local pulse](../../../results/generative_review_2026-10-31/pulse.png).
- [Compression indicator, shared 0–1 scale](../../../results/generative_review_2026-10-31/compression.png).
- [Activity and roughness](../../../results/generative_review_2026-10-31/activity.png).

Colors represent theta orientation, not height or matter. Every orientation
panel uses the same cyclic palette and fixed range. There are no inferred
boundary outlines. The compression indicator is shown separately and is not
a geometric height map. Seed1 was specified for animation before examining
results; the other seeds are included rather than selecting the nicest run.

## Fixed comparison

Study: `generative_review_2026-10-31`. Six configurations, N64, seeds 1/7/42,
8000 updates, dt 0.05, snapshots every 100 updates. No parameter search.
All configurations receive identical initial theta arrays. Structural fields
start zero; V2 retains its native seeded additional source fields. The historical
recipe uses the existing GUI parameter defaults at the common N64 size, rather
than the GUI's default N40.

The two geometry-disabled controls set kappa, shell gain and curvature strength
to zero, retaining their other rules and coefficients. That tests the geometry
bundle as a whole, not its individual components. Alignment alone is a separate
simple reference. Equal update counts are not equal physical time or matched
effective relaxation speed across different recipes.

The original GUI file is not imported. A headless vectorized implementation
preserves its mixed boundaries and stage timing. Tests compare it against the
AST-extracted original update for ten steps on two grid sizes, with geometry
enabled and disabled. Agreement is within 2e-11; different floating summation
orders mean long trajectories are not claimed to be bitwise historical replays.
The historical four preferred angles and directional triad templates are
supplied ingredients, not spontaneously discovered preferences.

## What changed, quantitatively

Late activity below is the mean RMS phasor change per 100 updates over the
sampled update 4000–8000 window, after removing the best common phase rotation.
Values are ranges over the three seeds, not confidence intervals. Roughness
is mean nearest-neighbor orientation disagreement, not a quality score.

| Configuration | Late spatial activity | Final roughness |
| --- | ---: | ---: |
| Alignment only | 0.0169–0.0187 | 0.0216–0.0260 |
| V1 structural | 0.0131–0.0190 | 0.0237–0.0259 |
| V1 without geometry | 0.0146–0.0181 | 0.0208–0.0277 |
| Historical full recipe | 0.0113–0.0194 | 0.2521–0.2778 |
| Historical texture rules, no geometry | <2e-9 | 0.5376–0.5627 |
| V2 bridge, gain0.20 | 0.0160–0.0219 | 0.0714–0.0800 |

The clearest visual contribution is formation of larger patches in the full
historical recipe, rather than merely different colors. Late activity is
measurable, but the images also show substantial settling. It does not establish
indefinite renewal, recurring births, traveling structures, or computational
universality. Continued smoothing in the simple reference is also activity;
activity alone is not evidence of novelty.

At update 4000 each state was cloned and given the same compact radius 5,
pi/2 angular pulse at the center. After 400 updates, full-recipe global RMS
phasor differences were 0.0769–0.1016; the no-geometry texture control gave
0.1087–0.1430. Both retain a localized response. The control has the larger
response here; this is not evidence that geometry improves editability or
propagates a new object. One location and amplitude do not characterize all
possible interactions.

The stored winding count closes plaquettes periodically, including in the
historical recipe with mixed interaction boundaries. It is only a descriptive
diagnostic and is not an object census. No synthetic “interestingness” score
or new pass/fail gate was introduced.

## Decision and next useful work

Keep the historical full recipe as the strongest demonstrated texture lead.
Keep V2 as an alternative visual style and preserve minimal V1 as a reference.
This result supports a small creative demonstration, not another open-ended
mechanism or parameter campaign.

The recommended next milestone is a bounded interactive sandbox using these
unchanged recipes: paint local orientation, pause/step, compare geometry on/off,
and save an image. Judge it by whether a person can deliberately make or modify
patterns they want to keep. If the textures and interactions remain uninteresting
in use, archive this branch of exploration instead of adding rules to justify it.
That is a recommendation, not a claim that the present gallery already supplies
an interactive sandbox.

## Reproduction and preservation

New code lives in `src/genesis_gallery/`; parity and initialization checks live
in `tests/test_generative_review.py`. All 41 repository tests pass. V1/V2 engine
sources, the original GUI recipe and closed audit evidence remain unchanged.
The baseline fingerprint verification is inherited; the old scientific tests
were not repeated to judge generative merit.

From the repository root in PowerShell:

```powershell
$env:GENESIS_USE_CUPY='False'
$env:OPENBLAS_NUM_THREADS='1'
$env:MPLCONFIGDIR=Join-Path (Get-Location) 'work/matplotlib'
.venv\Scripts\python.exe -B -m src.genesis_gallery.review --output results/generative_review_replay
.venv\Scripts\python.exe -B -m src.genesis_gallery.render results/generative_review_replay
```

The runner refuses to overwrite an existing review directory.
[Protocol](../../../results/generative_review_2026-10-31/protocol.json),
[full report](../../../results/generative_review_2026-10-31/report.json), and
[artifact manifest](../../../results/generative_review_2026-10-31/manifest.json)
preserve parameters, source fingerprints, observations and output hashes.
Snapshots are stored as float32; reported measurements were computed before
that quantization. Tiny residual activity cannot be reconstructed accurately
from the saved float32 snapshots; use the recorded report or a source replay.
