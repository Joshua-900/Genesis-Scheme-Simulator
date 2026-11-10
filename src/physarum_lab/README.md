# Physarum Studio

A separate generative-art simulator. Existing Genesis engines, recipes and
research evidence are preserved. This is a Physarum-inspired agent model with
optional mathematical guidance, not a biological or fluid-physics solver.

From the repository root:

```powershell
.\launch_physarum.ps1
.\launch_physarum.ps1 -Seed 17 -Preset Estuary
```

No new dependencies are required beyond the existing project environment.
The launcher uses 90,000 agents on a 512-square field. For a denser run:

```powershell
.venv\Scripts\python.exe -B -m src.physarum_lab --size 640 --agents 150000
```

The model's programmatic default remains 640/150,000. CLI dimensions are
explicitly recorded in every saved state. Use smaller values for faster
interaction; higher resolution increases both computation and visual detail.

## Explore

- **Silk:** finer networks with gentle currents.
- **Estuary:** broader, flowing plumes and longer trail memory.
- **Filigree:** trail-following without the authored current field.
- **Gather / Release:** smoothly change wave guidance over 100 simulation ticks.
  The guiding pattern attracts agents toward its nodal lines. Gathering also
  reduces current strength, so the environmental forces cooperate.
- **Wave modes:** change the guiding geometry. **Reveal guiding pattern** shows
  an optional overlay; that overlay does not change the simulation.
- **Current strength:** vary an analytic, time-varying curl field independently.
- **Drag:** locally stir agents' headings. Stirring works while paused and
  takes visible effect as the agents subsequently move.
- **Wheel / right-drag:** zoom / pan. **Fit whole field** resets the view.
- **Palette / exposure:** change presentation without changing agent state.
- **Save artwork + state:** export a 1600px full-field PNG, numerical arrays,
  rules, tick, transition progress and random-generator state. The artwork is
  always the whole field, independent of viewport zoom and guide overlay.
- **Open saved state:** restore a bundle, paused, ready for exact continuation
  under the same numerical environment and implementation.

Desktop startup warms a new population for 180 ticks. Reseeding starts at tick
zero, so you can watch its formation. Pause and Step allow deliberate inspection.

Headless generation uses the same simulation and reference renderer:

```powershell
.venv\Scripts\python.exe -B -m src.physarum_lab --headless --preset Silk --ticks 400
.venv\Scripts\python.exe -B -m src.physarum_lab --headless --guidance 1 --ticks 600
.venv\Scripts\python.exe -B -m src.physarum_lab --load "path\to\bundle.json"
```

`--ticks` on a loaded state means additional ticks; otherwise it means warmup.
Snapshot archives use NumPy arrays with pickle disabled and a checksum. The
bundle records source hashes and the NumPy version for provenance. The format
is a saved state rather than a replayable history of mouse gestures. The loader
does not enforce matching source hashes; exact continuation across different
implementations or numerical versions is not guaranteed.

## Architecture

The folder structure follows Clean Architecture's inward dependency direction,
without frameworks, repositories or interfaces for things that do not vary:

```text
physarum_lab/
  domain/model.py          Seeded agents and trail dynamics
  domain/fields.py         Independent wave/current formulas
  application/session.py   Playback policy and tick-based guidance transitions
  adapters/render.py       Headless reference rendering and appearance settings
  adapters/density.frag    GPU presentation shader
  adapters/gpu.py          VisPy display implementation
  adapters/desktop.py      Qt controls, camera and interaction
  adapters/storage.py      Versioned PNG/JSON/NPZ bundles
  __main__.py              Composition and CLI
```

The domain uses NumPy/SciPy for numerical computation and has no files, Qt,
OpenGL, or renderer imports. The application imports only the domain. Adapters
depend inward. The CLI composes them and imports Qt only for desktop use.

`Simulation.step`, `disturb`, `set_modes`, `snapshot`, and `restore` form the main
simulation interface. Frozen `Rules` validate configuration. `Session.advance`
is the shared interface for desktop and headless progression. Rendering only
reads state. Both renderers use the same palettes and exposure curve; bloom and
resampling differ slightly, so exported pixels need not equal a framebuffer.

Simulation currently runs on the CPU; the native display shader runs on the
GPU. Shared tone mapping preserves the trail density range; a float16 GPU texture
carries display intensity and the signed guide field. Software display
is automatic in offscreen sessions or on graphics failure. Performance depends
on population, resolution and hardware; tick duration never depends on render
frame timing. Model evolution is deterministic for a fixed sequence of inputs
within the same numerical environment.

## Model and extension points

Agents sense forward and sideways, turn toward higher scores, move and deposit
trail. Trail diffuses with periodic boundaries and evaporates. A local crowding
cost discourages excessive concentration. At each tick the sensor score is:

```text
S = (1 - 0.5*g) * log(1 + trail)
    - 18*g * wave**2
    - crowding * log(1 + blurred_density)
```

