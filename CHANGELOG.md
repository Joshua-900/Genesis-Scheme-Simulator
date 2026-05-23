# Changelog

All notable changes to GenesisScheme.

Format loosely follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Dates are YYYY-MM-DD.

## [Unreleased]

## 2026-05-23 — Status taxonomy & repo organization

### Added

- **5-value status taxonomy** for every script and module:
  `active | reference | exploratory | superseded | broken`. Defined in
  `docs/status_taxonomy.md`.
- **`modules_metadata.json`** — new file covering every module under
  `src/genesis_grid/` and `src/genesis_scheme/`. Schema mirrors
  `scripts_metadata.json`.
- **`findings/`** directory with the first entry,
  `2026-04-12_ssb_lattice_bias.md`, documenting the square-lattice
  anisotropy in the multi-seed SSB measurement (promoted out of a
  `notes` field on `genesis_measure.py`).
- **`README.md`** at the repo root — orientation, quick start, repo
  map, status system, engine generations. Replaces the old
  `readme.txt`.
- **`CHANGELOG.md`** (this file).

### Changed

- **`scripts_metadata.json`**
    - Schema bumped to version 2; added a `_taxonomy` header block
      describing the status values.
    - Every existing entry got a `status` field (mostly `exploratory`
      for December 2025 sketches, `superseded` for v0/v1 scripts,
      `reference` for first-engine-based and utility scripts).
    - Added entries for the 7 root-level scripts that previously had
      no metadata (`genesis_grid_anneal.py`,
      `genesis_grid_emergence_contours.py`, `genesis_grid_large.py`,
      `genesis_grid_minimal.py`, `genesis_grid_minimal_triad.py`,
      `genesis_grid_ssb.py`, `genesis_grid_vortices.py`).
    - The long SSB note on `genesis_measure.py` was replaced with a
      short pointer to `findings/2026-04-12_ssb_lattice_bias.md` and
      a `findings` array linking to it.
- **`launcher.py`**
    - Header gained a "Show:" filter dropdown
      (default / active-only / all / legacy-only). Default hides
      `superseded` and `broken`.
    - Each script card now displays a colored status pill
      (5 distinct colors keyed to the taxonomy).
    - Details panel gained a `Status` dropdown and a list of linked
      findings files.
    - Backend `_set_script_meta` now merges incoming meta into the
      existing entry instead of overwriting, so fields the UI doesn't
      send (e.g. `findings`) are preserved across saves.
    - Added `_empty_meta()` helper so default shapes for files
      without entries include the new `status` and `findings` fields.

### Known issues identified (not yet fixed)

- `src/genesis_scheme/__init__.py` references missing subpackages
  `.engine` and `.engine_v1`; eager imports would crash. Marked
  `broken` in `modules_metadata.json`. Decision pending: restore
  subpackages or strip the eager registration.
- `src/genesis_grid/rules_curvature.py` has a dead stub at the top
  (returns `xp.zeros_like(state.grid)` — no such attribute) that's
  shadowed by the real definition below. Cosmetic but should be
  deleted.
- `genesis_measure.py --multi-seed` measures square-lattice
  anisotropy, not spontaneous symmetry breaking. Tracked in
  `findings/2026-04-12_ssb_lattice_bias.md`. Cheapest next experiment:
  switch `rules_compression.py` from forward to central differences.

## Earlier history

Engine evolution prior to this changelog is captured in
`diagrams/timeline.mmd`:

- 2025-11-30 — `algebra.py` (1D scalar F/A duality, proof of concept)
- 2025-12-02 — engine v0 (single-field 2D grid, diffusion + growth)
- 2025-12-02 — engine v1 (Gray-Scott U,V two-field, tension feedback)
- 2025-12-02 – 2025-12-10 — `genesis_grid` (modular rule-based,
  orientation field, **current preferred engine**)
- 2026-04 — pluggable engine protocol + registry, launcher metadata
