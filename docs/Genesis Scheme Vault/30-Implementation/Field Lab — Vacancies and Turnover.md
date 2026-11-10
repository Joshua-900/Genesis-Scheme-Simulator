---
Area: Implementation
datetime_stamp: 2026-11-01T00:00:00-05:00
status: complete
confidence: vetted
tags:
  - sandbox
  - creative-tool
  - vacancies
  - stochastic-switching
links:
  - "[[Implementation Index]]"
  - "[[Current Direction]]"
  - "[[Genesis Creative Sandbox]]"
summary: Creative sandbox with luminous orientation glyphs, actual missing nodes, fresh arrivals, controlled random switching, zoom and reproducible export; the Genesis research programme is shelved.
canonical: false
---

# Field Lab — Vacancies and Turnover

The user has shelved the Genesis research programme and redirected work toward
a visually engaging experimental sandbox. This feature is a creative variant;
it is not a restart of the higher-order-object experiments. Historical models,
theory records, findings and evidence are preserved.

## Try it

Run `.\launch_sandbox.ps1`. The new session opens as **Field Lab** with luminous
dashes and a centered 2× detail view. **Full field**, 2× and 4× are available at
the top; **Compare geometry** reveals the second matched lane. Zoom and style
change presentation, not simulation state.

Open **Drop / add**, then:

- **Drop one / Add one:** remove a random visible dash or populate a visible hole.
  These buttons work while growth continues.
- **Drop 5% / Refill holes:** create a larger disturbance or fill all vacancies.
- **Flicker + Play:** set 0.2% departure and 0.6% return probability per update,
  then run. Stop random switching to watch the remaining field evolve on its own.
- Adjust either probability directly. The panel shows the expected long-run
  occupied fraction.

The Paint tab also offers **Erase dashes** and **Add fresh dashes**, alongside
the angle brushes. Painting pauses growth. Drop/add brushes use the displayed
radius and clip at the edges. Single manual drop/add buttons choose within the
current centered view; random turnover applies to the whole grid.

## The random process

Each site has an occupancy m_i∈{0,1}. With constant per-update probabilities:

\[
\Pr(m_i(t+1)=0\mid m_i(t)=1)=p_{out},\qquad
\Pr(m_i(t+1)=1\mid m_i(t)=0)=p_{in}.
\]

For occupied fraction f:

\[
\mathbb E[f_{t+1}\mid f_t]=f_t(1-p_{out})+(1-f_t)p_{in},\qquad
f_*={p_{in}\over p_{out}+p_{in}}.
\]

For ordinary nonzero settings in the controls, the expected population approaches
f*. Both probabilities zero means no automatic switching. Multiplying both
probabilities by the same factor preserves the stationary fraction while
changing the switching speed. The controls use probabilities per **model update**,
not per rendered frame or physical second. The UI allows 0–5% for each.

The preset gives f*=75%. In the recorded seed 7 demo, 600 switching updates after
an initial 400 occupied updates left 3136/4096 sites present (76.6%), with 3843
departures and 2883 arrivals. These fluctuate around an expectation, not an exact
population target. Continued switching is externally specified stochastic drive.

## A real vacancy

An absent dash has no angular, tension, displacement or compression state.
Every bond and dipole edge touching it is omitted; triads requiring it are
omitted entirely. Geometry stencils use zero difference across missing edges
(a no-flux convention). Former neighbors do not become connected across a hole.
Inactive payload values are ignored and cleared by the vacancy kernel.

A new dash receives a fresh uniformly random angle and zero retained fields.
Departures and returns are sampled simultaneously from the **previous** mask;
a dash cannot disappear and return in the same update. Both comparison lanes
receive identical vacancies and arrival angles. Geometry then evolves according
to each lane's own rules.

`src/genesis_sandbox/vacancies.py` is a separate experimental kernel. With every
site occupied, it calls the unchanged historical recipe exactly. The preserved
`model.py` remains the classic sandbox; `lab_model.py` adds this variant. V1/V2
engine sources and research code are unchanged.

## Rendering and export

The new procedural renderer shows actual angle as dash direction and cyclic
color, with a brighter tip to distinguish polarity. Angular activity increases
brightness. Pink rings mark recent departures; pale flashes mark arrivals.
These transient highlights are display cues, not interaction fields. Empty
cells contain no hidden dash. Compression/activity views and the classic
heatmap remain available.

