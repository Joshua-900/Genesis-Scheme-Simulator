# GenesisScheme

A simulation playground for studying emergent orientation-field dynamics
(alignment, geometric compression, vortex formation, locking) and
spontaneous-symmetry-breaking-like phenomena. The current engine is
`src/genesis_grid/`; everything else is either built on it, a precursor
to it, or unrelated visualization.

## Quick start

```bash
python launcher.py
# then open http://localhost:5000
```

The launcher discovers every runnable `.py` in the repo root, groups them
by category, and lets you start/stop them with live console output. It
also reads and writes the metadata files described below.

For headless measurement runs (no GUI):

```bash
python genesis_measure.py --multi-seed --seeds 20 --N 200
python genesis_measure.py --sweep-kappa --kappa-max 0.1 --kappa-steps 20
python genesis_measure.py --compare-geometry --seeds 5
```

## Repo map

```
GenesisScheme/
├── launcher.py                 # localhost:5000 control panel (start here)
├── genesis_measure.py          # headless measurement harness
│
├── src/
│   ├── genesis_grid/           # CURRENT engine — orientation field, modular rules
│   └── genesis_scheme/         # LEGACY engines (v0/v1) + the new pluggable protocol
│
├── scripts_metadata.json       # status + category for every root-level .py
├── modules_metadata.json       # status for every module under src/
│
├── docs/
│   ├── status_taxonomy.md      # what active/reference/exploratory/etc. mean
│   ├── 2026-04-11-session-notes.md
│   └── genesis_scheme_theory_report.md
│
├── findings/                   # promoted from notes: real experimental results
│   └── 2026-04-12_ssb_lattice_bias.md
│
├── diagrams/                   # .mmd source for architecture, timeline, dataflow
├── architecture.md             # rendered version of the architecture diagrams
│
├── results/                    # output of genesis_measure.py (JSON + CSV)
│
└── animate_*.py, genesis_*.py, coupling_*.py, ...
                                # 25+ top-level scripts — visualizations,
                                # iterations, demos. Status labels in
                                # scripts_metadata.json say which to trust.
```

## Status system

Every script and module is tagged with a `status` field in the metadata
files. The vocabulary, defined in `docs/status_taxonomy.md`:

- **`active`** — current work; safe to edit
- **`reference`** — stable, kept for teaching/regression value
- **`exploratory`** — sketch or A/B variant, not relied upon
- **`superseded`** — was current, now replaced (a successor exists)
- **`broken`** — known not to run or produce wrong output

The launcher hides `superseded` and `broken` by default. Use the "Show:"
filter in the header to reveal them. Each card shows its status as a
colored pill so you can scan the list and see what's load-bearing vs.
historical at a glance.

Edit a script's status by clicking the card → Details tab → Status
dropdown → Save.

`status` is the lifecycle axis. `quality` is a separate, reserved axis
for confidence/correctness — most entries leave it empty today.

## Findings

Real experimental results (negative or positive) live in `findings/` as
dated markdown files, not buried in `notes` fields. Each finding includes
a one-line headline, the numbers behind it, the cause, and what
experiment to run next. The metadata entry for the relevant script
links to its findings via a `findings` array.

Example: `findings/2026-04-12_ssb_lattice_bias.md` documents why the
SSB test in `genesis_measure.py --multi-seed` is measuring square-lattice
anisotropy rather than spontaneous symmetry breaking, and proposes
hexagonal / Voronoi / central-difference variants as the next experiments.

## Engine generations

Per `diagrams/timeline.mmd`:

| When | Module | Status |
|---|---|---|
| Nov 30 2025 | `src/genesis_scheme/algebra.py` (1D scalar) | superseded |
| Dec 2 2025  | engine v0 — single-field 2D grid | superseded |
| Dec 2 2025  | engine v1 — Gray-Scott (U, V) two-field | superseded |
| Dec 2025 –  | **`src/genesis_grid/` — modular rule-based** | **current** |
| Apr 2026    | Pluggable engine protocol + registry | current |

The current engine is a θ orientation field on an N×N grid with a
pipeline of pluggable physics rules (alignment, compression, curvature,
locking, plus several optional ones). See `diagrams/genesis_grid_engine.mmd`
for the detailed structure.

## Where to look first

- **"What's the current way to run an experiment?"** → `genesis_measure.py`
- **"What rules does the engine use?"** → `src/genesis_grid/` (the `rules_*.py` files)
- **"Which top-level scripts are still relevant?"** → filter the launcher to "Active only" or "Default"
- **"What have we learned?"** → `findings/`
- **"How does the whole thing fit together?"** → `architecture.md` and the diagrams in `diagrams/`

## Known issues

- `src/genesis_scheme/__init__.py` is **broken**: it eager-imports
  `.engine.adapter` and `.engine_v1.adapter`, neither of which exists in
  the repo. Scripts using the legacy package import its leaf modules
  directly to avoid triggering this. Tagged `broken` in
  `modules_metadata.json` pending a decision: restore the missing
  subpackages or strip the eager imports.
- `src/genesis_grid/rules_curvature.py` has a dead stub function at the
  top (references `state.grid`, which doesn't exist) that's overridden
  by the working definition below it. Worth deleting on next cleanup.
- The SSB measurement in `genesis_measure.py --multi-seed` is biased by
  the square lattice. See `findings/2026-04-12_ssb_lattice_bias.md`.
