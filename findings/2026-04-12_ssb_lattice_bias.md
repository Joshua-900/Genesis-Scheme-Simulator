# 2026-04-12 — SSB result is square-lattice bias, not spontaneous symmetry breaking

**Source:** `genesis_measure.py --multi-seed --seeds 20`
**Status:** confirmed negative result
**Owner:** Joshua

## Headline

The multi-seed SSB test does **not** demonstrate spontaneous symmetry breaking.
Across 20 runs with independent seeds, the final order-parameter angle θ
clusters in a narrow band (≈ 1.02–1.96 rad, std 0.218 on a range of 0–2π).
The system orders (|m| ≈ 0.32), but it picks the same direction every time —
the diagonal of the square grid.

What we were celebrating as SSB is **explicit symmetry breaking by the lattice
topology**, not spontaneous breaking by the field dynamics.

## Numbers

| Metric | Value |
|---|---|
| Seeds | 20 |
| Angle range observed | 1.02 – 1.96 rad |
| Angle std | 0.218 rad |
| Full angle range possible | 0 – 6.28 rad (2π) |
| Typical \|m\| | ≈ 0.32 |
| Expected std under genuine SSB | ≈ π/√3 ≈ 1.81 (uniform on [0, 2π)) |

The observed std is roughly an order of magnitude below what a genuinely
isotropic system would produce.

## Cause

Two interacting sources of anisotropy:

1. **Square-lattice 4-neighbor coupling.** The alignment rule uses
   N/S/E/W rolls. A square grid has only fourfold rotational symmetry, not
   continuous rotational symmetry. The lattice diagonal (π/4) is a preferred
   direction.

2. **Forward-difference derivatives in `rules_compression.py`.** The
   compression rule computes spatial derivatives via `roll(-1) - self`, which
   is asymmetric and contributes additional directional bias along the same
   diagonal.

Result: the system has a preferred angle near θ ≈ π/4 baked into the
discretization, and the dynamics relax onto it from any initial condition.

## Implications

- The "SSB" demonstration in `genesis_measure.py`'s multi-seed mode is not
  evidence of emergent symmetry breaking. It is evidence of correct ordering
  in a system whose symmetry was already broken by construction.
- Other downstream claims that depend on SSB (vortex pair formation as
  defect dynamics in an isotropic medium, for instance) should be revisited
  with this lens.
- The result itself is honest and useful — it tells us where the dynamics
  end and the discretization begins.

## Next experiments

In order of cost vs. signal:

1. **Switch to central differences in `rules_compression.py`.** Cheapest
   change. Replace `roll(-1) - self` with `0.5 * (roll(-1) - roll(+1))`.
   If the angle bias shrinks substantially, the forward-difference asymmetry
   was the dominant source. If it doesn't, the four-neighbor lattice itself
   is the source.

2. **Hexagonal lattice with 6-neighbor coupling.** Higher rotational
   symmetry (sixfold rather than fourfold). If the bias disappears under
   hex coupling, we've isolated the lattice contribution. Larger change —
   touches the grid topology and every rule that uses `xp.roll`.

3. **Voronoi or Delaunay random mesh.** No preferred directions at all.
   Most expensive change (would require rewriting the neighborhood
   primitives from index-based rolls to graph-based gathers) but is the
   only setup that can produce genuinely isotropic SSB.

## Related files

- `genesis_measure.py` — the harness that produced this result
- `src/genesis_grid/rules_alignment.py` — 4-neighbor square coupling
- `src/genesis_grid/rules_compression.py` — forward-difference derivatives
- `results/multi_seed_summary_N*.csv` — raw data
