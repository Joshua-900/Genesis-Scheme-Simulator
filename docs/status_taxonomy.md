# Status Taxonomy

This document defines the `status` field used in `scripts_metadata.json` and the
forthcoming `modules_metadata.json`. The goal is to tell, at a glance, which
files in the repo are part of the current work and which are historical, in
progress, or known-broken.

`status` is a **lifecycle label** — where this file sits in the project. It is
deliberately separate from `quality`, which is reserved for a future judgment
about correctness or confidence in results.

## Values

The five values below are mutually exclusive. Pick exactly one per file.

### `active`
Currently in development or actively run for results. New work happens here.
Touch this code freely. Anything imported by the active pipeline counts.

*Examples:* `genesis_measure.py`, `launcher.py`, `src/genesis_grid/core.py`.

### `reference`
Working, kept around because it documents something real or is useful as a
teaching example. Not under active development, but you would point a newcomer
at it. If you change it, do so deliberately.

*Examples:* `genesis_grid_emergence.py` (the first engine-based script),
`cupy-test.py` (a GPU sanity check), `vispy_heatmap_example.py`.

### `exploratory`
A sketch, probe, or A/B variant. May work; not relied upon. Could become
`active` if it pays off, or be demoted to `superseded` if a sibling wins. Most
of the December 2025 visualization sketches live here.

*Examples:* the `genesis_quiver_*` family, the `genesis_fields_pretty_*`
iterations, `rules_triads_relative.py`.

### `superseded`
Was active once. Has been replaced by something better, and that successor
exists in the repo today. Kept for history; not where new work should go. If
you find yourself editing a `superseded` file, ask whether you should be
editing the successor instead.

*Examples:* `src/genesis_scheme/algebra.py` (replaced by `src/genesis_grid/`),
the `animate_*` scripts that target the v0/v1 engines.

### `broken`
Known not to run, or runs but produces wrong or meaningless output. Either fix
or delete; don't leave indefinitely.

*Examples:* none in the repo at the moment, but the dead stub at the top of
`src/genesis_grid/rules_curvature.py` would qualify the file if it weren't
overridden by the working definition below it.

## Choosing between adjacent labels

The two distinctions that matter most:

**`reference` vs `exploratory`.** Different questions answer this. `reference`
answers "is this stable enough to point someone at?" — yes implies `reference`.
`exploratory` answers "would I trust the result?" — no implies `exploratory`.
A polished demo of a stable behavior is `reference`. A working but uncalibrated
probe is `exploratory`.

**`exploratory` vs `superseded`.** `exploratory` means "this hasn't been
decided about yet." `superseded` means "this lost, and the winner is X." If
you can name the successor, use `superseded`. If you can't, use `exploratory`.

## What the launcher does with this

The Flask launcher (`launcher.py`) reads `scripts_metadata.json` and groups by
`category`. After the UI update, it will also surface `status` as a colored
badge on each script card and (optionally) filter `superseded` and `broken`
out of the default view.

`active` and `reference` items always show. `exploratory` items show by
default but can be hidden. `superseded` and `broken` items are hidden by
default and revealed only with an explicit toggle.

## Scope

The taxonomy applies to:

- All `.py` files in the repo root (covered in `scripts_metadata.json`)
- Modules under `src/genesis_grid/` and `src/genesis_scheme/` (will be covered
  in `modules_metadata.json`)

It does not apply to: `.venv/`, `__pycache__/`, test fixtures, or generated
output under `results/`.

## Findings

Some metadata entries carry a `findings` field — a list of paths to markdown
files under `findings/` that document substantive results produced by the
script. This is separate from `notes`, which is for short metadata-grade
context. Anything longer than a paragraph or that draws a conclusion belongs
in a findings file, not a `notes` field.

Findings file naming: `findings/YYYY-MM-DD_short_slug.md`. The date is when
the result was observed, not when the file was written. Each file should
include a one-line headline, the numbers that produced the conclusion, the
cause, and what to do next.

## Schema version

`scripts_metadata.json` carries a `_taxonomy` block with `schema_version: 2`.
The current schema introduced the `status` and `findings` fields. Any future
field additions should bump that number and document the migration here.