Export records the visible style, centered zoom and single/paired view. The
bundle contains PNG, full field/mask snapshot and a version2 recipe. Configuration
changes and realized manual edits are timestamped; automatic switching replays
from its independent seeded generator. Generator state is retained for continued
use after replay. Old version1 recipes still use the preserved classic path.

Replay with `.venv\Scripts\python.exe -B -m src.genesis_sandbox --replay
"path\to\recipe.json"`. Source fingerprints are checked. Full-state replay of
the N64 demo was exact in this environment. Arbitrary cross-version numerical
identity is not promised; saved snapshots remain available independently.

## Verification and artifacts

All **71 tests** pass. New tests cover real disconnection across vacancy barriers,
ignored ghost payload, cleared state/fresh arrivals, simultaneous switching,
the occupancy formula, exact replay/continued evolution, classic compatibility,
glyph absence, native controls and zoomed brush coordinates/export.

- [Preview](../../../results/vacancy_lab_2026-11-01/flicker.gif).
- [Field Lab screenshot](../../../results/vacancy_lab_2026-11-01/field_lab.png).
- [4× detail](../../../results/vacancy_lab_2026-11-01/detail.png).
- [QA record](../../../results/vacancy_lab_2026-11-01/qa.json).
- [Tests](../../../results/vacancy_lab_2026-11-01/test_log.txt).
- [Manifest](../../../results/vacancy_lab_2026-11-01/manifest.json).

The archived research handoff is retained with these artifacts. Future work is
creative sandbox experimentation unless the user explicitly reopens research.


## Live 3D torus view (2026-11-01)

New Lab sessions open with a shaded, luminous torus. Right-drag to orbit, wheel
to zoom, left-drag to paint/erase/restore on the visible surface. The toolbar
switches to flat dashes or the classic heatmap. Reset camera returns to the
initial view; Show coordinate seams reveals the two parameter boundaries.
Both comparison panels use the same camera. Camera movement never advances
simulation ticks or consumes random numbers. Painting still pauses growth.

The surface coordinates are the original grid coordinates, periodically mapped:

$$u=2π(x+\frac12)/N,\quad v=2π(y+\frac12)/N,$$

$$\mathbf r(u,v)=((R+r\cos v)\cos u,\ r\sin v,\ (R+r\cos v)\sin u).$$

Here R=2.15 and r=0.86 are presentation units. The angles define glyph direction
in the surface parameter chart. They are not recomputed using distances in the
3D embedding. Shading and display curvature introduce no new forces or degrees
of freedom. Empty sites have no glyph; a dim reference surface remains to show
the torus shape. That surface is a visual guide, not a simulated membrane.

**Boundary caveat:** alignment and geometry wrap in both directions, while the
historical dipole/triad terms stop at grid edges. Thus the recipe is not uniformly
periodic across every interaction. This view preserves that implementation and
makes its coordinate seams inspectable. A fully periodic recipe would be a
separate dynamics change.

`torus_gl.py` supplies the native VisPy GPU renderer. `torus.py` supplies cached
software ray tracing for exports, offscreen sessions, and graphics failure.
Software interaction uses a smaller preview followed by a sharper paused view.
PNG exports use the reference renderer; GPU and software lighting/glow are
visually similar but not pixel-identical. Camera and seam settings are recorded
in recipes and restored on replay, along with the unchanged field dynamics.

The complete suite now has **76 passing tests**. Added checks cover periodic
surface geometry, UV picking, background/hole rejection, display isolation from
model state/RNG, exact dynamics replay after torus export, orbit, zoom and surface
erasing. Native Windows GPU rendering, camera interaction and surface erasing
were also exercised separately. Evidence:

- [Torus window](../../../results/torus_view_2026-11-01/window.png).
- [Orbit preview](../../../results/torus_view_2026-11-01/orbit.gif) — camera motion
  around a paused field, not an animation of model evolution.
- [Native QA](../../../results/torus_view_2026-11-01/qa.json).
- [Native QA script](../../../results/torus_view_2026-11-01/verify_native.py).
- [Test log](../../../results/torus_view_2026-11-01/test_log.txt).
