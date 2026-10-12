# 2026-10-11 - V2-delta delays coarsening but does not select a bounded scale

**Source:** `genesis_v2_delta_sweep.py` and
`genesis_v2_delta_stationarity.py`
**Status:** preliminary negative scale-selection result
**Owner:** Joshua

## Headline

V2-delta adds a specified competing-scale rule: local relation aligns
actuality while a smoothed, longer-range relational direction applies a weak
counter-torque. It avoids both immediate potentiality/actuality collapse and
gamma's early single-domain outcome in a narrow low-counter regime.

It does not yet select a stable bounded scale. After an early many-domain
phase, the largest observer-defined domain continued to grow until it occupied
roughly three quarters of the lattice.

## Protocol

The initial map used `N=64`, 2,000 frames, three seeds, relation cutoff `0.75`,
and minimum domain area `24`. It swept counter-gain `{0.03, 0.08, 0.16}` and
long-range smoothing passes `{4, 8, 12}`. The most promising condition
(`gain=0.03`, `passes=4`) was then sampled through 8,000 frames for three
`N=64` seeds and one `N=96` seed.

## Regime Map

| Smoothing passes | Counter gain | P/A alignment | Largest domain fraction | Mean domain count |
| ---: | ---: | ---: | ---: | ---: |
| 4 | 0.03 | 0.342 | 0.076 | 37.00 |
| 4 | 0.08 | 0.172 | 0.034 | 33.00 |
| 4 | 0.16 | 0.029 | 0.010 | 6.00 |
| 8 | 0.03 | 0.308 | 0.059 | 37.67 |
| 8 | 0.08 | 0.103 | 0.021 | 28.00 |
| 8 | 0.16 | 0.014 | 0.003 | 0.33 |
| 12 | 0.03 | 0.281 | 0.050 | 37.33 |
| 12 | 0.08 | 0.073 | 0.017 | 20.33 |
| 12 | 0.16 | 0.013 | 0.000 | 0.00 |

Low counter-gain produces a middle regime; high counter-gain suppresses
coherent domains into fragmentation. This maps a behavior window, not an
object class.

## Long-Horizon Result

For the low-counter condition, `N=64` largest-domain fractions at frame 8,000
were `0.761`, `0.810`, and `0.749` across seeds 1--3. The corresponding
domain counts fell from roughly 35--42 near frame 2,000 to 8--11 at frame
8,000. At `N=96`, the largest domain likewise reached `0.803` by frame 8,000.

The similar dominant fraction across lattice sizes is evidence against this
rule selecting a small intrinsic object scale. It is consistent with slowed
coarsening toward a macroscopic phase rather than sustained bounded units.

## Interpretation

1. A spatial counter-relation is a legitimate, independently testable way to
   oppose local absorption; it improved the transient structure relative to
   gamma.
2. Its current static form is insufficient: it delays dominance without
   preventing it.
3. The next mechanism needs **time-scale separation and renewal**, not simply
   a stronger spatial counter-term. A candidate resource/inhibition mechanism
   must state what accumulates, how it spreads or recovers, and how it changes
   merger pressure.
4. The next acceptance gate is a bounded late-time area distribution and
   bounded-track survival across a modest lattice and observer sweep. Merely
   producing spots at one parameter choice is failure.

## Related Files

- `src/genesis_v2_delta/core.py`
- `genesis_v2_delta_sweep.py`
- `genesis_v2_delta_stationarity.py`
- `results/v2_delta_regime_passes4.json`
- `results/v2_delta_regime_passes8.json`
- `results/v2_delta_regime_passes12.json`
- `results/v2_delta_stationarity_seed1.json`
- `results/v2_delta_stationarity_seed2.json`
- `results/v2_delta_stationarity_seed3.json`
- `results/v2_delta_stationarity_N96_seed1.json`
