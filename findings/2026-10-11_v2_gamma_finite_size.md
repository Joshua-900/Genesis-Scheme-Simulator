# 2026-10-11 - V2-gamma bounded response survives modest finite-size changes

**Source:** `genesis_v2_gamma_finite_size.py --sizes 32 64 96 --cutoffs 0.70 0.75 0.80 --seeds 3`
**Status:** preliminary finite-size robustness result
**Owner:** Joshua

## Headline

The inside-versus-outside location-control effect survives from `N=64` to
`N=96` across the usable relation-permeability cutoffs. Candidate area stays
on the order of tens of lattice cells rather than scaling with the full field.

This clears a modest **finite-size robustness** gate for the current gamma
observer. It is not a continuum-resolution result, because `N` changes the
model's lattice extent rather than a calibrated physical discretization.

## Results

Each condition used three seeds, 1200 warmup frames, 400 recovery frames, and
equal inside/outside `pi/2` perturbations. Values are medians over measured
runs; a run is omitted if a candidate and matched patches cannot be formed.

| Size | Cutoff | Measured runs | Candidate area fraction | Control overlap | Inside candidate delta | Outside candidate delta |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 32 | 0.70 | 2/3 | 0.2651 | 0.379 | 0.067 | 0.002 |
| 32 | 0.75 | 1/3 | 0.0479 | 0.415 | 0.497 | 0.039 |
| 32 | 0.80 | 0/3 | - | - | - | - |
| 64 | 0.70 | 2/3 | 0.0632 | 0.408 | 0.183 | 0.003 |
| 64 | 0.75 | 3/3 | 0.0220 | 0.478 | 0.390 | 0.005 |
| 64 | 0.80 | 3/3 | 0.0073 | 0.614 | 0.558 | 0.047 |
| 96 | 0.70 | 2/3 | 0.0626 | 0.232 | 0.110 | 0.001 |
| 96 | 0.75 | 3/3 | 0.0094 | 0.389 | 0.475 | 0.008 |
| 96 | 0.80 | 3/3 | 0.0035 | 0.675 | 0.394 | 0.044 |

At cutoff `0.75`, median candidate area is about 49 cells at `N=32` (one
measured run), 90 at `N=64`, and 87 at `N=96`. At cutoff `0.80`, it is about
30 cells at `N=64` and 32 at `N=96`. Those are tentative characteristic
lattice scales, not a proven universal size.

## Interpretation

1. The bounded-response effect is not confined to one `N=64`, cutoff-0.75
   presentation. It reproduces at `N=64` and `N=96` across nearby usable
   cutoffs.
2. Inside perturbations retain a much larger residual in the selected
   candidate than outside perturbations. At cutoff `0.75`, the ratio of
   median inside to outside candidate effect is about 47 at `N=64` and 57 at
   `N=96`.
3. Stricter cutoffs reduce candidate size but retain the response. The
   observer changes the partition scale, so the model has not established an
   observer-independent object class.
4. `N=32` cannot consistently support the stricter candidate-plus-buffer
   protocol. It is a boundary condition of this experiment, not negative
   evidence against gamma.

## Decision

Gamma now has a reproducible, finite-size-stable **bounded-response candidate
phenomenon**. This warrants a next test of whether a candidate's future can
be predicted or controlled at the region level better than by an equal-sized
background patch. Do not describe it as an autonomous object yet.

## Related Files

- `genesis_v2_gamma_finite_size.py`
- `genesis_v2_gamma_location_control.py`
- `src/genesis_v2_gamma/probes.py`
- `results/v2_gamma_finite_size.json`
