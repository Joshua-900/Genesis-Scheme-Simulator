---
Area: Implementation
datetime_stamp: 2026-11-01T00:00:00-05:00
status: complete
confidence: vetted
tags:
  - genesis-scheme
  - generative-system
  - creative-sandbox
links:
  - "[[Implementation Index]]"
  - "[[Current Direction]]"
  - "[[Genesis Generative Review — 2026-10-31]]"
summary: Native paired-lane creative sandbox using the preserved historical rules, with local painting, fixed-scale views, image export and deterministic recipe replay.
canonical: false
---

# Genesis Creative Sandbox

The creative sandbox is ready for use. It wraps the existing historical full
recipe and its geometry-disabled comparison in a separate native PyQt window.
It adds interaction and export, without adding a dynamical mechanism or
changing V1, V2, the historical recipe, or the completed generative review.

## Start and use

From the repository root in PowerShell:

```powershell
.\launch_sandbox.ps1
```

Or use `.venv\Scripts\python.exe -B -m src.genesis_sandbox --seed 7`.
The existing main launcher is preserved. The sandbox uses already installed
numpy, matplotlib, Pillow and PyQt5 dependencies. It runs on CPU.

1. Click **Grow +1000** to form a texture. It grows in small batches, with the
   update count visible; **Pause** stops the queued growth.
2. Select **Set orientation**, an angle and brush radius. Click or drag either
   field. Painting pauses growth and applies the same prescription to both lanes.
3. Click **Play** to see how those edits evolve, or **Step +1** for one update.
   Speed changes the number of discrete updates per frame, not the equations.
4. Switch between **Orientation θ** and **Compression C**. Painting is available
   in the orientation view. Both views use fixed scales; C is a model indicator,
   not a height map. Reset starts both lanes from the displayed seed and clears
   that session's edit history.
5. Click **Export PNG + recipe**. This pauses and writes a fresh bundle under
   `work/sandbox_exports/`; the saved image link opens the exported PNG.

**Set** follows the shortest angular path toward the selected orientation,
weighted by a cosine-tapered disk. **Turn** adds the selected angle per stamp.
Dragging interpolates stamp centers along the mouse path; overlapping Turn
stamps accumulate. Brush disks clip at the edge rather than wrapping.
Only theta is edited; tension and displacement then respond through the
unchanged rules when growth resumes.

The geometry-off lane starts with zero displacement and keeps kappa, shell gain
and curvature strength zero throughout. This is an explicit control lane rather
than a mid-run toggle carrying hidden displacement from the full recipe.
Because the lanes diverge, identical Set prescriptions need not produce
identical numerical angle changes away from the brush center.

## Export and replay

Each bundle contains:

- `pattern.png`: paired view using the selected field and fixed rendering scale.
- `recipe.json`: seed, grid, update count, complete parameters, timestamped brush
  stamps, view, source fingerprints and numpy version.
- `fields.npz`: both complete field states, stored in float64.
- `README.txt`: replay command.

Replay an exported recipe from the repository root:

```powershell
.venv\Scripts\python.exe -B -m src.genesis_sandbox --replay "path\to\recipe.json"
```

Replay recomputes the history before opening paused. It requires matching
dynamics source fingerprints and preset parameters; a saved field snapshot
remains available separately if source versions change. Exact replay was
verified in this environment; floating arithmetic across different numerical
environments is not guaranteed bitwise identical. Long sessions have a replay
cost proportional to their update count. Export bundles are never overwritten.

## Implementation and verification

New code: `src/genesis_sandbox/` and `launch_sandbox.ps1`.
The model calls `src/genesis_gallery/legacy.py` directly. The existing
original-function parity tests remain in place. No source was moved or replaced.
The fallback font comes from matplotlib's installed font files when system
fonts are unavailable in a sandboxed/offscreen Windows session.

All **48 tests** pass, including seven new tests covering local edits, angular
seams, exact paired-state replay/export, source checks, native play/pause/step,
queue cancellation, seed reset, mouse coordinate mapping and drag interpolation.

A native-widget smoke demonstration grew seed 1 at N64 to update 1000, applied
31 brush stamps through mouse events, continued to update 1400, exported the
view and replayed every field exactly. Its 1000-update growth took about 8.3
seconds on this machine during verification; this is an observed timing, not
a performance guarantee. This sample demonstrates the interface, not a new
scientific or generative result.

The full workflow screenshots and mouse tests use Qt offscreen rendering.
Normal Windows-platform startup, creation of a native window and event-loop
exit were also verified separately.


- [Sandbox screenshot](../../../results/creative_sandbox_2026-11-01/sandbox.png).
- [Compression screenshot](../../../results/creative_sandbox_2026-11-01/compression.png).
- [QA record](../../../results/creative_sandbox_2026-11-01/qa.json).
- [Test log](../../../results/creative_sandbox_2026-11-01/test_log.txt).
- [Source and artifact manifest](../../../results/creative_sandbox_2026-11-01/manifest.json).

Closed baseline fingerprints and the previous gallery artifact hashes still
match. This implementation inherits that evidence; it does not reopen the old
audits or establish novel physics, self-renewal or Life-like behavior.

## What to decide next

### Reading an apparently static field

The user clarified that the sandbox is loved and needed as an exploratory tool,
while emergent behavior remains the primary objective. They report that the
UPDATE counter keeps increasing when the picture appears static, so updates
are executing. Appearance alone does not measure remaining state change.

A read-only check of the existing review archives at updates 7900–8000 finds
only 0.293%–0.879% of geometry-on cells changing angle by more than one degree.
Compression still changes, with RMS differences 0.0172–0.0359. Geometry-off
orientation changes in the original double-precision report are effectively
zero, and stored compression is unchanged. The image can therefore look still
while structural activity persists. These numbers describe the archived three
seeds, not a direct measurement of the user's running session. Saved snapshots
are float32; the tiny orientation residuals come from the original report.
See [the archive interpretation](../../../results/sandbox_stillness_2026-11-01/report.json).

For the broader programme, settling can represent stabilization, but it does
not by itself demonstrate robust objects, memory or an ongoing generative
repertoire. A full-state fixed point would require theta, tension, displacement
and compression all to stop changing. A visually persistent patch can instead
be maintained by hidden activity. Continued autonomous renewal remains a
separate capability, not something inferred from running the update loop.

### Project objective

The user subsequently rejected the appearance and clarified that pretty images
are not a sufficient objective. The assistant's texture-making recommendation
was a scope error. This tool can inspect dynamics, but it does not establish a
worthwhile or novel generative system. The current question is what distinctive
behavior the rules enable beyond simpler controls; see [[Current Direction]].
Further UI polish, rules or comparison campaigns are not commissioned by the
tool's completion.