Here `g` is current guidance strength. The wave is a designed cosine-mode
interference pattern, not a solution for a particular vibrating physical plate.
The current is the analytic curl of a multiscale stream function; it is an
authored environmental influence, not an emergent fluid velocity. New wave or
current formulas belong in the domain and should retain explicit parameters and
periodic conventions. No dynamic evaluation of arbitrary Python expressions is
used. New appearance treatments belong in rendering, without changing rules.

The model can produce attractive patterns and controlled reorganizations; this
does not establish self-reproduction, open-ended evolution or the Genesis Ladder.

## Validation

```powershell
$env:QT_QPA_PLATFORM='offscreen'
$env:GENESIS_USE_CUPY='False'
$env:OPENBLAS_NUM_THREADS='1'
.venv\Scripts\python.exe -B -m unittest discover -s tests
```

Tests cover seeded/chunked evolution, particle count and trail-mass accounting,
periodic positions/current, nodal concentration, local stirring, display
isolation, resumable snapshots, guidance transitions and desktop controls.
Native GPU screenshots and timing are checked separately; see
`results/physarum_lab_2026-11-02/`.

Model inspiration: Jeff Jones's Physarum transport-network work
(https://arxiv.org/abs/1503.06579) and Sage Jenson's description of particle/grid
feedback (https://n-e-r-v-o-u-s.com/blog/?p=9137). This implementation was written
for this project; it is not copied from either implementation.


## Live formula editor

Click **Formula editor…** below the wave-mode selector. Type a scalar field or
choose **Vector current (u, v)** and enter two velocity expressions. **Preview
draft** evaluates a sample field without changing agents, ticks or RNG. **Apply
live** validates against the actual field and changes its target strength;
transitions still blend over simulation ticks. Press Play if paused.

Examples:

```text
sin(4*pi*x + t) * cos(3*pi*y - t)
sin(12*sqrt(x*x + y*y) - 2*t)
x*x + y*y - (0.55 + 0.15*sin(t))^2
```

For a rotating current, use `u=-y`, `v=x`. Weaving currents can use
`u=sin(3*pi*y+t)`, `v=cos(3*pi*x-t)`. Example selection edits the draft; Apply
is always explicit. **Return to wave modes** restores the built-in guidance.
Reseeding retains the active custom formula. New bundles record formulas,
response mode, scale and time speed; loading restores them. Older version-one
bundles remain readable.

Coordinates `x,y` range from -1 to 1 across the domain, with y pointing upward.
Spatial scale multiplies both coordinates. `t = tick/60 * time_speed` is model
time, independent of wall-clock or display FPS. Zero time speed freezes the
formula's time argument. All agents and trails still use periodic boundaries;
an arbitrary formula need not join smoothly across their seams.

Response modes:

- **Zero contours:** adds `-18*g*min(F^2,16)` to the score.
- **Peaks:** adds `6*g*clip(F,-4,4)`.
- **Repel peaks:** adds `-6*g*clip(F,-4,4)`.
- **Vector current:** adds `3*g*clip(u,-4,4)` and `3*g*clip(v,-4,4)` pixels per
  tick to displacement. Built-in currents fade by `1-g` in this mode. No
  scalar attraction is added. Velocity is interpolated at each agent position from the validated
  cell-centered grid. These arbitrary currents need not conserve divergence.

Here g is the current blended field strength. Scalar responses retain the
existing `(1-.5*g)` trail weighting and the current attenuation `1-.9*g`.
Preview brightness shows scalar attraction, or vector speed with direction
arrows. The main guide overlay follows the selected response. Draft previews
are sampled at their labeled tick; time-dependent applied fields evolve live.

Supported functions: `sin cos tan tanh abs sqrt exp log atan atan2 min max hypot
floor ceil clip where`. Constants: `pi tau e`. Operators: arithmetic, `%`, powers
`^` / `**`, comparisons, and `and/or/not`. Function arguments are evaluated
eagerly, including both branches of `where`; use `sqrt(abs(x))`, for example,
when negative coordinates are possible.

The domain's `formulas.py` interprets a restricted AST directly. It never uses
`eval`, Python compilation, attribute access, indexing, imports or arbitrary
calls. Expressions are limited to 512 characters, 128 AST nodes, nesting depth
20, exponents of magnitude at most 16, and finite intermediate values no larger
than one million. Invalid drafts leave the active formula unchanged. A later
numerical singularity pauses before the invalid tick, preserving its RNG and
transition state. Errors are shown in the editor or main status message.

Formula parsing/field sampling live in the domain, editor/preview in adapters.
There is no new dependency. Snapshot format is now version two; the loader
continues to accept version one. Formula continuation, parser restrictions,
steering responses, numerical failure handling and editor controls are covered
by `tests/test_physarum_formulas.py`.
