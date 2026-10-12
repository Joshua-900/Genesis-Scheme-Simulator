# P-to-A Coupling Has a Coherent Field Dose Response Without Replacing V1 Local Structure

## Design

Twenty fixed seeds were evaluated at five P-to-A gains: `0`, `0.025`, `0.05`,
`0.10`, and `0.20`. The high-compression V1 substrate, potential transport,
and source restoration were held fixed. Each strength received two predeclared
measurements:

1. A 2,000-frame field audit of P/A alignment, global actual-order, tension,
   compression, and vortex count.
2. The 1,000-frame burn-in plus matched candidate-neighborhood, background,
   and untouched strict-continuation test.

## Field Results

| P-to-A gain | P/A alignment | Mean tension | Mean compression | Vortex count | Global actual-order |
|---:|---:|---:|---:|---:|---:|
| 0 | 0.013 | 0.047 | 0.066 | 35 | 0.176 |
| 0.025 | 0.089 | 0.059 | 0.068 | 34 | 0.184 |
| 0.05 | 0.156 | 0.076 | 0.068 | 34 | 0.187 |
| 0.10 | 0.273 | 0.114 | 0.068 | 38 | 0.198 |
| 0.20 | 0.425 | 0.190 | 0.088 | 48 | 0.139 |

For every seed, P/A alignment and tension had a monotonic positive Spearman
association with gain (median `rho = 1.0`; paired two-sided Wilcoxon
`p = 0.0000077`). Compression and vortex count also rose overall (median
per-seed `rho = 0.50`, `p = 0.000084`; and `rho = 0.669`, `p = 0.000138`).
Global actual-order turned downward at the strongest gain (median per-seed
`rho = -0.45`, `p = 0.0416`).

## Local Structural Results

| P-to-A gain | Candidate median | Background median | Candidate lower / equal / higher | One-sided paired `p` |
|---:|---:|---:|---:|---:|
| 0 | 4.5 | 22 | 15 / 4 / 1 | 0.000802 |
| 0.025 | 3 | 14.5 | 14 / 5 / 1 | 0.000732 |
| 0.05 | 2 | 7 | 12 / 8 / 0 | 0.00108 |
| 0.10 | 1.5 | 8 | 13 / 6 / 1 | 0.00226 |
| 0.20 | 5 | 31 | 14 / 5 / 1 | 0.000662 |

At every strength, candidate-neighborhood weakening still reduced strict pair
continuation relative to the same-shape background control. However, the size
of that background-minus-candidate deficit had no monotonic gain trend across
the 19 informative seeds (median `rho = -0.051`, two-sided `p = 0.737`).

## Interpretation

The V2 bridge has crossed an important threshold: P-to-A strength is a
measurable, controllable parameter with a reproducible field-level dose
response. It does not replace the V1 structural mechanism; the matched local
causal lead remains visible across the whole tested range.

The response is not a one-dimensional persistence control. Stronger coupling
increases alignment, tension, compression, and vortex population, while the
highest tested gain lowers global actual-order. This is evidence of competing
effects or a regime shift, not evidence that more P-to-A coupling is simply
better.

## Next Test

Map the apparent high-gain transition more narrowly between `0.10` and `0.20`
with field observables and spatial diagnostics. Keep the mechanism fixed. The
purpose is to determine whether the shift is a reproducible regime boundary or
a smooth tradeoff before interpreting or modifying P dynamics further.
