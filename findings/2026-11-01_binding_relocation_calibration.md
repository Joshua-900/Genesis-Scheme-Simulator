# Binding relocation calibration: topology moves, retained state is distorted

Date: 2026-11-01. Scope: Stage B of the structural binding-response milestone.

The compact relocation procedure fails its declared numerical error budget.
This is a limitation of the intervention, not evidence for or against binding.
No dynamical response trajectories were generated.

## Fixed method

The two preflight-selected full V1 states, seeds 1005 and 3001, were used without
new candidate selection. Each has sham, stretch, compression and two common-
translation arms. The requested nonsham displacement is one grid cell per core
along the dominant Cartesian separation axis. Relative arms move the two cores
in opposite directions; translation arms move them together.

A periodic coordinate map has rigid translation inside radius1 and a cosine
taper to identity at radius3. Its displacement Lipschitz bound is pi/4<1;
inverse fixed-point sampling is therefore contractive. Bilinear interpolation
samples unit phasors for theta and stored values for tau/ux/uy/C. Vector
components are transported as lab-frame values, not transformed as tensors.
Only the local neighborhoods move; extended wakes remain unchanged.

Protocol, code hashes and numerical limits were written before case evaluation.
The entire expected winding map, fresh tracker assignment, exact off-support
values, protected core-corner values and forward/reverse mapping error were
checked. No acceptance tolerance was changed after results.

## Outcome

Both sham arms pass exactly. All eight nonsham arms fail: displacement's
within-support roundtrip relative L2 discrepancy is 26.0%–51.4%, exceeding the
declared 25% limit. Two arms also exceed the 25% tension discrepancy limit.

All eight preserve the entire expected winding map, place the selected charges
at the intended cells, preserve all fields outside support, and carry the four
corner values at each core to within 4.5e-16. Angle roundtrip phasor RMS is
0.0330–0.0529. Compression relative discrepancy is 15.8%–47.7%, within its
declared 50% ceiling. These normalized discrepancies are not energy losses or
percentages of the field's information destroyed.

The reverse operation samples the relocated data back at the original map's
forward coordinates. Its residual measures interpolation distortion, not
physical relaxation. The local fine structure cannot be transported cleanly
enough by this particular compact bilinear map. Moving the winding charges
correctly was insufficient to validate the surrounding-state intervention.

## Decision

Stop before Stage C under this method. An apparent restoring trajectory after
this operation could include a response to artificial smoothing of its retained
state. No bound-object, nonbinding, fuel-exhaustion or new-ingredient conclusion
follows. No threshold or radius sweep was used to rescue the method.

A next method proposal should avoid resampling retained state, for example a
finite-duration probe through the angle update while structural fields evolve
naturally, or justify a representation-preserving relocation. Such a probe
would be an explicitly temporary intervention, not new autonomous driving or
evidence of spontaneous assembly. It needs its own calibrated motion, topology
and pinning controls before a scientific response experiment.

All 54 tests pass, including six new relocation tests. Preserved baseline and
all inherited archive fingerprints match. Both engines and prior studies
remain unchanged.

- [Frozen protocol](../results/binding_calibration_2026-11-01/protocol.json)
- [All numerical results](../results/binding_calibration_2026-11-01/report.json)
- [Error-budget plot](../results/binding_calibration_2026-11-01/error_budget.png)
- [Local field comparison](../results/binding_calibration_2026-11-01/relocation_detail.png)
