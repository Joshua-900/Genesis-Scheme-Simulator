# 2026-10-11 - V1 pair census establishes persistent candidates, not validated objects

**Source:** `genesis_object_census.py --seeds 5 --frames 10000`
**Status:** preliminary baseline
**Owner:** Joshua

## Headline

The current Genesis v1 engine repeatedly produces tracked vortex-antivortex
pair candidates that satisfy a declared persistence threshold. This supports
the narrower claim that the v1 field contains repeatable, measurable
relational configurations. It does not yet establish autonomous higher-order
objects or a new interaction law.

## Configuration

| Setting | Value |
| --- | ---: |
| Grid | 100 x 100 |
| Frames per seed | 10,000 |
| Seeds | 1-5 |
| Sampling interval | 25 frames |
| Persistent-candidate threshold | age >= 100 frames and >= 4 observations |
| Alignment | 0.30 |
| Tension | 0.01 |
| Geometry coupling | 0.05 |
| Curvature | 0.04 |
| Lock strength | 0.96 |

## Results

| Metric | Value |
| --- | ---: |
| Observed pair candidates | 5,242 |
| Persistent candidates | 1,440 (27.5%) |
| Persistent candidates per seed | 251 - 341 |
| Persistent candidates with age >= 1,000 | 318 |
| Persistent candidates with age >= 5,000 | 90 |
| Median persistent-candidate age | 300 frames |
| 90th-percentile persistent-candidate age | 2,900 frames |
| Maximum observed age | 9,950 frames |

Persistent candidates had higher median line coherence (0.535) than all
observed candidates (0.473). Their median compression signal was effectively
zero, so this run does not support an interpretation of these pairs as
compression-bound structures.

## Interpretation

1. **A repeatable population exists.** Each seed produced roughly one
   thousand observed pair candidates and 251-341 threshold-passing candidates.
   This makes the pattern suitable for further measurement rather than a
   one-off visual impression.
2. **Some relations are genuinely long lived under this detector.** Ninety
   candidates remained tracked for at least half of a 10,000-frame run.
3. **The present result concerns topological relations, not generic objects.**
   The constituents are +1 and -1 defects detected from field winding; the
   pair itself is constructed by a greedy nearest-opposite-charge matcher.
4. **No autonomy has been shown.** The report describes persistence and
   attributes. It does not show that a pair's coarse state predicts its future
   better than the underlying field, nor that it survives perturbation.

## Limits That Matter

- Pair membership can change because the current tracker greedily selects the
  nearest opposite-charge defect. A long-lived pair may reflect stable nearest
  neighbors, but the current run does not test this against alternative
  matching rules.
- `annihilation_candidate` is a repeated tracker heuristic, not a verified
  physical annihilation count. It fires many times while a pair is missed and
  must not be interpreted as 38,527 interaction events.
- The defect tracker uses a five-frame missed-detection allowance while the
  census samples every 25 frames. This makes identity continuity sensitive to
  the sampling schedule when a defect is not matched.
- The known square-lattice bias remains relevant. See
  `findings/2026-04-12_ssb_lattice_bias.md`.

## Next Experiment

Run an identity-sensitivity control on the same seeds: vary sample interval,
pairing radius, and matching rule or hysteresis while holding the v1 dynamics
fixed. Compare candidate prevalence, lifetime distribution, and overlap of
long-lived pair identities. This tests whether the observed population is
robust to the detector rather than only to random initialization.

## Related Files

- `genesis_object_census.py`
- `src/genesis_grid/defect_tracker.py`
- `src/genesis_grid/pairline_tracker.py`
- `results/pair_census.json`
