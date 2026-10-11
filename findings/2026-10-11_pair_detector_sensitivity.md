# 2026-10-11 - Long-lived v1 pair population is robust to first detector controls

**Source:** `genesis_object_sensitivity.py --seeds 5 --frames 10000`
**Status:** confirmed baseline result
**Owner:** Joshua

## Headline

The full candidate population is sensitive to the observation cadence, but the
long-lived tail is robust across all nine tested detector configurations. This
supports treating vortex-antivortex pairs as a reproducible population of
long-lived relational candidates in the current v1 model.

It does not establish one-to-one object identity across configurations,
autonomy, or a new interaction law.

## Controlled Variables

The v1 dynamics, grid size (100 x 100), model parameters, frames per seed
(10,000), and seeds (1-5) were fixed. Only detector configuration changed:

- sample interval: 10, 25, or 50 frames;
- maximum pair radius: 32, 64, or 96 cells.

Each condition used the same elapsed-time persistence criterion (age >= 100
frames). The required number of observations was adjusted by sampling interval
so cadence did not redefine persistence.

## Results

| Sample interval | Pair radius | Observed | Persistent | Persistent fraction | Age >= 1,000 | Age >= 5,000 |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 10 | 32 | 9,870 | 1,567 | 15.9% | 306 | 88 |
| 10 | 64 | 10,026 | 1,607 | 16.0% | 322 | 90 |
| 10 | 96 | 10,125 | 1,629 | 16.1% | 329 | 90 |
| 25 | 32 | 5,144 | 1,380 | 26.8% | 302 | 88 |
| 25 | 64 | 5,242 | 1,417 | 27.0% | 318 | 90 |
| 25 | 96 | 5,303 | 1,437 | 27.1% | 325 | 90 |
| 50 | 32 | 2,464 | 1,123 | 45.6% | 300 | 91 |
| 50 | 64 | 2,528 | 1,158 | 45.8% | 317 | 93 |
| 50 | 96 | 2,568 | 1,178 | 45.9% | 324 | 93 |

## Interpretation

1. **Do not compare the raw candidate fraction across sample intervals.**
   Faster sampling captures more short-lived pair assignments, expanding the
   denominator. The 15.9%-45.9% range is therefore a detector-cadence effect,
   not evidence that the underlying dynamics changed.
2. **The long-lived tail is stable.** Across all nine configurations, the
   number surviving at least 1,000 frames stays between 300 and 329; the
   number surviving at least 5,000 frames stays between 88 and 93. This is
   much less sensitive than the raw population.
3. **Pair radius has a small effect in the tested range.** Increasing radius
   from 32 to 96 changes the long-lived count only modestly within each
   sampling interval. The detector is not creating the long-lived population
   solely by allowing remote matches.
4. **The justified claim has strengthened.** In v1, there is a robust
   population of long-lived, measurable vortex-antivortex relations under
   these detector controls.

## Remaining Limits

- Matching remains greedy nearest-opposite-charge pairing. The same physical
  relation has not been identified one-to-one across configurations.
- No perturbation test has assessed whether coarse pair attributes predict
  survival or response.
- Square-lattice bias remains a model limitation; see
  `findings/2026-04-12_ssb_lattice_bias.md`.
- This is evidence about v1 only. It neither validates Genesis metaphysics
  nor supplies a v2 model.

## Consequence

The v1 baseline is now sufficiently characterized for the project to begin
v2 bridge design. Continuity-aware pairing and perturbation testing remain
valuable v1 validation work and should be reused as common measurement tools
for a future v2 comparison.

## Related Files

- `genesis_object_sensitivity.py`
- `genesis_object_census.py`
- `results/pair_census_sensitivity.json`
- `findings/2026-10-11_pair_census_baseline.md`
