# Genesis V3 — Traveling Pair Benchmark

## A known traveling state

Cooper’s 1998 continuum study is a close mathematical benchmark for a neutral pair in a single orientation field. Its conservative Landau–Lifshitz dynamics acts on a unit vector at each point in two dimensions. The numerical example uses isotropic exchange. At high momentum, the localized solution has two opposite-winding cores and moves at constant velocity perpendicular to the line joining them. Figure 3(b) shows one such configuration. This is a theoretical and numerical result. [Cooper, *Physical Review Letters* 80, 4554–4557](https://doi.org/10.1103/PhysRevLett.80.4554) · [Full text](https://arxiv.org/pdf/cond-mat/9801160)

The construction selects a field by minimizing its energy at fixed net topological charge $Q=0$, momentum $\mathbf P$, and axial spin deficit $N$. The momentum is proportional to a 90° rotation of the first spatial moment of topological charge density. For two localized charges close to $+1$ and $-1$ with little charge moment in the exterior, that first moment approximates their separation vector. Conservation of the full moment does not by itself fix their spacing if the exterior carries a changing share. [Cooper, equations (2)–(7)](https://arxiv.org/pdf/cond-mat/9801160)

The selected profile is stationary in a frame that translates and also allows common axial rotation. In vector notation its initial rate satisfies

$$
\partial_t\mathbf n = -v_x\,\partial_x\mathbf n - v_y\,\partial_y\mathbf n
+\omega\,\hat{\mathbf z}\times\mathbf n.
$$

A common axial rotation preserves $n_z$ and the charge profile. It therefore belongs in the comparison even when the observed motion of the centers appears to be pure translation. [Cooper, equation (5)](https://arxiv.org/pdf/cond-mat/9801160)

## Transfer to Genesis

The testable idea is that a traveling pair starts close to a **coherent field profile**, including the region around the knots. At a saved V3 checkpoint, calculate the actual conservative rate from the simulator and ask how much of it can be represented by one translation and one common axial rotation. The residual is the part of the instantaneous change that deforms the profile in that frame. Fit from the initial field only. Compare the residual on the staged traveler and on contracting and expanding cases using identical measurement conventions, then freeze any prediction before using a set-aside trajectory. A low residual is a candidate predictor of finite-time coherent motion, and its validity over three core diameters must be checked against the trajectory. A residual magnitude alone cannot distinguish closing from opening. [V3 model](../../../src/genesis_v3/model.py) · [V3 precession](../../../src/genesis_v3/rotation.py) · [[Genesis Revival — Orientation Field Experiment]]

V3 adds a sharp-gradient energy and easy-axis preference, and its finite grid has a fixed perimeter. These change the energy landscape and limit continuous translation symmetry. Cooper’s published numerical thresholds and dispersion therefore do not transfer directly. The benchmark supplies the shape of a diagnostic for an existing V3 pair. Autonomous formation from disorder is a separate milestone. [Cooper, equations (6)–(7) and numerical setup](https://arxiv.org/pdf/cond-mat/9801160) · [V3 model](../../../src/genesis_v3/model.py)

## Bounded Genesis test

Evaluate the actual conservative rate and fit the two translation components and common rotation by least squares in a radius-0.14 tube about the core segment. Use centered, tangent-projected spatial differences. Divide the residual norm by the actual rate norm. Put both starting fields in domains padded by 0.125 per side. The reference cases are the mature staged traveler and the unrotated contracting checkpoint previously extended in the wider domain. The score measures instantaneous deformation relative to the local evolution rate. It is not a stability theorem.

Freeze a binary forecast by taking the midpoint between the two 113-grid reference scores. Use two new starts at the same spacing. Apply a common +45° axial rotation inside radius 0.10 of the pair segment, taper it to zero by radius 0.155, then pad. Start one from the saved staged time-0.030 field and one from the contracting checkpoint. Save both forecasts before evolution. Predict three-diameter travel below the cutoff and a spacing violation above it. Keep the existing 15% spacing, charge, tracking, and boundary gates. Cap follow-up at 0.6. These are held-out trajectories from the same seed family. They do not provide independent-seed validation.

| Starting field | 113-spacing residual | 129-spacing residual |
|---|---:|---:|
| Mature staged traveler, padded | 0.247 | 0.248 |
| Contracting reference, padded | 0.981 | 0.985 |
| Winding-reversed expander, original domain | 0.975 | 0.977 |

The unpadded expander is a separate retrospective check and was excluded from calibration. Its high residual is consistent with the score indicating departure from a rigidly translating profile, without encoding the sign of spacing change.

**Success for the two frozen failure forecasts.** The cutoff was 0.61377. Both unseen starts scored high and were forecast to violate the spacing limit. Both contracted past that limit with tracked cores. The staged time-0.030 variant came close to three diameters, so the result depends on the previously defined travel gate.

| Held-out start | Residual | Outcome | Travel at violation | Spacing change |
|---|---:|---|---:|---:|
| Staged, +45° | 0.959 | Spacing failure | 2.943 diameters | −16.70% |
| Contracting, +45° | 0.982 | Spacing failure | 1.755 diameters | −15.56% |

The benchmark distinguished the known traveler from the unstable reference fields and correctly forecast both new failures. Neither held-out case provided a low-score forecast of successful travel. The cutoff is specific to this comparison. The results do not establish predictive sufficiency, autonomous formation, or an interaction missing from the single-field rule.

[Initial-field diagnostic](../../../src/genesis_v3/traveling_profile.py) · [Reference scores](../../../results/genesis_v3_fixed_rule/traveling_profile_comparison.json) · [Frozen forecasts](../../../results/genesis_v3_fixed_rule/traveling_profile_heldout_forecast.json) · [Held-out trajectories](../../../results/genesis_v3_fixed_rule/traveling_profile_heldout_result.json)

## Low-score challenge

Use the mature seed-405 staged time-0.035 field at 113 spacing. Apply a new +5° local axial rotation with the same tube and taper as the +45° challenges, then add the same padding. Freeze the score and classification before evolving. Use the existing cutoff of 0.61377, the same integration and measurement conventions, and the time cap of 0.6. The small rotation deliberately challenges the forecast near the known traveling state. This is a distinct starting field from the calibration case, but it shares its seed and preparation and is a local robustness test.

**Success for the low-score forecast.** The frozen score was 0.58705, below the 0.61377 cutoff. The pair reached 3.061 core diameters at time 0.175 with 9.62% contraction and both opposite-charge cores resolved. Together with the two previous failure forecasts, the frozen rule correctly classified all three new trajectories in this bounded comparison. The positive case was a mild perturbation of the calibrated traveler on one grid. This result supports using the score to screen nearby prepared states. It supplies no independent-seed validation and no evidence that an unchanged rule builds such states autonomously.

[Frozen low-score forecast](../../../results/genesis_v3_fixed_rule/traveling_profile_low_score_forecast.json) · [Low-score trajectory](../../../results/genesis_v3_fixed_rule/traveling_profile_low_score_result.json)

## Cross-seed challenge

Use the saved mature wall-born seed-22 fields at time 0.085 on 97×97 and 113×113. Seed 22 was used in earlier V3 work and played no role in choosing this score or cutoff. Apply the same +5° rotation and padding as in the seed-405 low-score challenge so these trajectories differ from the prior seed-22 replays. Retain the checkpoint's gradient penalty 0.0002 and easy-axis strength 150 in the score and trajectory. Freeze both forecasts at cutoff 0.61377 before evolution. Apply the same gates and time cap 0.6. The two grids are a resolution check on one seed.

**Failure of the cross-seed forecast.** Both initial scores exceeded the cutoff and predicted a spacing violation. Both pairs instead passed three diameters with resolved opposite charges and little spacing drift.

| Grid | Initial score | Forecast | Travel at pass | Maximum absolute spacing change |
|---|---:|---|---:|---:|
| 97×97 | 0.8335 | Spacing failure | 3.028 diameters | 1.22% |
| 113×113 | 0.7660 | Spacing failure | 3.008 diameters | 2.45% |

The fixed score and cutoff do not generalize from seed 405 to this staged seed-22 family. The test also carries the seed's own anisotropy setting, so it does not isolate seed variation from that parameter change. A high initial deformation residual is compatible with subsequent coherent travel. Do not retune the cutoff on this challenge or use the score to justify a substrate change. The result leaves the staged travel benchmark intact and autonomous assembly open.

[Frozen cross-seed forecasts](../../../results/genesis_v3_fixed_rule/traveling_profile_seed22_forecast.json) · [Cross-seed trajectories](../../../results/genesis_v3_fixed_rule/traveling_profile_seed22_result.json)

## What did the staged handoff change?

At 113 spacing, branch each mature seed-22 and seed-405 field into the conservative release and a continuation of the original projected relaxation. Both branches start with the same 0.125 padding per side, orientation, and energy coefficients. Measure over the first 0.04 after handoff in intervals of 0.0025. Keep the same core lineage and stop a branch if it cannot be tracked. This compares the post-handoff behavior with a matched no-switch counterfactual in the padded geometry.

Record the energy within radius 0.10 of the moving core segment, in the surrounding band from 0.10 to 0.22, and outside. Also report energy in the same band fixed at the initial location to check for a moving-window effect. Compare spacing and the precession-rate residual from the initial-field diagnostic. A low residual indicates that the current conservative rate resembles a shared translation and axial rotation. On the relaxation branch the same score describes the conservative rate the field would have at that instant, rather than its actual relaxation rate. Energy in a band is a regional readout and cannot by itself establish outward radiation.

**Both pairs began coordinated sideways motion by the first sample after release.** Continued relaxation from the identical field instead produced rapid contraction. Transverse speed is projected perpendicular to the initial core segment, with the sign convention chosen to match the released motion. Values are per unit model time.

| Seed | Released core speeds at first sample, negative / positive | Released spacing change at 0.04 | Continued relaxation, last tracked spacing change |
|---|---:|---:|---:|
| 22 | 1.049 / 0.946 | −0.45% | −30.65% at 0.0175 |
| 405 | 0.951 / 1.167 | −0.11% | −27.15% at 0.0150 |

At the first sample, the moving surrounding band's energy increased 1.36% for seed 22 and decreased 3.92% for seed 405. The conservative deformation score rose immediately on both seeds while the cores were already traveling. By 0.04 the score was 0.247 for seed 22 and 0.488 for seed 405, compared with 0.231 and 0.247 at launch. Neither a shared early decline in surrounding energy nor convergence toward rigid translation was observed before the start of coordinated motion. The contrast supports the immediate change from relaxational contraction to conservative sideways motion in these prepared fields. It leaves open how the staged preparation produced that capability and whether smaller-scale or earlier energy transfer contributed.

[Seed 22 handoff comparison](../../../results/genesis_v3_fixed_rule/handoff_mechanism_22.json) · [Seed 405 handoff comparison](../../../results/genesis_v3_fixed_rule/handoff_mechanism_405.json) · [Reproduction code](../../../src/genesis_v3/handoff_mechanism.py)

## Can weaker continuous relaxation coexist with travel?

As a bounded compatibility test, take damping 0.25, the weakest positive value in the earlier fixed-rule formation screen. Apply it continuously with unit precession to both known staged handoffs at 113 spacing with 0.125 padding per side. Keep the seed-specific energy coefficients, the original travel gates, and a time cap of 0.6. If both prepared pairs pass, test the same coefficient from disorder. Failure on these handoffs rejects this candidate as a bridge between these preparation and travel regimes. It does not exhaust smaller damping values or different relaxation laws.

**Failure for continuous damping 0.25.** Both pairs violated the 15% spacing gate by contracting while their cores remained tracked. Seed 22 traveled 0.679 core diameters before contracting 15.48% at time 0.0400. Seed 405 traveled 0.741 diameters before contracting 16.97% at time 0.0375. The corresponding zero-damping branches in the handoff comparison changed spacing by less than 0.5% at 0.04. The candidate failed the sustainment prerequisite, so the formation branch was not run. The compiled step matched NumPy to 1.28 × 10⁻¹⁵ in maximum orientation difference after 1,000 steps at damping 0.25 on a 65×65 field.

[Seed 22 weaker damping](../../../results/genesis_v3_fixed_rule/weak_damping_sustain_22.json) · [Seed 405 weaker damping](../../../results/genesis_v3_fixed_rule/weak_damping_sustain_405.json)

## Relaxation gated by local bending

At each site compute the magnitude of the sum of its four neighbor differences divided by twice the root sum of their squared magnitudes. An aligned field gives zero. Locally linear gradients mostly cancel in the numerator. Turn damping on smoothly from zero at a ratio of 0.25 to 0.75 at 0.65, using the same rule at every site and integration stage. Precession remains active. These thresholds specify a cell-scale experiment, so a success at one resolution would require a separate spacing check. The rule can also damp a smooth extremum or a small core if its bending is strong at lattice scale.

Test the unchanged coefficient and thresholds on both mature staged pairs at 113 spacing with the same 15% and three-diameter gates. Separately replay the padded seed-405 disorder through time 0.01 with the same rule and an uncoupled damping-off control. Compare wall candidates, net charge, and energy to check whether damping acts during early organization. These are prerequisite screens for full autonomous assembly.

**Both prerequisite screens passed.** The staged seed-22 and seed-405 pairs traveled 3.007 and 3.061 core diameters respectively. Their endpoint spacing changes were −0.73% and −9.63%. In the disordered start, 9.8% of interior sites initially had nonzero damping. The gated run formed wall candidates, stayed neutral through 0.01, and lost 51.3% of its energy. The zero-damping control formed wall candidates but reached net charge +1 at the first violating sample, 0.0015. The compiled gated step matched the NumPy RK4 reference to 1.23 × 10⁻¹⁵ after 100 steps.

Advance the same rule to seed-405 formation on 113×113 and 129×129 interior grids. Keep 0.125 padding per side, bias −0.12, easy-axis strength 225, and penalty 0.0002. Use a maximum dimensionless step of 0.02, sample every 0.0025 through 0.14, and apply the established wall ancestry, neutrality, mature charge 0.90, and travel criteria. This tests one exploratory seed across resolutions.

[Prepared seed 22](../../../results/genesis_v3_fixed_rule/roughness_sustain_22.json) · [Prepared seed 405](../../../results/genesis_v3_fixed_rule/roughness_sustain_405.json) · [Early disorder screen](../../../results/genesis_v3_fixed_rule/roughness_disorder_405.json)

**Inconclusive for autonomous travel.** The original schedule computed 57 intervals for the 0.14 cap, giving actual sampling intervals of 0.00245614. Both grids stayed neutral and produced a mature opposite-charge pair with shared wall ancestry. At 113 spacing the pair first qualified at 0.02456 and traveled 0.087 diameters before tracking ended at 0.02947. At 129 spacing the pair first qualified at 0.04175 and tracking ended at the next sample, 0.04421. A replay from each saved formation field found qualifying signed charge in radius-0.09 disks within 0.035 of both last tracked centers at the stopping sample. This confirms that the tracking limits do not establish loss of local charge, but it does not establish continuous core identity or coherent travel past those samples.

| Grid | Net travel last measured | Nearby local charges at tracker stop |
|---|---:|---:|
| 113×113 | 0.087 diameters | −0.946 / +0.999 |
| 129×129 | Formation sample only | −0.986 / +1.190 |

This rule has demonstrated compatibility with early disorder relaxation and prepared-pair sustainment. It has not yet demonstrated that the pairs produced from disorder survive as identifiable traveling objects.

[113 formation](../../../results/genesis_v3_fixed_rule/roughness_formation_113.json) · [129 formation](../../../results/genesis_v3_fixed_rule/roughness_formation_129.json) · [113 endpoint check](../../../results/genesis_v3_fixed_rule/roughness_formation_endpoint_113.json) · [129 endpoint check](../../../results/genesis_v3_fixed_rule/roughness_formation_endpoint_129.json)

### Following the wall-born pairs by local charge

Continue each saved formation field with its original timestep and damping law. At intervals of about 0.001, search for a nearby center using signed charge in disks of radii 0.055 and 0.075 and a continuity penalty. Confirm each center using the existing radius-0.09 charge disk, partitioning any overlap. Use the original pair separation and core diameter. A spacing failure requires both estimates to cross the 15% threshold in the same direction. The prepared seed-22 control passed this tracker at 3.008 diameters with resolved opposite charges and 5.68% endpoint spacing change.

**Failure to demonstrate autonomous travel across grids.** The new tracker followed both candidates beyond the earlier region-tracking limits. At 129 spacing both estimates found the pair opening past 15% after only 0.21–0.26 diameters of travel. Both signed cores retained charge magnitude above 0.97. At 113 spacing the positive disk fell to +0.630 after about 0.13 diameters of net travel at the endpoint. The strongest nearby disk reached only +0.677, below the 0.70 threshold. This is a localized-charge tracking limit and does not establish annihilation or exclude charge farther from the tracked site.

[Prepared control](../../../results/genesis_v3_fixed_rule/roughness_charge_follow_control.json) · [113-spacing continuation](../../../results/genesis_v3_fixed_rule/roughness_charge_follow_113.json) · [129-spacing continuation](../../../results/genesis_v3_fixed_rule/roughness_charge_follow_129.json)

## When does a pair become ready to travel?

Take five snapshots of each staged formation trajectory at 113 spacing, centered on its successful handoff and separated by 0.005. Take five snapshots of each local-damping trajectory at 113 and 129 spacing, centered on the first mature pair and separated by one formation sample. Continue the original preparation between snapshots, independently of the release tests. For each snapshot with a resolved opposite-charge pair, run the same zero-damping precession diagnostic for 0.0125. Keep the padded domain, original physical spacing and energy coefficients. A short coordinated release requires continuous two-core tracking, less than 5% spacing drift, both mean transverse speeds in the same direction with magnitude at least 0.2, and a speed difference at most 30% of their mean absolute speed. This screen measures early coordination and does not replace the three-diameter travel test. Turning damping off for the probe is an intervention.

All ten staged snapshots passed, including those 0.01 before the successful handoff. The onset of short coordination is earlier than the earliest sampled staged snapshot, or at that snapshot. For the ten local-damping snapshots, five had no resolved pair at launch and five lost region tracking during the conservative release. A charge-peak replay failed to detect short motion in the staged seed-22 positive control, so that readout cannot establish stationary cores.

A subcell charge-centroid replay followed all five locally damped starts with resolved launch pairs through roughly 0.012–0.013. Use two Gaussian scales and measure mean transverse speed after the first two samples to reduce dependence on the original center convention. The staged seed-22 control passed under both scales. One early 113-spacing snapshot at 0.019649 also passed under both scales, with 2.2–2.7% maximum spacing change and 9–12% speed mismatch. Its positive charge at launch was +0.729, below the mature-pair requirement of 0.90. Its positive region was spatially distinct from the one in the first mature pair at 0.024561. The two mature starts failed the short coordination criteria. On 113 spacing their cores moved in opposite transverse directions. On 129 spacing their spacing changed by more than 9%.

These observations show brief coordinated release is possible in a locally damped formation trajectory, while maturity by local charge is insufficient to identify a coordinated pair. The early result did not repeat across grids in this sample and does not establish that continued damping destroyed that same candidate. The staged preparations gave the only repeatable short coordination across their sampled times. The autonomous milestone remains open.

[Region-tracked releases](../../../results/genesis_v3_fixed_rule/formation_snapshot_release.json) · [Charge-centroid releases](../../../results/genesis_v3_fixed_rule/formation_snapshot_centroid_release.json) · [Charge-centroid control](../../../results/genesis_v3_fixed_rule/formation_snapshot_centroid_control.json)
