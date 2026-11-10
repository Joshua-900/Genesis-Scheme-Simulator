---
Area: Research
status: proposed
tags:
  - genesis-scheme
  - topology
  - emergence
canonical: false
---

# Genesis Revival — Orientation Field Experiment

The [revival proposal](../../Genesis%20Scheme%20Research%20Revival.md) reframes Genesis as a laboratory for emergence. The first experiment holds the two-dimensional lattice fixed and changes the allowed orientation at each site from a circle to a sphere. A site can tilt out of plane, giving it two internal angular degrees of freedom.

## First question

Does a seeded localized texture retain a measurable identity and a resolved core under a specified local update? Start with persistence. Formation from disordered states is a subsequent experiment with a separate outcome.

Use [[V1 Baseline Audit — 2026-10-31]] as the historical record for the preserved V1 implementation. Preserve V1 and V2 as independent modules. Use an alignment-only planar control within the new experiment because a comparison against the entire V1 rule stack would change the rules and state space together.

## Matched models

Use the same square lattice, fixed uniform perimeter, nearest neighbors, and exchange strength in both lanes. Evolve unit vectors by a small projected descent step followed by normalization. If the initial vectors lie in a common plane through the origin, exchange and the update preserve that plane. Check this invariant before using the planar restriction as the alignment-only control.

For the spherical lane, start with a smooth seeded texture with measured absolute charge near one and a uniform perimeter. Include a uniform zero-charge fixture and a localized zero-charge distortion. The planar lane checks the update and its planar behavior. The spherical zero-charge distortion checks whether a localized shape alone persists. Record the starting profiles and boundary conditions.

## Measurements and decision

- Validate the charge readout on the fixtures using signed spherical triangle areas on the lattice. Flag ambiguous triangles and check charge across resolutions. [Berg and Lüscher](https://scixplorer.org/abs/1981NuPhB.190..412B/abstract)
- Track energy, charge, and core radius over time. A texture that keeps its charge while shrinking to a few cells counts as a collapse candidate. Discrete exchange lattices can permit collapse even when the smooth continuum texture has a topological charge. [Belavin and Polyakov](https://cds.cern.ch/record/406104) · [Lattice collapse study](https://arxiv.org/abs/1204.4848)
- Repeat with smaller time steps and finer grids at fixed physical domain size and initial core size. Record the mapping between update steps and model time across resolutions. Before running the comparison, specify the observation window and the minimum resolved core size.
- If exchange alone fails to sustain a resolved core, use that result as the reference for one additional interaction at a time. A candidate Genesis rule earns further study if its effect survives refinement and a matched rule-off run.

Report seeded persistence, spontaneous formation, and interactions separately. Spinorial behavior and DDFH's spatial-emergence question belong to separate tracks.

## V3 pilot

The separate `src/genesis_v3` package implements projected nearest-neighbor exchange with fixed boundaries. It reports a charged spherical seed, a spherical zero-charge distortion, a planar distortion, and a uniform fixture. The three localized seeds share their starting vertical profile. The reported radius is that of a disk with the same area as the sites where the vertical component is negative.

```powershell
.venv\Scripts\python.exe -B -m src.genesis_v3 --size 65 129
.venv\Scripts\python.exe -B -m src.genesis_v3 --size 65 --factor 0.1
```

At model time 0.01, both uncharged distortions lost their negative-core region. The charged texture retained charge −1 at both resolutions, but its radius fell from about 0.073 of the domain width to 0.040 on the 65×65 grid and 0.043 on the 129×129 grid. The coarse endpoint was below the pilot's three-cell resolution threshold. Halving the coarse time step gave the same endpoint radius to the reported precision. The planar control stayed exactly in its plane and the uniform fixture stayed at zero energy.

The pilot shows a seeded charged texture retaining its charge while shrinking over this window. A longer run and further spatial refinement are needed to characterize its fate.

## Exchange-only follow-up

Extended the observation window to model time 0.04 with samples every 0.001 and the same three-cell radius threshold. The physical domain and initial profile were fixed.

| Grid | Radius at 0.01 | Radius at 0.02 | Radius at 0.03 | Radius at 0.04 | Charge at 0.04 |
|---|---:|---:|---:|---:|---:|
| 65×65 | 0.0404 | 0.0088 | 0 | 0 | 0 |
| 129×129 | 0.0434 | 0.0366 | 0.0296 | 0.0237 | −1 |
| 193×193 | 0.0437 | 0.0373 | 0.0334 | 0.0295 | −1 |

Radii are fractions of domain width. The coarse core first fell below three lattice cells at sampled time 0.007 and first registered zero charge at 0.022. The finest core still spanned 5.67 cells in radius at the endpoint. Its physical radius kept declining through the last quarter of the window. The 129×129 step-size check reproduced all sampled core radii and charge to rounding precision at the tabulated times.

The coarse run exhibits collapse. The finer runs exhibit longer-lived, shrinking cores, with increasing resolution dependence late in the window. This establishes a reference for testing a stabilizing interaction. The eventual fate in the continuum remains open.

[Raw results](../../../results/genesis_v3_exchange_followup/report.json)

```powershell
.venv\Scripts\python.exe -B -m src.genesis_v3 --size 65 129 193 --duration 0.04 --samples 40
.venv\Scripts\python.exe -B -m src.genesis_v3 --size 129 --duration 0.04 --samples 40 --factor 0.1
```

## Sharp-gradient penalty

The added energy per bond is `λ |nᵢ − nⱼ|⁴ / (4 h²)`, with lattice spacing `h` and fixed physical coefficient `λ`. This penalizes sharp changes increasingly as a smooth texture contracts. The matched control uses `λ = 0`. All runs used the same physical domain, seeds, and model time of 0.04.

| Penalty | 65×65 final radius | 97×97 final radius | Final charge at 65 / 97 |
|---|---:|---:|---|
| 0 | 0 | 0 | 0 / 0 |
| 0.000025 | 0 | 0.0316 | 0 / −1 |
| 0.0001 | 0.0404 | 0.0459 | −1 / −1 |

Radii are fractions of domain width. On 65×65, the weaker penalty shifted the first sampled charge loss from 0.022 to 0.030. The smaller time step reproduced that sampled loss time. With the stronger penalty, both reported radii stayed in the same area-count bins from 0.02 to 0.04, and energy continued falling in both. The 65×65 radius was 2.59 cells, below the three-cell cutoff. The 97×97 radius was 4.41 cells. The plateau is provisional because the radius is quantized by cell counts and the coarse core is underresolved.

This term resists collapse over the test window. It supplies no opposing cost for expansion in a large domain. A finite core could reflect lattice resolution or the fixed perimeter. A longer run with a finer grid and a larger domain at fixed spacing would help distinguish those effects.

[Weak and control runs](../../../results/genesis_v3_gradient_penalty/report.json) · [Stronger runs](../../../results/genesis_v3_gradient_penalty/stronger.json)

```powershell
.venv\Scripts\python.exe -B -m src.genesis_v3 --size 65 97 --duration 0.04 --samples 20 --penalty 0.0001
```

## Finite-core test

Add a separate easy-axis energy, `K h² (1 − n_z²) / 2` per site. It favors either pole and charges energy for the tilted region between them. In a rescaled copy of a localized continuum profile, the sharp-gradient energy grows as the radius decreases and the easy-axis energy grows as the radius increases. Their competition motivates a finite-core test.

Use penalty 0.0002, easy-axis strength 30, and initial support radii 0.10 and 0.36. Compare 65×65 and 97×97 on width 1, plus 97×97 on width 1.5 to move the boundary at the coarse grid spacing. Run the narrow seed with easy-axis strength zero as an interaction control and halve the step bound for one coarse run. All runs end at model time 0.12.

Track the continuous tilt radius from the integrated weight `(1 − n_z) / 2` as well as the negative-core cell count. The tilt radius includes the surrounding transition region. For a finite-window pass, require charge magnitude one, a final negative-core radius of at least three cells on both resolutions, less than 2% drift in tilt radius over the final quarter, and endpoint agreement within 5% between starts, grids, and domain widths.

### Results through time 0.12

| Grid and width | Seed | Tilt radius at start | Tilt radius at 0.09 | Tilt radius at 0.12 | Final core radius in cells |
|---|---|---:|---:|---:|---:|
| 65×65, width 1 | Narrow | 0.03550 | 0.06563 | 0.06588 | 2.59 |
| 65×65, width 1 | Wide | 0.12780 | 0.06711 | 0.06622 | 2.59 |
| 97×97, width 1 | Narrow | 0.03550 | 0.07155 | 0.07178 | 4.41 |
| 97×97, width 1 | Wide | 0.12780 | 0.07267 | 0.07202 | 4.41 |
| 113×113, width 1 | Narrow | 0.03550 | 0.07255 | 0.07278 | 5.08 |
| 97×97, width 1.5 | Narrow | 0.03550 | 0.06619 | 0.06656 | 2.59 |
| 65×65, easy-axis off | Narrow | 0.03550 | 0.09345 | 0.09787 | 3.43 |

All runs retained charge −1 and sampled energy decreased. On the resolved 97×97 unit domain, the narrow seed grew and the wide seed shrank toward endpoints within 0.4% of one another. Both drifted less than 1% over the final quarter. Turning easy-axis off left the tilt radius still growing by about 4.7% over that interval. Increasing the domain at fixed coarse spacing changed the endpoint by about 1%, and halving the coarse time step changed the endpoint by less than 0.01%.

The original cross-grid gate did not pass. The 65×65 core is underresolved and its tilt radius differs from the 97×97 unit-domain result by more than 5%. The resolved two-start result gives evidence of a preferred size over this window. The boundary check so far is at coarse spacing.

An added 113×113 narrow-seed check ended within 1.4% of the 97×97 narrow-seed result and drifted about 0.3% over the final quarter. It retained charge −1 and had a resolved core. The remaining check is to vary the domain width at resolved spacing.

[Raw comparison runs](../../../results/genesis_v3_finite_core/report.json) · [113×113 refinement](../../../results/genesis_v3_finite_core/refined.json)

```powershell
.venv\Scripts\python.exe -B -m src.genesis_v3 --size 65 97 --duration 0.12 --samples 24 --penalty 0.0002 --easy-axis 30 --support-radius 0.10 --charged-only
```

## Pair interaction test

Use the same local update as the finite-core experiment. Seed compact, initially disjoint textures along the horizontal midline and compare the left texture with an isolated copy at the same position. The right texture has either the same winding or reversed winding. Keep the initial azimuth convention fixed. This samples one orientation arrangement for each pair.

Track the signed charge in each half of the domain and its horizontal centroid. Total charge alone would miss an opposite-charge pair because its charges cancel even when both knots are intact. Report the left centroid's displacement relative to the isolated run. Use separation 0.2083 for the nearby pair, twice that for the distant check, and repeat the nearby pair on 65×65. These are seeded interactions under dissipative evolution.

### Results

| Grid and starting separation | Same-charge extra outward shift | Opposite-charge extra outward shift |
|---|---:|---:|
| 65×65, 0.2083 | 0.00942 | 0.03410 |
| 97×97, 0.2083 | 0.01209 | 0.04066 |
| 97×97, 0.4167 | 0.00238 | 0.00701 |

Shifts are measured at time 0.08 in unit-domain coordinates, relative to the isolated left texture at the same starting position. Both nearby arrangements separated at both resolutions and retained their signed half-domain charges. Doubling the starting separation reduced the effect by roughly a factor of five to six on the resolved grid. The coarse result checks direction, with a sizable difference in magnitude. These are charge-centroid shifts under a particular azimuth arrangement. Shape changes can also move the centroid.

The resolved boundary check used a 129×129 grid of width 4/3, matching the spacing of 97×97 at width 1. At time 0.12, the tilt radius was 0.07249 versus 0.07178 on the original domain, a difference of about 1%. Both retained charge −1 and had a 4.41-cell negative-core radius.

[Nearby runs](../../../results/genesis_v3_pair_interactions/near.json) · [Distant runs](../../../results/genesis_v3_pair_interactions/far.json) · [Coarse check](../../../results/genesis_v3_pair_interactions/refinement.json) · [Boundary check](../../../results/genesis_v3_pair_interactions/boundary.json)

```powershell
.venv\Scripts\python.exe -B -m src.genesis_v3 --size 97 --duration 0.08 --samples 16 --penalty 0.0002 --easy-axis 30 --support-radius 0.10 --pair-separation 0.20833333333333333
```

## Relative orientation and binding

Rotate the right knot around the internal vertical axis at initialization using `--pair-phase`. This preserves the starting positions and charges. Track the number and centroid spacing of connected negative-core regions as well as charge. The two-core milestone requires convergence to a nonzero spacing from different starts, recovery after perturbation, and replication at finer spacing.

At starting separation 0.2083, the 65×65 runs at phases π/2 and π reversed the separation seen at phase zero. Same-charge knots approached and joined into one connected negative-core region with charge −2 through time 0.16. Opposite-charge cores disappeared. The same-charge composite's final energy was about 1.24–1.25 units below twice the energy of the separately evolved isolated knot at the same endpoint.

At separation 0.2917 and phase π, the same-charge pair still had two cores at time 0.16, but the separation was still falling. The closer case at separation 0.1458 required smaller starting profiles to avoid overlap. Those profiles were underresolved on the coarse grid and lost charge, so that case cannot establish a close-range interaction outcome.

The 97×97 run at separation 0.2083 and phase π reproduced both outcomes. At time 0.16, the same-charge composite had charge −2, one connected core with an equivalent radius of 8.39 cells, and energy 1.43 units below twice the isolated endpoint energy. The opposite-charge cores disappeared and the field energy approached zero.

The specified two-core milestone remains open. The runs established an orientation-dependent reversal and a resolved fused composite. No resolved pair settled at a nonzero separation, so the return-after-perturbation check for a two-core pair was not applicable.

[Raw phase and spacing runs](../../../results/genesis_v3_binding/)

## Formation from smooth disorder

The formation runner initializes smooth random azimuth and tilt from the same sine modes and random coefficients at each grid size. The perimeter points up. The initial field contains no inserted knot profile. Broad negative-orientation regions can occur, so initial charge is checked both globally and in disks of radius 0.09.

Compare the stabilized field (penalty 0.0002, easy-axis strength 30) with exchange alone from the same starts. Count a candidate pair only when separate negative-core regions each span at least three cells in equivalent radius, their radius-0.09 disks are disjoint, and the signed disk charges are at least 0.7 in magnitude with opposite signs. The formation milestone requires such pairs to persist across at least three consecutive samples, to recur across seeds, and to survive refinement. Check initial disk charges before attributing a candidate to formation. The sampled detector can miss shorter-lived or smaller features.

### Results

Seeds 11, 22, and 33 started at total charge zero on 65×65 and 97×97 grids. The largest absolute initial disk charge ranged from 0.57 to 0.64. Sampled every 0.005 through time 0.08, none of the six stabilized runs or their six exchange controls produced a qualifying pair at any sampled time. Exchange alone briefly produced localized charge and changes in total lattice charge in some runs. Those events did not reproduce as persistent pairs under refinement. Increasing easy-axis strength from 30 to 300 on the coarse grid relaxed all three stabilized starts toward the uniform state without producing a qualifying pair.

This is a negative result for the tested smooth starts and undriven relaxation. Seeded survival and spontaneous formation remain distinct outcomes. [Raw runs](../../../results/genesis_v3_formation/)

```powershell
.venv\Scripts\python.exe -B -m src.genesis_v3.formation
.venv\Scripts\python.exe -B -m src.genesis_v3.formation --size 65 --easy-axis 300
```

### Delayed stabilization

Let exchange act alone initially, then switch on the existing sharp-gradient penalty and easy-axis term globally. Seed 22 was selected because its exchange-only run developed two concentrations of opposite charge. This is a candidate selected from the previous data.

On 97×97, switching at time 0.05 to penalty 0.0002 and easy-axis strength 150 produced two distinct resolved cores. Their radius-0.09 disks were disjoint and contained opposite charges of magnitude at least 0.7 at ten consecutive samples, from 0.060 through 0.105. Each reached local charge magnitude about 0.92 while total charge stayed zero. The cores continued approaching, and by time 0.12 the detector found one connected region with local charge near zero. The same timing with easy-axis strength 30 produced no qualifying pair. The coarse strength-150 checks produced qualifying pairs for fewer than three consecutive samples.

The same seed and timing reproduced the qualifying pair on 113×113 for eight consecutive samples, from 0.060 to 0.095. Seeds 8, 9, and 33 produced no qualifying pair under that schedule on 97×97. The result establishes a repeatable case across resolved grids, with the cross-seed criterion still open.

[Quench runs and seed screen](../../../results/genesis_v3_formation_quench/)

```powershell
.venv\Scripts\python.exe -B -m src.genesis_v3.formation --size 97 --seed 22 --duration 0.12 --samples 24 --easy-axis 150 --quench-sample 10
```

## Wall-to-knot conversion

Compare straight, staggered, and necked extended walls under the V3 update. The necked fixture begins with one connected negative-orientation region. One winding of each sign is prepared around its broad lobes. The matched control has the same shape and constant azimuth. The initial twist is prescribed, while the split and any subsequent localization are determined by the field update. This probes conversion of distributed winding into compact objects.

Use the formation detector to require two separate resolved cores, disjoint charge disks, and opposite disk charges of magnitude at least 0.7. Compare the initial maximum disk charge with the post-split charges. The main question is whether the detached cores survive after the bridge disappears on both grid sizes.

The straight strips, one-turn staggered wall, and necked wall relaxed without a qualifying detached pair. In the necked case, the strongest initial disk charge on the 97×97 grid was about 0.22. The stronger staggered wall used 1.35 turns and a stagger of 0.14, starting as a single connected strip with zero net charge. Its initial maximum absolute disk charge was 0.83 on 97×97. It split into a qualifying pair at time 0.015. The two detached cores passed the detector for 13 consecutive samples through 0.075, with local charges reaching approximately ±0.95. The matched unwound staggered wall produced no qualifying cores. The 65×65 run passed for one sample.

This is a test of converting prepared wall winding into compact cores. The strong staggered wall exceeds the initial disk-charge cutoff for the earlier clean-disorder experiment.

The 113×113 check reproduced the split at time 0.015 and retained a qualifying pair for all 18 subsequent samples including the first split sample, through time 0.10. Each final core had a radius of 3.57 cells and local charge magnitude 0.949. The conversion survived refinement. The measured lifetime remained resolution-dependent over the tested window.

[Raw wall runs](../../../results/genesis_v3_wall_conversion/)

```powershell
.venv\Scripts\python.exe -B -m src.genesis_v3.walls --size 97 113 --turns 1.35 --stagger 0.14
```

## Wall formation from disorder

The `--track-walls` option records overlap between connected negative-orientation regions in successive frames. This checks whether two compact cores descend from the same extended region. Overlap is a sampled geometric lineage.

On 97×97, seed 22 began with diffuse regions and a maximum absolute disk charge of 0.625. By time 0.005 two of those regions had joined and developed a nearly downward interior. At time 0.040 the resulting region still spanned roughly half the domain, with a near-zero charge reading around its centroid. At time 0.045 it split into two regions that both overlapped the preceding wall. Their opposite disk charges then increased, passing the pair criterion from time 0.060 through 0.105.

The 113×113 rerun reproduced the half-domain precursor, the shared-parent split at time 0.045, and the first qualifying opposite-charge pair at time 0.060. This establishes the sequence at two resolved grid sizes for the selected start. The independent-start criterion remains open.

For a broader screen on 49×49, tested seed 22 and seeds 24–47 with the same delayed switch at time 0.05. Nineteen of the 25 starts passed the initial disk-charge cutoff. Also tested a second disorder ensemble built by mapping two smooth random fields onto the sphere. Twenty-two of its 24 starts passed the initial cutoff and were evolved with stabilization active from the beginning. Neither coarse screen found a qualifying pair. The three-cell cutoff is more restrictive in physical units on this coarse grid, which also failed to recover the resolved seed-22 result.

[Lineage and screening data](../../../results/genesis_v3_wall_formation/)

```powershell
.venv\Scripts\python.exe -B -m src.genesis_v3.formation --size 97 --seed 22 --duration 0.12 --samples 24 --quench-sample 10 --easy-axis 150 --track-walls
```

### Independent replication

Screened angular and stereographic disorder on 97×97, and a larger angular cohort on 65×65. Seed 59 produced a resolved opposite-charge pair at both 97×97 and 113×113 after a global switch at 0.005. Its cores came from separate regions, so it did not count toward the shared-wall criterion.

Seed 405 passed the shared-wall test on both 97×97 and 113×113. This run used a uniform interior tilt offset of −0.12 in the initialization. Its maximum initial absolute disk charge was about 0.57. The global switch at time 0.015 enabled penalty 0.0002 and easy-axis strength 225. A polarized region spanning about 0.42 domain widths at the switch split into two descendants at time 0.020. Both met the resolved radius, opposite charge, separation, and net charge criteria at four consecutive samples through time 0.035 on both grids. At the endpoint their charge magnitudes were approximately 0.93 and both radii exceeded three lattice cells. Easy-axis strengths 200 and 250 also passed the three-sample minimum on both grids.

Together with seed 22, this meets the two-independent-start criterion for a wall formed from disorder splitting into resolved knots. Seed 405 was selected through screening and its global switch was tuned separately. A common untuned schedule and the frequency of formation under it remain unmeasured.

[97×97 replication](../../../results/genesis_v3_wall_formation/bias_trial_97_405_3_225.json) · [113×113 replication](../../../results/genesis_v3_wall_formation/bias_trial_113_405_3_225.json)

```powershell
.venv\Scripts\python.exe -B -m src.genesis_v3.formation --size 97 113 --seed 405 --duration 0.035 --samples 7 --quench-sample 3 --easy-axis 225 --tilt-bias -0.12 --track-walls
```

## Classical rotational response

Retain the stabilized V3 energy and add a separate conservative evolution for the rotation experiment. With `H = −∂E/∂n`, each orientation evolves by `dn/dt = n × H / h²`. The fixed north perimeter and the energy respect internal rotations around the vertical axis. Under this equation, the axial orientation sum is conserved. The measured axial deficit is `h² Σ(1 − n_z)`, measured relative to the uniform north state. This defines a classical spin variable in the precession model. [Landau–Lifshitz precessing droplets](https://arxiv.org/abs/1111.2310)

Relax a charged seed first. Then use an unforced knot, two opposite polar-angle impulses, and a zero-charge distortion with the same initial vertical profile as the positive impulse. A polar impulse changes axial deficit without prescribing a new azimuth. Measure the phase and normalized coherence of the in-plane pattern relative to its initial shape inside a fixed radius-0.15 disk. Track charge, core radius, energy, and the fraction of the axial deficit inside that disk. Compare grids and halve the time step at fixed resolution. The zero-charge control distinguishes a coherent localized response from generic precession under the added rule.

For the finite-window test, require the two impulses to produce opposite phase shifts relative to the unforced knot, phase shifts above 0.1 radian, coherence above 0.9, retained charge and a resolved core. Check that axial deficit stays localized and that numerical drift in energy and axial deficit is small relative to the applied impulse and the grid-to-grid differences.

### Results

At time 0.025, the unforced knot had rotated by less than 0.0003 radian. The polar-angle impulse that increased the axial deficit produced −0.279 radian of rotation on both grids. The opposite impulse produced +0.561 and +0.565 radian on 97×97 and 113×113. Both kicked knots kept charge −1, a resolved core, and phase coherence above 0.999. About 74–90% of their axial deficit was inside the measurement disk at the endpoint. The matched zero-charge distortion also precessed, but its core disappeared and only about 15% of its axial deficit remained inside the disk.

Axial deficit was conserved to rounding precision in all runs. The largest sampled energy drift in the charged cases was below 0.000005. Halving the step on 97×97 reproduced the reported phases and improved the energy check. The finite-window result supports a classical collective rotation of a localized knot under the added precession law. It does not test quantum spin or exchange of angular momentum between two knots.

[97×97](../../../results/genesis_v3_rotation/rotation_97_0.1.json) · [113×113](../../../results/genesis_v3_rotation/rotation_113_0.1.json) · [Half-step check](../../../results/genesis_v3_rotation/rotation_97_0.05.json)

```powershell
.venv\Scripts\python.exe -B -m src.genesis_v3.rotation
.venv\Scripts\python.exe -B -m src.genesis_v3.rotation --size 97 --factor 0.05
```

## Two-knot axial transfer test

Place two relaxed knots at separation about 0.27 and taper each to the uniform field outside radius 0.125. The initial supports are disjoint. Apply either sign of the polar impulse to the left knot only. Compare against an unforced pair and an isolated positively kicked donor, using the same conservative dynamics.

Measure axial deficit inside radius 0.10 around each core, in fixed disks at the starting centers, and outside the two disks by subtraction. Measure the receiver's phase relative to its initial pattern and subtract the unforced-pair response. Require that both cores retain charge and that the receiver gain is larger than drift and the isolated donor's signal in the empty receiver region. Check agreement between fixed and moving disks, across grid sizes, and with a smaller time step.

### Results

At time 0.035, the negative donor impulse increased the fixed-disk receiver deficit by 0.00156 on 97×97 and 0.00167 on 113×113 relative to the unforced pair. The positive impulse decreased it by 0.00115 and 0.00130. Moving disks reproduced the signs, and the smaller step reproduced the fixed-disk measurements. Receiver phase changed by about −0.19 to −0.21 radians for the negative impulse and +0.34 to +0.37 for the positive impulse. Both cores remained present with half-domain charges within 0.01 of −1. Total axial deficit was conserved to rounding precision within each run.

The isolated negative impulse changed the empty receiver disk by about −0.00010 relative to the unforced isolated knot, opposite in sign and much smaller than the paired response. The negative-impulse receiver still ended below its own initial deficit because the tapered pair preparation radiated strongly even in the unforced run. The field outside the disks carried a substantial part of the difference from the unforced pair. This establishes a reproducible effect on the second knot and leaves a clean net transfer budget open.

[Raw paired and isolated runs](../../../results/genesis_v3_transfer/)

```powershell
.venv\Scripts\python.exe -B -m src.genesis_v3.transfer
.venv\Scripts\python.exe -B -m src.genesis_v3.transfer --size 97 --factor 0.05
```

### Delayed impulse

Evolve the same prepared pair and isolated donor freely to time 0.0175, after the large initial drop in local deficit. Branch the runs from those warmed states. Apply the polar impulse only around the left starting center, with a smooth taper to zero at radius 0.125. Report time since the impulse. Compare the receiver to its own pre-impulse value and to the matched unforced pair. The matched isolated runs estimate how much of the change appears in an empty receiver region.

For the negative impulse, the donor disk lost axial deficit and the receiver gained it relative to both its initial value and the unforced receiver at every sampled time from 0.0275 to 0.03375 in all three runs. At the illustrative common sample 0.030:

| Grid | Donor change | Receiver change | Outside both disks | Receiver gain above unforced | Isolated empty-disk change above unforced |
|---|---:|---:|---:|---:|---:|
| 97×97 | −0.000895 | +0.003756 | −0.002861 | +0.001969 | −0.000113 |
| 113×113 | −0.000975 | +0.003635 | −0.002659 | +0.002076 | −0.000115 |

The first three changes are relative to the start of the post-kick interval and sum to zero to rounding precision. The receiver was outside the kick envelope and shared its initial deficit with the unforced receiver. Both cores stayed distinct and each half retained charge within 0.01 of −1. Tracking the disk centers reproduced the same signs. Halving the 97×97 step changed the tabulated disk values by less than 0.000001. The receiver phase also differed from the unforced run at the common sample. The field outside the core disks participates substantially in the net exchange. The regional balance does not identify a direct, closed transfer between the two disks.

[Delayed 97×97](../../../results/genesis_v3_transfer/delayed_97_0.1.json) · [Delayed 113×113](../../../results/genesis_v3_transfer/delayed_113_0.1.json) · [Half-step run](../../../results/genesis_v3_transfer/delayed_97_0.05.json)

```powershell
.venv\Scripts\python.exe -B -m src.genesis_v3.transfer --delay 0.0175
.venv\Scripts\python.exe -B -m src.genesis_v3.transfer --delay 0.0175 --size 97 --factor 0.05
```

## Driven flyby and spin-state response

The flyby uses precession plus a prescribed transport along the vertical direction of the lattice, with opposite directions on either side of the midline. This sends the two cores past each other. The controls use the same transport and initial profiles with one knot removed. The transport is external to the conservative precession law.

Hold starting positions, charges, and transport fixed. Apply positive, negative, or zero polar impulse to the left knot and independently set the right knot's starting internal phase to zero or π. Track both charge centroids, local axial deficits, and phases. For the right knot, measure transverse deflection relative to the isolated right knot. Compare the change in that deflection across kick conditions at each initial phase. A resolved flyby requires that the vertical ordering reverses while both half-domain charges remain near −1. A spin-state effect should recur on the finer grid. A polar kick also changes the donor profile and the subsequent phase, so this experiment addresses the effect of the prepared state.

### Results

All six paired conditions passed each other on both grids. The sampled closest vertical alignment occurred at time 0.018, and each half-domain charge stayed within 0.017 of −1 throughout. At initial phase π, the receiver's final transverse displacement relative to its solo control was:

| Donor kick | 97×97 | 113×113 |
|---|---:|---:|
| None | −0.000490 | −0.000526 |
| Positive | +0.000303 | +0.000356 |
| Negative | −0.001413 | −0.001388 |

These are signed charge-centroid shifts in domain-width units. Both grids reproduced the sign reversal for the positive kick and the larger inward displacement for the negative kick. The unforced phase-zero receiver moved outward on both grids. At phase zero the positive-kick effect was substantially smaller and more resolution-sensitive than at phase π.

The experiment establishes a kick-dependent deflection in a driven flyby. The left impulse changed axial deficit and profile together. It also changed the phase at closest alignment by about 0.24 or −0.45 radian in the phase-π cases. An encounter matched in phase and profile would be needed to isolate a dependence on axial angular momentum itself.

[97×97 flybys](../../../results/genesis_v3_scattering/flyby_97.json) · [113×113 flybys](../../../results/genesis_v3_scattering/flyby_113.json)

```powershell
.venv\Scripts\python.exe -B -m src.genesis_v3.scattering
```

### Flybys matched at encounter phase

Apply the polar impulse only in the donor annulus from radius 0.065 to 0.125. The resolved core is identical at launch. Keep the same transport and charges. Adjust the receiver's initial internal angle by shooting to target relative phase π at model time 0.018, the closest vertical alignment in the preceding flyby. Report the actual alignment time, the phase residual, each core radius, and the axial deficits at the encounter. Subtract each donor's own solo path and the common solo receiver path.

The phase-matched comparison needs a phase residual below 0.025 radian at the comparison sample, a donor deficit difference that persists to that sample, and reproducible deflection changes at both resolutions. Check core radii at encounter. The full orientation field and its axial deficit are linked, so any residual dependence on the annular shape must remain explicit.

Both grids reached closest sampled alignment at time 0.018 with phase error below 0.014 radian. All paired half-domain charges stayed within 0.005 of −1. The negative impulse reduced the donor's encounter deficit by about 8% and its core radius by about 4–5%. The receiver shifted outward relative to the unforced pair by 0.000258 domain widths on 97×97 and 0.000170 on 113×113, after subtracting solo motion. The positive impulse increased the donor deficit, but the receiver's change relative to the unforced pair reversed sign between resolutions.

The negative branch therefore reproduces under phase matching, while the positive branch remains unresolved. Core size changed during the approach even though the core was identical at launch. The data do not isolate axial angular momentum from changes in the donor profile.

[97×97 matched flybys](../../../results/genesis_v3_scattering/matched_97.json) · [113×113 matched flybys](../../../results/genesis_v3_scattering/matched_113.json)

```powershell
.venv\Scripts\python.exe -B -m src.genesis_v3.matched_flyby
```

## Predicting transverse drift from charge and axial deficit

Apply an axial field `B_z = g x` to a single relaxed knot in the conservative precession model. There is no prescribed transport in this test. The predicted charge-centroid velocity in the continuum, with negligible boundary forces, is `v_y = −g M / (4π Q)`, where `M = ∫(1 − n_z) dx dy` and `Q` is the signed topological charge in the V3 convention. The formula follows from the first moment of topological charge under precession. The axial field contributes `−∫ B_z ∂_x n_z / (4π Q)`, which becomes `−g M / (4π Q)` by integration by parts. This is an established type of skyrmion response in Landau–Lifshitz models. [Komineas and Papanicolaou](https://arxiv.org/abs/1505.04377)

Compute the prediction from the starting field, with no velocity fit. Test zero gradient, reversal, doubling, and reversal of the charge. Separately change the starting deficit with polar impulses under the same gradient. For a pass, require the predicted sign and speed within 5% on both grids for the nonzero-gradient runs, a negligible zero-gradient drift, conserved charge, and a resolved core. Compare the grid-scale charge centroid against the center of the negative-core region in the impulse runs.

### Results

| Condition | 97×97 predicted / measured speed | 113×113 predicted / measured speed |
|---|---:|---:|
| Gradient 150, charge −1 | 0.3872 / 0.3795 | 0.3980 / 0.3901 |
| Gradient −150, charge −1 | −0.3872 / −0.3795 | −0.3980 / −0.3901 |
| Gradient 300, charge −1 | 0.7744 / 0.7443 | 0.7960 / 0.7649 |
| Gradient 150, charge +1 | −0.3872 / −0.3795 | −0.3980 / −0.3901 |
| Gradient 150, increased deficit | 0.5279 / 0.5053 | 0.5422 / 0.5187 |
| Gradient 150, decreased deficit | 0.2662 / 0.2653 | 0.2740 / 0.2731 |

Speeds are charge-centroid displacements over model time 0.03. Every nonzero case passed the 5% bound. The zero-gradient knot remained centered. All runs kept their charge and at least a three-cell core. Halving the time step changed the 97×97 gradient-series speeds by less than 0.000000001. The negative-core centers also moved in the predicted transverse direction in both impulse cases, although the core and charge centroids differed in displacement. Changing the axial deficit predicted the direction and magnitude of the speed change without fitting. The impulse also changed the profile, so the result tests predictive sufficiency in this setting.

[Raw drift and impulse runs](../../../results/genesis_v3_drift/)

```powershell
.venv\Scripts\python.exe -B -m src.genesis_v3.drift
.venv\Scripts\python.exe -B -m src.genesis_v3.drift --impulses
.venv\Scripts\python.exe -B -m src.genesis_v3.drift --size 97 --factor 0.05
```

## Predicting undriven pair motion

Start two relaxed, equal-charge knots at separations 0.19, 0.24, and 0.29, with relative phase zero or π. Combine the profiles by adding their stereographic coordinates so that the tails overlap. Compute the interaction energy by subtracting the energies of the two separately translated knots. Estimate its radial derivative with a centered difference of step `h/4`.

Use the single-knot transverse force law to predict a circular path at angular speed `−U′(d)/(4π Q R)`, with `R` the initial charge-centroid half-separation. Compute all predictions before evolving the fields. Over model time 0.008, compare the trajectories against a stationary pair and the evolution of an isolated translated knot. The finite-window criterion is correct rotation direction and smaller trajectory error than the no-interaction prediction in every resolved configuration on both grids.

All 12 runs passed. The energy model predicted the rotation direction in every case, including reversal when the starting phase changed by π. Over nine samples, the root-mean-square position error of the left charge centroid fell by 51–78% relative to stationary knots and 56–74% relative to the isolated trajectory aligned at its initial position. Both half-domain charges remained within 0.01 of −1 throughout. The model describes the initial orbit over a short window. It assumes fixed separation and phase, and does not establish longer-term orbital stability.

[97×97](../../../results/genesis_v3_free_pair/pair_97.json) · [113×113](../../../results/genesis_v3_free_pair/pair_113.json)

```powershell
.venv\Scripts\python.exe -B -m src.genesis_v3.free_pair
```

## Free travel of an opposite-charge pair

Prepare two separately relaxed knots with opposite winding, combine their stereographic fields, and evolve by conservative precession with no drive. Screen separations and phases on 65×65, then check the phase-zero pair at separation 0.125 on 97×97 and 113×113, plus a wider box at the 97×97 spacing.

For the travel milestone, require two resolved cores with opposite charges throughout, travel after the initial 0.02 of at least three times the largest core extent measured along the direction of motion in that interval, and separation within 15% of its value at time 0.02. Compare average speeds over the latter half of the run and across the refined and widened runs. The travel length is measured against the negative-core footprint along the path. Measuring a dispersion curve and effective mass is a separate test.

The initial 0.105 runs revealed a finite travel window. Late in the unit boxes, the pair neared the fixed boundary, slowed, and spread apart. Widening the 97-grid box delayed the slowdown and reduced the change in separation. The coarse spacing also left individual cores below the three-cell radius cutoff at some samples. Use the common interval 0.020–0.075 identified from these runs for separate confirmation at 129×129 in the unit box and on a width-1.5 box with 113-grid spacing.

| Grid and width | Travel distance | Travel in longitudinal core lengths | Largest separation change | Mean speed, first / second part |
|---|---:|---:|---:|---:|
| 113×113, width 1 | 0.243 | 3.03 | 7.6% | 4.29 / 4.58 |
| 129×129, width 1 | 0.250 | 3.19 | 9.2% | 4.42 / 4.68 |
| 169×169, width 1.5 | 0.230 | 3.22 | 1.6% | 4.17 / 4.19 |

All three retained two cores with radii above three lattice cells and half-domain charges within 0.001 of their respective integers throughout the common interval. The result establishes finite-window undriven travel. The wider run had steadier spacing and speed during that window. The initial long runs show that long-time stability and boundary effects still need to be separated.

[Unit box](../../../results/genesis_v3_dipole/travel_113_0.json) · [Finer grid](../../../results/genesis_v3_dipole/confirmed_129_0.json) · [Wider box](../../../results/genesis_v3_dipole/confirmed_113_28.json)

```powershell
.venv\Scripts\python.exe -B -m src.genesis_v3.dipole --size 129 --separation 0.125 --duration 0.075
.venv\Scripts\python.exe -B -m src.genesis_v3.dipole --size 113 --padding 28 --separation 0.125 --duration 0.075
```

## From wall-born knots to free travel

Replay the previously established formation schedules for seeds 22 and 405. At the first qualifying opposite-charge pair after stabilization switches on, pass the entire field directly from relaxation to conservative precession, retaining the same energy coefficients. Keep the knots, surrounding field, positions, and phases as they were. Compare with the previously verified prepared-pair travel benchmark.

The travel criterion is persistent resolved opposite charges, midpoint travel of at least three initial core diameters, and separation staying within 15% of its starting value. The formation detector requires disjoint charge disks and stops the trial if a pair falls below that criterion. This is a detection endpoint, which can occur before physical annihilation.

For the initial-motion check, compute the charge-center velocity from the precession equation at the handoff and extrapolate linearly for at most 0.01 model time. Compare with fixed starting centers while the pair remains identifiable. This uses the complete field and tests predictability at handoff. An effective law using only the pair's collective properties would require a subsequent test.

**Verdict: failure at the three-diameter travel milestone in the tested window.** At the earliest handoff, all four runs fell below the local charge threshold by time 0.020 after switching, while two cores were still visible at the detection endpoint. Repeated the test with later handoffs, at formation time 0.085 for seed 22 and 0.035 for seed 405. The energy coefficients and full field were preserved across each handoff.

| Seed and grid | Last qualifying time after handoff | Midpoint travel in initial core diameters | Largest change in separation |
|---|---:|---:|---:|
| 22, 97×97 | 0.075 | 0.74 | 1.0% |
| 22, 113×113 | 0.075 | 1.05 | 2.2% |
| 405, 97×97 | 0.0675 | 1.12 | 8.8% |
| 405, 113×113 | 0.0525 | 0.94 | 6.1% |

For mature seed 22, both pairs qualified through the end of the test window. For mature seed 405, the cores approached closely enough that the disjoint-disk detector stopped the test, with opposite-charge cores still visible. The full-field short-time prediction reduced position error against stationary charge centers by about 96–98% in the mature runs. This shows short coherent travel from wall-born knots after a rule switch. It leaves longer travel and a reduced law for the composite open.

[Raw handoff runs](../../../results/genesis_v3_wall_handoff/)

```powershell
.venv\Scripts\python.exe -B -m src.genesis_v3.wall_handoff
.venv\Scripts\python.exe -B -m src.genesis_v3.wall_handoff --mature
```

### Extended mature seed-22 test

The earlier mature runs ended with both knots still qualifying. Their result was inconclusive about travel beyond the original window. Replay the same handoff at 0.085 on 97×97 and 113×113. Add 0.125 domain units of north-aligned padding on each side at handoff, preserving the original field and spacing while moving the boundary outward. This changes the continuation domain, including making the original perimeter interior.

Use a maximum post-handoff time of 0.4 and the original three-diameter target, 15% separation tolerance, and charge and core criteria. Stop at the target, a separation violation, a tracker loss, or a core center coming within 0.09 of the new boundary. Distinguish tracker, boundary, and time limits from a violation of the separation criterion.

Both runs passed. The 97×97 handoff reached 3.03 core diameters at time 0.305, with maximum separation change 1.2%. The 113×113 handoff reached 3.01 diameters at time 0.2175, with maximum change 2.4%. Both retained resolved opposite-charge cores and met the boundary clearance throughout. Travel replicated across grids, with a substantial difference in time to target. This establishes sustained travel for one formation seed under the padded two-stage protocol. Predicting its sustained speed from collective properties remains open.

[Extended 97×97](../../../results/genesis_v3_wall_handoff/extended_97_22.json) · [Extended 113×113](../../../results/genesis_v3_wall_handoff/extended_113_22.json)

```powershell
.venv\Scripts\python.exe -B -m src.genesis_v3.wall_handoff --size 97 --seed 22 --mature --duration 0.4 --padding 12 --travel-gate
.venv\Scripts\python.exe -B -m src.genesis_v3.wall_handoff --size 113 --seed 22 --mature --duration 0.4 --padding 14 --travel-gate
```

### Crossed formation and travel grids

Save the two native seed-22 handoff fields at time 0.085. Evolve each on both 97×97 and 113×113, with equal physical padding of 0.125 on each side. When changing grids, interpolate the orientation components cubically, renormalize the vectors, and keep the physical energy coefficients fixed. Compare mean midpoint speed from post-handoff time 0.020 to 0.075. For a same-source match, require agreement within 5% and a resolved pair throughout that interval.

| Formation grid | Speed on 97×97 | Speed on 113×113 |
|---|---:|---:|
| 97×97 | 0.715 | 0.722 |
| 113×113 | 1.049 | 1.071 |

The same-source comparisons passed with differences of about 0.9% and 2.1%. The roughly 50% difference between native runs largely follows the field produced during formation over this observation window. This does not establish convergence of the formation stage. [Crossed runs and saved fields](../../../results/genesis_v3_wall_handoff/)

### Held-out speed prediction

Use the untested seed-405 handoff at formation time 0.030. Summarize it by the signs of the core charges, core radii, separation and internal phases in the frame of the pair. Reconstruct a trial pair from relaxed isolated-knot templates at the same physical coefficients. Estimate its interaction-energy slope using the same centered difference as the free-pair test. For an opposite-charge pair the predicted transverse midpoint speed is `−U′(d)/(4π)` in the frame directed from negative to positive charge. Write the prediction before evolving the actual pair. Compare mean midpoint velocity over post-handoff time 0.010–0.025. Require speed error within 15% and direction within 30 degrees on both grids.

The direction test passed on both grids. The angle error was 7.0° on 97×97 and 8.3° on 113×113. The speed test failed. Predicted and measured speeds were 1.447 and 1.085 on 97×97 (33.4% high), and 1.230 and 1.204 on 113×113 (2.2% high). The surrogate predicted a lower speed on the finer grid while the observed speed increased. This rejects this specific surrogate at the stated tolerance. Core radius was measured by lattice-cell area, and the surrogate omits the actual core asymmetry and surrounding field. The runs do not identify which approximation caused the discrepancy.

[97×97 forecast](../../../results/genesis_v3_wall_handoff/heldout_prediction_97.json) · [97×97 run](../../../results/genesis_v3_wall_handoff/heldout_result_97.json) · [113×113 forecast](../../../results/genesis_v3_wall_handoff/heldout_prediction_113.json) · [113×113 run](../../../results/genesis_v3_wall_handoff/heldout_result_113.json)

### Core-radius measurement check

Save both seed-405 fields at the same 0.030 handoff and cross the formation and travel grids as for seed 22. For each fixed starting field and grid, predict with both the original whole-cell radius and a subcell radius estimated by sampling the interpolated vertical component eight times per cell along each axis. Use the corresponding radius method for the relaxed template as well. Keep the other inputs and prediction equation fixed. Compare same-source prediction differences across grids and the original 15% speed tolerance. This is a diagnostic on the existing case. A change chosen from these results would need a fresh held-out test.

| Formation → travel grid | Measured speed | Whole-cell forecast error | Subcell forecast error |
|---|---:|---:|---:|
| 97 → 97 | 1.085 | +33.4% | +8.6% |
| 97 → 113 | 1.011 | +8.7% | +16.1% |
| 113 → 97 | 1.173 | +41.1% | +13.4% |
| 113 → 113 | 1.204 | +2.2% | +10.6% |

With the same handoff field, whole-cell forecast speeds differed by approximately 24% and 26% when changing from 97 to 113, relative to the 97 forecasts. The corresponding subcell differences were under 0.4% and 0.1%. Thus the radius measurement, including that of the isolated template, explains most of the original predictor's sensitivity to the travel grid for these starts. It does not explain the remaining systematic overprediction. All four subcell predictions were high, and one exceeded the 15% tolerance. The actual same-source travel speeds differed by about 6.8% and 2.6%, relative to their 97-grid values. A fresh held-out prediction remains necessary.

[Crossed forecasts](../../../results/genesis_v3_wall_handoff/heldout_cross_predictions.json) · [97 → 113](../../../results/genesis_v3_wall_handoff/heldout_cross_97_113.json) · [113 → 97](../../../results/genesis_v3_wall_handoff/heldout_cross_113_97.json)

```powershell
.venv\Scripts\python.exe -B -m src.genesis_v3.pair_speed --compare-grids
```

### Frozen subcell predictor on a new handoff

Test the unchanged subcell predictor on seed 22 at formation time 0.090 on both grids. This handoff was not used in the seed-405 measurement diagnostic or the seed-22 speed comparison at 0.085. It is a new handoff from a previously studied formation seed. Keep the evaluation interval 0.010–0.025 after handoff, the 15% speed tolerance, and the 30° direction tolerance. Save each forecast before evolving the corresponding handoff.

The traveling pair illustrates Koestler's holon concept. Each knot remains a recognizable whole while it participates as a part of a moving composite. The quantitative question here is whether a few properties of those parts predict the motion of the composite. [Koestler's account of holons](https://www.panarchy.org/koestler/holon.1969.html)

Both grids passed the frozen test. On 97×97, predicted and measured speeds were 0.821 and 0.780, with 5.2% speed error and 2.85° direction error. On 113×113, speeds were 1.371 and 1.345, with 1.9% speed error and 0.73° direction error. Both pairs remained resolved throughout the observation window. The two independently formed fields had substantially different speeds, and the same predictor captured each. The result applies to this new handoff of a known seed and a short forecast window.

[97×97 forecast](../../../results/genesis_v3_wall_handoff/subcell_validation_prediction_97.json) · [97×97 run](../../../results/genesis_v3_wall_handoff/subcell_validation_result_97.json) · [113×113 forecast](../../../results/genesis_v3_wall_handoff/subcell_validation_prediction_113.json) · [113×113 run](../../../results/genesis_v3_wall_handoff/subcell_validation_result_113.json)

```powershell
.venv\Scripts\python.exe -B -m src.genesis_v3.pair_speed --validate-subcell
```

### Full travel-window cross-seed test

Freeze the subcell predictor and use the mature seed-405 field at 0.035. This is independent of seed 22, but seed 405 informed the radius diagnostic and the 0.035 handoff was previously evolved briefly. It is not an untouched formation seed. Save the forecast before each extended run. Use the three-initial-core-diameter target, at most 15% separation change, 15% speed error and 30° direction error. Compare the forecast to mean midpoint velocity from handoff to target, with maximum post-handoff time 0.3 and padding 0.125 on each side.

When the two charge disks overlap, assign their shared region to the nearest core, so the charge sums never double count it. Continue to require two resolved opposite-charge cores and the same charge threshold. This changes measurement only.

Both grids passed with the frozen predictor.

| Grid | Travel in initial core diameters | Time to target | Predicted / measured mean speed | Direction error | Maximum separation change |
|---|---:|---:|---:|---:|---:|
| 97×97 | 3.01 | 0.195 | 1.0470 / 1.0576 | 1.54° | 7.8% |
| 113×113 | 3.06 | 0.175 | 1.2443 / 1.2459 | 1.66° | 9.6% |

Both cores remained resolved and oppositely charged. The 113×113 run required partitioning at the endpoint. The result validates the mean velocity over the travel window, with no fit to the trajectory. It does not validate the instantaneous speed at each sample or constitute a blind test on a new seed.

[97×97 forecast](../../../results/genesis_v3_wall_handoff/travel_validation_prediction_97.json) · [97×97 run](../../../results/genesis_v3_wall_handoff/travel_validation_result_97.json) · [113×113 forecast](../../../results/genesis_v3_wall_handoff/travel_validation_prediction_113.json) · [113×113 run](../../../results/genesis_v3_wall_handoff/travel_validation_result_113.json)

```powershell
.venv\Scripts\python.exe -B -m src.genesis_v3.pair_speed --travel-validation
```

## Milestone roadmap

A major milestone answers a question about the Genesis Ladder. A minor milestone prepares a fair test or validates a measurement. Set the pass criteria and limits before the validation runs.

| Major milestone | Pass criterion | Status |
|---|---|---|
| Demonstrate one rung with a handoff | A wall splits into knots that travel together for three core diameters, and their starting properties predict the mean motion after the handoff. | Passed under the two-stage protocol. |
| Demonstrate the rung under one fixed rule | Starting from disordered fields, a wall forms and splits, and those same knots travel together for three core diameters without a rule or parameter switch. Require resolved opposite charges and separation within 15%. Reproduce the sequence on two independent validation seeds and two grid sizes. | Next major milestone. |
| Predict motion under that fixed rule | Freeze a predictor before testing on independent starts held out of its development. Predict mean pair motion over the three-diameter window within 15% for speed and 30° for direction on both grids. | Follows fixed-rule travel. |

Minor milestones for the fixed-rule test, in order:

1. Implement one evolution law with relaxation and precession active from the start. Check its limiting cases against the existing relaxation and precession code.
2. Verify that the tracker follows the same cores from the wall split through travel and distinguishes physical loss of coherence from a measurement limit.
3. Use a bounded exploratory sweep to choose a balance of relaxation and precession. Record which stage fails in each setting.
4. Freeze the rule, parameters, validation seeds, grid sizes, and run limits. Run the validation batch with no retuning.

Use **Success** when the stated criterion passes and **Failure** when a valid test misses it. If the boundary, tracker, or observation limit prevents a decision, report that limit and resolve it where feasible. Failure applies to the tested rule and conditions.

### Fixed-rule exploration

Use a constant Landau–Lifshitz precession term plus tangent relaxation from the start. The strength of precession is one. The relaxation coefficient, sharp-gradient penalty, and easy-axis energy are held fixed throughout each run. The exploratory sweep uses seeds 22 and 405 with their previously studied starting biases. It compares relaxation coefficients 0.25, 0.75, and 2 at easy-axis strengths 150 and 225 respectively, plus strength 70 at relaxation 0.75. The 65×65 screen is for ranking candidates and identifying failure stages. It cannot settle the resolved-grid milestone.

Track overlap between consecutive negative-core components. A candidate pair must share an earlier polarized extended region as an ancestor, and the initial field must pass the original zero-net-charge and disk-charge checks. The travel gate still requires three initial core diameters, resolved opposite charges, and separation within 15%.

### Fixed-rule results

The coarse screen produced no qualifying wall-born pair. The initial exploratory integrator showed small orientation-length drift, so the resolved runs normalize after each damped step. The conservative zero-damping path is unchanged. In the pure relaxation limit, halving a small step reduced its difference from the original projected relaxation update by about a factor of four.

Seed 405, with relaxation 0.75 and easy-axis strength 225, produced a qualifying wall-born pair on both 97×97 and 113×113. The 97×97 run lost tracking after one core fell below the resolution cutoff. On 113×113 the resolved pair exceeded 15% separation change at time 0.050, after traveling 0.13 core diameters. Halving the time step reproduced this result. Lowering the easy-axis strength to 180 also exceeded the separation limit on 113×113.

To distinguish initial maturation from loss of stable spacing during travel, ran a separate check at the same fixed settings, starting the measurement only once both local charge magnitudes exceeded 0.90. On 113×113 and 129×129, the two cores still approached until their spacing fell by 16.7% and 17.4% after only 0.17 and 0.19 diameters of travel. Both were still resolved when the spacing criterion failed. This rules out the tested setting for the stated travel criterion. No setting qualified for the independent-seed validation batch.

[Raw fixed-rule runs](../../../results/genesis_v3_fixed_rule/)

```powershell
.venv\Scripts\python.exe -B -m src.genesis_v3.fixed_rule --size 113 --seed 405 --bias -0.12 --damping 0.75 --easy-axis 225 --duration 0.14 --mature-charge 0.9
```

### Same-field damping diagnostic

Capture the mature seed-405 field at the first sample where both local charge magnitudes reach 0.90 under the fixed rule. Branch that exact field into continuations with damping 0.75 and zero. Keep the energy, precession coefficient, boundaries, time step, and charge tracker matched. Measure separation over 0.04 after the branch. The decisive comparison is whether removing damping prevents the 15% spacing violation seen in the original fixed-rule run while both cores remain resolved. This experiment isolates the role of ongoing damping and does not qualify as a fixed-rule formation and travel run.

| Grid | First 15% violation, damping on / off | Final spacing loss, damping on / off |
|---|---:|---:|
| 113×113 | 0.0275 / 0.0325 | 25.9% / 30.9% |
| 129×129 | 0.0275 / 0.0200 | 27.7% / 33.2% |

Both branches started with identical measurements and retained two qualifying cores through time 0.04. The conservative branches kept energy within about 10⁻¹¹ at the endpoint. Turning damping off did not prevent contraction, and its effect on the time of first crossing was inconsistent across grids. This rules out removing ongoing damping as a sufficient remedy for these formed fields. It does not determine whether pair geometry, internal phase, or the surrounding field drives contraction.

[113×113 comparison](../../../results/genesis_v3_fixed_rule/damping_comparison_113.json) · [129×129 comparison](../../../results/genesis_v3_fixed_rule/damping_comparison_129.json)

```powershell
.venv\Scripts\python.exe -B -m src.genesis_v3.damping_diagnostic --size 113
.venv\Scripts\python.exe -B -m src.genesis_v3.damping_diagnostic --size 129
```

### Pair-region and background swap

Compare the successful seed-405 staged handoff at 0.035 with the contracting seed-405 fixed-rule handoff saved by the damping diagnostic. Use conservative precession and identical energy coefficients for all continuations. On each grid, pad both fields by 0.125 per side. Keep the native fields as controls. In each reciprocal swap, translate the donor patch by an integer number of cells to align the pair midpoints, copy the disk of radius 0.22 exactly, and blend into the recipient field between radii 0.22 and 0.29. The patch includes the two cores, their relative orientation and spacing, and their nearby field.

Compare the 15% spacing criterion over time 0.04 with both pairs resolved. If the reciprocal swaps follow the donor patch on both grids, that implicates the pair region. If they follow the recipient field, that implicates the surroundings. Mixed or resolution-sensitive outcomes leave the distinction open. Translation and blending can affect the field, so this comparison cannot isolate a single property inside the patch.

The padded native contracting control failed to reproduce the original contraction. Its spacing increased by about 8–9% by time 0.04, whereas the original unpadded conservative continuations contracted by about 31–33%. This prevents attribution from the padded swaps. Repeat on the original unit domain with the blending weight smoothly reduced to zero within 0.035 of the fixed edge.

On the unit domain, both native controls reproduced their contrasting behavior. The traveling pair stayed within 4.5% of its initial separation. The contracting pair closed by 31–33%. Moving the contracting pair region into the traveling field preserved both cores through 0.04, with maximum spacing change below 2.9% on both grids. In the reverse swap, two-core tracking ended at 0.025 on 113×113 and 0.030 on 129×129. The finer run exceeded the 15% spacing limit before tracking ended.

The pair region alone is insufficient to predict the outcome. The surrounding field or the location relative to the fixed boundary matters in these comparisons. The reciprocal swaps alter both, and the blend changes the transition region. The tracking endpoints do not by themselves demonstrate annihilation.

[113×113 original domain](../../../results/genesis_v3_fixed_rule/pair_swap_113_fixed_boundary.json) · [129×129 original domain](../../../results/genesis_v3_fixed_rule/pair_swap_129_fixed_boundary.json) · [Padded controls](../../../results/genesis_v3_fixed_rule/pair_swap_113.json)

```powershell
.venv\Scripts\python.exe -B -m src.genesis_v3.pair_swap --size 113
.venv\Scripts\python.exe -B -m src.genesis_v3.pair_swap --size 129
```

### Surroundings probe outcome and next decision

At fixed core positions and boundary, smoothing the exterior toward north reduced the contraction at time 0.04 from 30.9% to 16.0% on 113×113 and from 33.2% to 16.4% on 129×129. Both quiet runs retained two resolved cores and still exceeded the 15% separation limit. The exterior azimuth rotation produced a tracking limit on 113×113 and an 8.7% endpoint contraction on 129×129. It did not provide a reproducible remedy.

The next diagnostic is to track the spatial first moment of topological charge for the whole field and separately for the core regions and exterior. For opposite charges, the core contribution approximately tracks their separation vector. In translation-invariant continuum precession the full first moment is related to conserved impulse. On the finite lattice it can also change through boundary and discretization effects. If core impulse moves into the exterior while the total remains nearly fixed, the surrounding field is carrying the change. If total impulse drift depends strongly on boundary distance, investigate confinement before adding a new local feedback rule. [Conservative vortex-pair impulse and confinement](https://www.nature.com/articles/srep15773)

[113×113 exterior probe](../../../results/genesis_v3_fixed_rule/halo_probe_113.json) · [129×129 exterior probe](../../../results/genesis_v3_fixed_rule/halo_probe_129.json)

### Charge-moment budget

On both grids, repeat the native and quiet-exterior continuations and add a widened native continuation. Widen by adding 0.125 units of north-aligned padding on every side, keeping the original field and lattice spacing intact. Sum the spatial first moment of geometric charge over the whole box, the union of the two radius-0.09 disks, and the exterior. Project each change onto the initial core moment direction, so a negative core change represents a reduction in the pair contribution along its initial axis. The projection and partition are diagnostics. The remainder can include diffuse charge and changes at the moving disk boundaries. The finite lattice and fixed perimeter can change the full moment.

| Grid and continuation | Core change | Exterior change | Total change |
|---|---:|---:|---:|
| 113×113, native | −0.0452 | −0.0520 | −0.0972 |
| 113×113, quiet | −0.0343 | −0.0024 | −0.0367 |
| 113 spacing, widened | −0.0248 | +0.0100 | −0.0148 |
| 129×129, native | −0.0430 | −0.0546 | −0.0976 |
| 129×129, quiet | −0.0347 | −0.0030 | −0.0377 |
| 129 spacing, widened | −0.0234 | +0.0085 | −0.0150 |

All branches retained a qualifying pair through time 0.04. Native contraction is not a balanced transfer from cores to exterior along the measured axis. Both contributions decrease. Quieting the exterior reduces total drift by about 61–62%. Widening reduces it by about 85%, and the exterior partly offsets the core decrease. This identifies sensitivity to the exterior and the finite-domain continuation. Padding makes the original edge interior, so it does not isolate a boundary flux from the effect of changing the surrounding field. A fixed-rule run with the wider domain in place from initialization is the next control.

[113×113 budget](../../../results/genesis_v3_fixed_rule/impulse_budget_113.json) · [129×129 budget](../../../results/genesis_v3_fixed_rule/impulse_budget_129.json)

```powershell
.venv\Scripts\python.exe -B -m src.genesis_v3.halo_probe --size 113 --impulse-budget
.venv\Scripts\python.exe -B -m src.genesis_v3.halo_probe --size 129 --impulse-budget
```

### Wider domain from initialization

Initialize the north-aligned padding before evolving the disordered seed-405 field, rather than adding it after formation. Retain the original interior and grid spacing, with 0.125 of padding on each side. Use damping 0.75, easy-axis strength 225, and the prior gradient penalty throughout. Begin measuring travel when the two wall descendants both reach a local charge magnitude of 0.90. Keep the same three-diameter target, resolved-core and charge criteria, and 15% separation limit. Run both spacings through the first observation window of 0.14 unless a gate is reached sooner. A pair still qualifying at the time limit warrants a longer continuation.

**Failure for this fixed rule.** Both extended runs formed a resolved wall-born pair by time 0.030. The pairs contracted past the spacing limit while both local charges still had magnitude about 0.96.

| Interior grid | Padded grid | Time at spacing violation | Travel in core diameters | Separation loss |
|---|---|---:|---:|---:|
| 113×113 | 141×141 | 0.225 | 0.344 | 15.64% |
| 129×129 | 161×161 | 0.215 | 0.337 | 15.39% |

Compared with the original unit-domain runs, widening roughly doubled the distance before spacing failure. Both pairs still fell far short of three diameters. Seed 405 was an exploratory seed, and the rule did not qualify for independent-seed validation. The extended runs used a compiled RK4 step whose maximum absolute difference from the NumPy step was 4.6 × 10⁻¹⁶ after a 1,000-step comparison on a 65×65 field. The commands below reproduce the setup with the NumPy implementation and the extended sampling interval of 0.005.

[113-spacing extended run](../../../results/genesis_v3_fixed_rule/widened_fixed_extended_113_405.json) · [129-spacing extended run](../../../results/genesis_v3_fixed_rule/widened_fixed_extended_129_405.json)

```powershell
.venv\Scripts\python.exe -B -m src.genesis_v3.fixed_rule --size 113 --padding 14 --seed 405 --bias -0.12 --damping 0.75 --easy-axis 225 --duration 0.45 --mature-charge 0.9
.venv\Scripts\python.exe -B -m src.genesis_v3.fixed_rule --size 129 --padding 16 --seed 405 --bias -0.12 --damping 0.75 --easy-axis 225 --duration 0.45 --mature-charge 0.9
```

### Can the fixed rule sustain a known traveling pair?

Replay the seed-405 staged handoff at formation time 0.035 on 97×97 and 113×113. On each grid, copy the same full field into two branches with 0.125 of north-aligned padding per side. Keep precession, the gradient penalty, easy-axis strength, timestep, and nearest-core partition of overlapping charge disks matched. The only change after handoff is damping, zero in the control and 0.75 in the fixed-rule branch. Require the existing three-diameter travel and 15% spacing limits with both cores resolved. Cap observation at 0.3 after handoff. This diagnostic tests sustainment from a staged field.

**Failure for sustainment at damping 0.75.** On both grids the damped pair was still resolved when its spacing fell below the limit. At those same elapsed times the conservative pair had contracted by less than 0.34% on either grid. Both fresh conservative replays matched the archived trajectories exactly.

| Grid | Conservative travel at pass | Damped travel at failure | Damped spacing loss | Damped failure time after handoff |
|---|---:|---:|---:|---:|
| 97×97 | 3.009 diameters | 0.293 diameters | 18.12% | 0.0175 |
| 113×113 | 3.061 diameters | 0.293 diameters | 18.35% | 0.0150 |

Together with the earlier damping diagnostic, this identifies two separate problems. Removing damping from the fixed-rule-formed pair did not rescue its spacing. Adding damping to the staged pair prevented travel even when it started from a field already known to support it. The test concerns damping 0.75 and the seed-405 handoff.

[97×97 damped branch](../../../results/genesis_v3_fixed_rule/known_pair_97_damping_0.75.json) · [113×113 damped branch](../../../results/genesis_v3_fixed_rule/known_pair_113_damping_0.75.json) · [97×97 conservative control](../../../results/genesis_v3_wall_handoff/travel_validation_result_97.json) · [113×113 conservative control](../../../results/genesis_v3_wall_handoff/travel_validation_result_113.json)

```powershell
foreach ($size in 97, 113) {
    foreach ($damping in 0, 0.75) {
        .venv\Scripts\python.exe -B -m src.genesis_v3.wall_handoff --size $size --seed 405 --mature --padding (($size-1)/8) --duration 0.3 --travel-gate --partition-overlap --damping $damping
    }
}
```

### Conservative formation and energy transport

Distinguish uniform damping, which removes energy from the model, from conservative transport, which can move energy out of a forming structure into the surrounding field. Replay seed 405 with the same widened initial domain, bias −0.12, easy-axis strength 225, and gradient penalty 0.0002. Activate all conservative terms at initialization and keep damping at zero. Observe through time 0.14 on both grid spacings. Keep the wall lineage, charge, spacing, and travel criteria from the fixed-rule test. Extend a qualifying pair if it reaches the time limit before a gate.

Sum the original model energy and partition it spatially by assigning half of each bond's energy to each endpoint. Record the energy in the padding and, once a qualifying pair appears, in a fixed radius-0.22 disk centered at its first midpoint. Padding energy measures redistribution. It does not by itself identify radiation specifically emitted by a wall. A decrease in the fixed disk can also include energy carried by a pair leaving the disk. The outer perimeter is fixed, so waves can reflect.

**Failure for the tested conservative start.** Wall-like regions appeared on both grids, but neither run produced a qualifying neutral wall-born pair through time 0.14. Energy reached the padding despite zero explicit damping. With no qualifying pair, the run provides no evidence of a pair settling through radiation.

| Interior grid | Padding energy at 0.14 as share of initial total | Maximum relative total energy drift | First sampled charge change |
|---|---:|---:|---:|
| 113×113 | 31.63% | 0.52% | 0 → +1 at 0.001375 |
| 129×129 | 30.36% | 0.69% | 0 → +1 at 0.001375 |

The full runs used a compiled version of the same RK4 step with maximum absolute orientation difference of 5.8 × 10⁻¹² from NumPy after 1,000 conservative steps on a 65×65 field. An early replay through time 0.005 sampled charge every 0.000125 and reproduced the jump on both grids when the timestep was reduced by a factor of about four. Net charge was near +1 at every later sample in the full runs. This rules out the original timestep as the simple explanation for the jump. It leaves open whether the lattice permits a change through an unresolved texture or the corresponding continuum evolution becomes singular. The charge criterion rules out tracking a qualifying neutral pair after that jump.

[113-spacing run](../../../results/genesis_v3_fixed_rule/conservative_113_405.json) · [129-spacing run](../../../results/genesis_v3_fixed_rule/conservative_129_405.json) · [113-spacing early charge check](../../../results/genesis_v3_fixed_rule/conservative_charge_check_113.json) · [129-spacing early charge check](../../../results/genesis_v3_fixed_rule/conservative_charge_check_129.json)

```powershell
foreach ($size in 113, 129) {
    .venv\Scripts\python.exe -B -m src.genesis_v3.fixed_rule --size $size --padding (($size-1)/8) --seed 405 --bias -0.12 --damping 0 --easy-axis 225 --duration 0.14 --mature-charge 0.9 --step-factor 0.02 --energy-regions
}
```

### Location of the first conservative charge jump

Replay the early conservative interval and compare individual oriented triangle charges at adjacent integration steps bracketing the first whole-field jump. Report coordinates in the original unit square, excluding the padding offset. Repeat with half the integration step. As a measurement control, recompute charge on the same evolved fields with the opposite diagonal in every plaquette.

**Success.** One interior triangle accounted for the jump on each grid. The triangle contribution went from approximately −0.5 to +0.5 as the numerator of its solid-angle formula changed sign with a negative denominator. At both spacings the nearly opposed directions were on the plaquette diagonal, which has no direct bond in the current energy. The jump stayed in the same cell on each grid after halving the timestep.

| Interior grid | Triangle centroid in the original square | Time bracket at the smaller step | Diagonal angle before jump |
|---|---|---|---:|
| 113×113 | (0.67262, 0.39881) | 0.001327428–0.001327627 | 168.9° |
| 129×129 | (0.66667, 0.39583) | 0.001310366–0.001310518 | 170.4° |

Both diagonals measured net charge near zero at 0.00125 and near +1 at 0.001375 on both grids. The alternate-diagonal control establishes agreement across that sampled interval. It does not identify the alternate crossing at individual integration steps. The location and angular separation indicate a loss of smoothness within one lattice cell, about one-third of the original box width from its edge. The result does not establish a continuum singularity or show that the absent diagonal bond caused the event.

[Step-by-step event geometry](../../../results/genesis_v3_fixed_rule/conservative_charge_location_405.json) · [Alternate diagonal control](../../../results/genesis_v3_fixed_rule/conservative_charge_diagonal_405.json)

### Symmetric diagonal penalty screen

Replay seed 405 on the two padded grids with zero damping and easy-axis strength 225. Compare the original cardinal quartic penalty of 0.0002, a cardinal-only increase to 0.00025, and the original cardinal penalty plus 0.0000125 on both diagonal bond directions. All coefficients are divided by the squared grid spacing in the integrator. Diagonal bonds are √2 times as long as cardinal bonds, so their length to the fourth power is four times as large. With two directions in each set, using one quarter of the cardinal increment matches the orientation-averaged leading quartic energy increment for smooth fields. At cell-scale gradients the two interventions intentionally differ.

Sample whole-field charge every 0.000125 through time 0.01 with both plaquette triangulations. Check wall candidates every 0.0005. The screen requires charge to remain within 0.01 of zero and a wall candidate to appear. A rule that passes the screen earns an extended formation and travel test with the same parameters. A later charge jump still fails the neutrality criterion.

**Failure across grids.** All six branches formed wall candidates by time 0.0005. Both added penalties kept the finer grid neutral throughout the window, but both made the coarser grid lose neutrality one sample earlier than the original rule. The two triangulations agreed in every branch about the first sampled jump or its absence. The result shows sensitivity to grid spacing and gives no evidence that this diagonal penalty has a distinct advantage over the matched cardinal increase. Neither modification passed the screen on both grids, so neither advanced to the travel test.

| Interior grid | Original | Stronger cardinal penalty | Diagonal penalty |
|---|---:|---:|---:|
| 113×113 | +1 at 0.001375 | +1 at 0.001250 | +1 at 0.001250 |
| 129×129 | +1 at 0.001375 | Neutral through 0.01 | Neutral through 0.01 |

The compiled diagonal step matched the NumPy reference to a maximum absolute orientation difference of 6.94 × 10⁻¹⁴ after 1,000 steps on 65×65. Maximum relative energy drift was below 4 × 10⁻⁷ in all six runs. This was one exploratory seed and one matched penalty increment. The comparison does not settle neutrality under other coefficients or finer spatial resolution.

[113 original](../../../results/genesis_v3_fixed_rule/diagonal_screen_113_original.json) · [113 cardinal](../../../results/genesis_v3_fixed_rule/diagonal_screen_113_cardinal.json) · [113 diagonal](../../../results/genesis_v3_fixed_rule/diagonal_screen_113_diagonal.json) · [129 original](../../../results/genesis_v3_fixed_rule/diagonal_screen_129_original.json) · [129 cardinal](../../../results/genesis_v3_fixed_rule/diagonal_screen_129_cardinal.json) · [129 diagonal](../../../results/genesis_v3_fixed_rule/diagonal_screen_129_diagonal.json)

### Grid refinement of the cardinal penalty

Repeat the original and stronger cardinal penalties from the diagonal screen on 161×161 and 193×193 interior grids, with 0.125 of padding per side. Keep the seed-405 disorder construction, coefficients, physical domain, and sampling schedule fixed. Require a wall candidate and whole-field charge within 0.01 of zero throughout time 0.01 under both triangulations. The stronger penalty advances to the formation and travel test only if both finer grids meet the screen. Agreement over this interval establishes the screen outcome at these spacings. It cannot establish convergence at later times.

Both penalties passed the early screen on both finer grids. All four runs formed wall candidates by time 0.0005, and both triangulations measured neutral charge at every sample through 0.01. The original penalty also passed, so the stronger penalty is unnecessary for this early result at these spacings. The early jump in the coarser runs is therefore sensitive to spatial resolution.

[161 original](../../../results/genesis_v3_fixed_rule/diagonal_screen_161_original.json) · [161 stronger](../../../results/genesis_v3_fixed_rule/diagonal_screen_161_cardinal.json) · [193 original](../../../results/genesis_v3_fixed_rule/diagonal_screen_193_original.json) · [193 stronger](../../../results/genesis_v3_fixed_rule/diagonal_screen_193_cardinal.json)

Replay the stronger penalty from the same initial conditions on both finer grids through time 0.14, using a dimensionless step factor of 0.01. Keep the fixed-rule formation and travel criteria. Stop if a sampled charge measurement loses neutrality. This longer test samples at roughly 0.005 intervals and does not resolve short charge excursions between samples.

On 161×161, a qualifying pair appeared at time 0.057931. The next sample recorded 0.118 diameters of midpoint travel and a 1.53% separation change. At 0.067586 the negative core's connected region merged with a much larger region, ending tracking. Net charge stayed within 1.25 × 10⁻⁵ of zero. An independent disk readout at the last tracked negative-core center still measured −1.022 at the merge sample. The nearby disk search found −1.054. These observations show localized negative charge survived the tracking endpoint. They do not establish later pair motion. The replay's archival check compared tuples with JSON lists and interrupted report writing after the three measurements printed. The linked report preserves those printed measurements.

[161 extended run](../../../results/genesis_v3_fixed_rule/refined_cardinal_extended_161_405.json) · [161 local charge replay](../../../results/genesis_v3_fixed_rule/refined_cardinal_core_check_161_405.json)

On 193×193, net charge remained within 4.19 × 10⁻⁶ of zero through time 0.14 and wall candidates remained present. The selected opposite-charge pairs with shared wall ancestry fell short of the 0.90 minimum local charge. For example, at 0.028966 the local charges were −0.869 and +0.825. No qualifying pair entered the travel test on this grid. Maximum relative energy drift was 0.0224% on 161×161 and 0.0863% on 193×193.

**The fixed-rule milestone remains unmet.** Refinement removed the observed early loss of neutrality, but did not yield reproducible formation of a mature pair across these grids. The 161×161 travel observation ended at a tracker limit, with negative charge still localized at the endpoint. The 193×193 result failed the formation criterion in the stated window. These are exploratory outcomes on seed 405.

[193 extended run](../../../results/genesis_v3_fixed_rule/refined_cardinal_extended_193_405.json)

```powershell
foreach ($size in 161, 193) {
    .venv\Scripts\python.exe -B -m src.genesis_v3.fixed_rule --size $size --padding (($size-1)/8) --seed 405 --bias -0.12 --damping 0 --easy-axis 225 --duration 0.14 --mature-charge 0.9 --step-factor 0.01 --cardinal-penalty 0.00025 --require-neutrality --energy-regions
}
```

### Local charge tracking through a region merge

Replay the 161×161 run with the stronger cardinal penalty and save the full field at its first mature wall-born pair. Keep the integration step, equation, three-diameter travel target, original separation and diameter, and 15% separation tolerance. Between the original observations, follow each sign's local charge peak within 0.025 of its previous center. Compare peak positions from two disk smoothing radii, three and five cells, and require resolved opposite charges in radius-0.09 disks with overlap assigned to the nearer center. Treat a search-edge hit, a disagreement greater than 0.025 between the two peak measurements, or loss of qualifying local charge as a tracking limit. A spacing failure requires both peak measurements to cross the limit in the same direction. This is a diagnostic of the archived candidate at one resolution.

The formation replay matched the archived trajectory exactly. The peak tracker stopped at time 0.059137 after a one-sample center move of 0.022535, while both charge magnitudes were still above 0.98. From the same saved field, a second tracker measured signed charge centroids with Gaussian scales of 0.01875 and 0.025, restricted to 0.055 around the previous center. At time 0.067581, approximately the original region-merge time, both centroid estimates gave 0.18 diameters of travel and 1.6–1.8% separation change. Both cores still exceeded the 0.7 local charge magnitude requirement.

**Inconclusive for travel.** At time 0.069993 the two centroid-centered disks measured negative charges of −0.689 and −0.669, below the qualifying magnitude. A radius-0.09 disk within 0.03 of the centroid estimates still contained −0.876. The result depends on center placement at that sample. It establishes that the region merge did not immediately end the tracked pair and that the later centroid limit does not establish disappearance of the negative charge. Neither tracker followed an identified pair for three diameters.

[Peak tracker](../../../results/genesis_v3_fixed_rule/refined_cardinal_charge_track_161_405.json) · [Centroid tracker and endpoint check](../../../results/genesis_v3_fixed_rule/refined_cardinal_charge_centroid_161_405.json) · [Formation checkpoint](../../../results/genesis_v3_fixed_rule/refined_cardinal_pair_checkpoint_161_405.npz)

### Charge concentration through the merge

Track the centers of the most concentrated nearby same-sign charge using radius-0.045 disks and a continuity penalty. Measure the fraction of same-sign charge mass within radius 0.045 relative to radius 0.09, with overlapping outer disks partitioned by nearest center. Also record the signed charge in both disks so a high fraction cannot hide a loss of absolute charge. Calibrate on the mature seed-405 staged 113×113 control before applying the measurement to the saved 161×161 candidate. The control replay tracked 3.065 diameters, with a maximum available center discrepancy of 0.01023 against the archived region tracker. The provisional concentration floor was 0.605, or 90% of the lowest value observed on the control.

The 161×161 positive knot was already below the control floor at launch, so that floor cannot diagnose dispersal at the merge. Replayed the candidate without stopping at that floor and retained the original charge, spacing, and travel criteria. The negative knot's concentration fraction fell from 0.707 at launch to 0.498 near the merge and 0.462 one sample later. Over that interval the signed inner-disk magnitude fell from 0.758 to 0.568 and then 0.481, while the outer disk still contained magnitude 0.950 at the last of those samples. The positive knot became more concentrated over the same interval. At time 0.069997 the selected negative disk fell below the 0.7 outer charge threshold. The earlier centroid replay found a nearby disk with magnitude 0.876 at essentially the same time, so the endpoint remains sensitive to center placement.

**Inconclusive for sustained travel.** The tracked negative patch broadened around the merge by this concentration measure. Local negative charge persisted, and the diagnostic could not establish whether a single compact knot survived. The candidate supplied no three-diameter trajectory. Close this tracking diagnostic and return to reproducible formation across grids.

[Known traveling control](../../../results/genesis_v3_fixed_rule/refined_compactness_control_113.json) · [Control-floor comparison](../../../results/genesis_v3_fixed_rule/refined_compactness_candidate_161.json) · [Merge replay](../../../results/genesis_v3_fixed_rule/refined_compactness_merge_161.json)

### Reciprocal strain-wave interaction

Add a scalar displacement and its velocity at each site of a separate V3 experiment. Keep the orientation field and its precession. The shared interaction energy is \(-g h^2 \sum u(1-n_z^2)\). The orientation drives the strain through the source \(g(1-n_z^2)\), and strain changes the axial effective field by \(-2h^2 g u n_z\). Use a fixed north perimeter for orientation and zero displacement at the strain perimeter. Wave speed is 35, the on-site frequency is 100, and coupling is 600 in model units. These are exploratory choices.

Use two prepared knots. The wave branch starts with zero strain velocity and the strain profile in equilibrium for the undisturbed orientation. Perturb only the left knot in the kicked branch. Compare the kick-minus-rest receiver response in three modes. The uncoupled mode uses the original orientation dynamics, the instantaneous mode recomputes the equilibrium strain at every integration stage, and the wave mode evolves strain and orientation jointly. This tests interaction between existing knots. The formation milestone requires a separate test.

Measure receiver strain RMS, the phase of the transverse orientation, and the centroid of signed charge in a fixed receiver disk. Test through time 0.018. Require resolved receiver charge, similar effects on both grids, and a displacement difference from both controls that exceeds timestep sensitivity. Check when the differences become appreciable relative to the strain signal. The lattice supports small precursors, and the instantaneous control responds through an elliptic solve, so first nonzero floating-point readings are not an arrival criterion.

The additional blocked control evolves the kicked orientation under the exact strain history from the unperturbed wave branch, including the Runge–Kutta stages. It retains the background strain and the direct orientation interaction while removing the kick-induced change in strain. It is a prescribed-field control with no closed-system energy conservation requirement. Report arrival as the first sample at 1% of peak receiver strain, and response onset as the first sample at 1% of peak wave-versus-blocked displacement. These thresholds summarize the measured signal and do not define a sharp causal front.

| Grid | Strain arrival | Response onset | Peak shift versus uncoupled | Versus instantaneous | Versus blocked |
|---|---:|---:|---:|---:|---:|
| 65×65 | 0.0035 | 0.0045 | 8.17 × 10⁻⁶ | 5.29 × 10⁻⁶ | 9.53 × 10⁻⁶ |
| 81×81 | 0.0040 | 0.0045 | 1.03 × 10⁻⁵ | 5.92 × 10⁻⁶ | 1.12 × 10⁻⁵ |

**Success for the prepared-knot interaction test.** The dynamic field induced a small additional shift in the receiver's charge centroid on both grids. The blocked difference before the operational arrival was about 0.1% of its peak. The receiver retained local charge magnitude above 0.92 and wave-branch relative energy drift stayed below 8 × 10⁻⁵ at the smaller step. The displacement is about 1–1.5% of the uncoupled kick response. The two grids agree on the effect's timing and scale, with some difference in amplitude. The centroid records a change in the receiver's charge distribution. It can include deformation of the knot as well as translation. This experiment does not test formation or identify the coupling with a physical force.

Halving the timestep changed each displacement contrast by less than 1% of its peak. For the blocked contrast the maximum absolute change was below 6.6 × 10⁻⁹ on both grids. No ambiguous charge triangles were observed in any branch.

[65×65 run](../../../results/genesis_v3_strain_wave/screen_65.json) · [65×65 smaller-step run](../../../results/genesis_v3_strain_wave/check_65.json) · [81×81 run](../../../results/genesis_v3_strain_wave/screen_81.json) · [81×81 smaller-step run](../../../results/genesis_v3_strain_wave/check_81.json)

```powershell
foreach ($size in 65, 81) {
    .venv\Scripts\python.exe -B -m src.genesis_v3.strain_wave --size $size --step-factor 0.04 --output "results/genesis_v3_strain_wave/check_$size.json"
}
```

### Which knot drives the contraction?

Reconstruct each signed core's trajectory from the saved swap and exterior-probe runs. Project the displacement onto the initial line joining the cores and its perpendicular. Report the along-line component as inward speed for each knot, with negative values indicating motion away from the other knot. Compute spacing change separately from the actual distance. No dynamics were changed in this analysis.

| Pair and surroundings | Time window | Negative knot inward speed, 113 / 129 | Positive knot inward speed, 113 / 129 |
|---|---|---:|---:|
| Native traveling | 0.02–0.04 | 0.014 / 0.041 | 0.178 / 0.223 |
| Native contracting | 0.01–0.02 | 1.087 / 1.039 | 1.713 / 1.854 |
| Native contracting | 0.02–0.04 | −0.836 / −0.662 | 2.772 / 2.854 |
| Contracting pair, quieted exterior | 0.02–0.04 | 0.109 / 0.142 | 0.953 / 0.944 |
| Contracting pair in traveling surroundings | 0.02–0.04 | 0.039 / 0.090 | 0.109 / 0.124 |

Both knots moved inward during the initial strong contraction. Later the positive knot closed the gap even as the negative knot moved away along the initial axis. Quieting the exterior at the original position reduced that late positive-knot inward speed by about two thirds on both grids. The traveling background reduced it further in the swap. The native traveling knots also had closely matched transverse speeds over 0.02–0.04. In the reverse swap the traveling pair acquired early inward motion before tracking ended, so the late interval is unavailable for that branch. These are measured velocities of the tracked centers. The fixed-position exterior intervention implicates the surroundings, while neither intervention isolates a particular torque or proves that the effect is tied to the charge sign.

[Velocity decomposition](../../../results/genesis_v3_fixed_rule/pair_swap_velocity_comparison.json)

### Charge reversal at fixed core positions

Reflect the transverse orientation about one common axis inside the radius-0.10 tube around the segment joining the cores. This reverses both windings while retaining the axial orientation inside the tube. Blend the reflected texture back to the original exterior between radii 0.10 and 0.155. Require resolved opposite charges at the reversed sites, both positions within one cell of their original locations, and a minimum pre-normalization blend norm of 0.1. Choose the lowest initial energy among 24 uniformly spaced candidate reflection axes. Run both charge assignments with the original exterior and with the exterior quieted by the same taper. Keep the precession rule, checkpoint, and perimeter matched.

Label the core trajectories by original site to separate location from charge sign. Compare inward speeds over 0.02–0.04 where both cores remain tracked. The reversal changes the winding texture and the blend introduces an interface, so this is a test of whether the observed asymmetry follows charge sign under this intervention.

**Success for the diagnostic.** The same 75° reflection axis minimized initial energy on both grids. Both tracked centers stayed at their original locations at launch and their local charge signs reversed. The blend raised initial total energy by 2.3–2.4%. The native branches reproduced the archived separation trajectories to within 8 × 10⁻¹⁶.

| Charge assignment and exterior | Late inward speed at the original negative site, 113 / 129 | Late inward speed at the original positive site, 113 / 129 | Spacing change at 0.04, 113 / 129 |
|---|---:|---:|---:|
| Native, native exterior | −0.836 / −0.662 | 2.772 / 2.854 | −30.9% / −33.2% |
| Native, quiet exterior | 0.109 / 0.142 | 0.953 / 0.944 | −16.0% / −16.4% |
| Reversed, native exterior | 0.556 / 0.491 | −0.014 / 0.063 | +5.2% / +5.5% |
| Reversed, quiet exterior | −0.048 / −0.036 | −0.331 / −0.311 | +7.2% / +7.2% |

In the native exterior the larger late inward component moved to the site that became positive, but it was far weaker than the original contraction. With quieted surroundings neither reversed knot showed sustained late inward motion along the initial axis. The strong collapse therefore did not simply follow the positive charge or stay at its original site. The effect depends on the interaction between the winding texture and the surroundings under this intervention. Both reversed branches stayed inside the 15% spacing band through time 0.04, with final net travel of roughly a quarter of a core diameter. This prepared-field diagnostic does not test autonomous formation or satisfy the three-diameter milestone.

[113×113 reversal](../../../results/genesis_v3_fixed_rule/charge_reversal_113.json) · [129×129 reversal](../../../results/genesis_v3_fixed_rule/charge_reversal_129.json)

### Extended travel after charge reversal

Recreate the same reversed pair with the native exterior on both grids. Retain the original domain, timestep, coefficients, and conservative precession. Compare the first 0.04 against the archived reversal. Continue with samples every 0.0025 to time 0.3 or until the three-diameter travel target, 15% spacing limit, tracking limit, or 0.09 boundary guard. This tests sustainment from a prepared reversal.

**Failure for sustained travel.** Both runs reproduced the archived separations through 0.04 to within 10⁻¹⁰. The pair exceeded the spacing limit by opening up. At failure both cores were resolved and the pair was still inside the boundary guard.

| Grid | First spacing violation | Travel in core diameters | Spacing change |
|---|---:|---:|---:|
| 113×113 | 0.0725 | 0.465 | +15.46% |
| 129×129 | 0.0700 | 0.423 | +15.06% |

Reversing winding changed the failure from contraction to expansion on both grids. This prepared reversal did not produce stable spacing over the required travel distance.

[113×113 extension](../../../results/genesis_v3_fixed_rule/charge_reversal_extended_113.json) · [129×129 extension](../../../results/genesis_v3_fixed_rule/charge_reversal_extended_129.json)

### Phase alignment at fixed winding

Apply a common rotation about the axial direction to both knots in the saved contracting pair. Inside the same radius-0.10 tube, the rotation is uniform. Taper it to zero by radius 0.155 while keeping the axial component fixed. This preserves the starting centers and the winding signs, while changing the transverse phase relative to the exterior. Compare 0°, 90°, 180°, and 270° through time 0.04 on both grids. Angles specify the full rotation through the taper, so 270° uses a different interface from −90°. Require both tracked cores, spacing within 15%, and clearance from the boundary guard on both grids to advance a phase to the full travel test. If multiple phases qualify, advance the one with the greater minimum net travel across grids.

Include −90° as a supplemental comparison. No angle qualified on both original domains. The 180° case hit a tracking limit on 113×113 and a spacing violation on 129×129. The 270° phase reached the boundary guard first on both grids at time 0.0275. This prevented a sustainment verdict for that phase in the original geometry.

Replay 270° and the unrotated control with 0.125 of north-aligned padding on every side from the start. This moves the boundary and changes the evolution, so compare phases only within the same padded geometry. Both phases passed the short screen on both grids. The 270° phase had a greater maximum spacing drift, 13.8–14.2% versus 9.6–9.9% without rotation. Extend both cases with the same timestep and the original three-diameter, spacing, boundary, and tracking gates.

[113×113 original domain](../../../results/genesis_v3_fixed_rule/phase_alignment_113.json) · [129×129 original domain](../../../results/genesis_v3_fixed_rule/phase_alignment_129.json) · [113-spacing padded screen](../../../results/genesis_v3_fixed_rule/phase_alignment_widened_113.json) · [129-spacing padded screen](../../../results/genesis_v3_fixed_rule/phase_alignment_widened_129.json)

| Padded branch | 113 spacing | 129 spacing |
|---|---|---|
| Unrotated | 1.234 diameters at time 0.3, spacing −7.57% | 1.381 diameters at time 0.3, spacing −8.03% |
| 270° | Two-core tracking ended at time 0.0875 | 1.348 diameters at time 0.3, spacing +1.12% |

**Inconclusive for three-diameter travel.** The unrotated padded control was still qualifying at the cap on both grids. The phase-rotated branch did not improve tracked travel across the two resolutions. The comparison supports the wider geometry as the clearer lead for this prepared pair. Padding changes both the boundary location and the field outside the original square, so the result cannot attribute the improvement to boundary distance alone. The first 0.04 of each extension reproduced the corresponding padded screen. This test starts from a prepared pair and leaves autonomous formation open.

[113-spacing extended branches](../../../results/genesis_v3_fixed_rule/phase_alignment_widened_extended_113.json) · [129-spacing extended branches](../../../results/genesis_v3_fixed_rule/phase_alignment_widened_extended_129.json)

### Three-diameter sustainment in the wider domain

Continue the unrotated padded checkpoints using the same precession, coefficients, grid spacing, and timestep. Require the earlier trajectory through 0.3 to reproduce before interpreting the continuation. Measure net midpoint displacement in initial core diameters. Stop at three diameters, more than 15% spacing drift, loss of tracking, approach within 0.09 of the boundary, or time 1.2. Save each stopping field to permit follow-up measurements without replaying the whole run. This gate tests prepared-pair sustainment in the wider geometry.

**Failure to meet the two-grid sustainment milestone.** The first 0.3 reproduced the earlier spacing trajectories to within 10⁻¹⁰. At 129 spacing the pair contracted by 17.61% after traveling 1.835 diameters, with both knots resolved and inside the boundary guard. At 113 spacing the original tracker stopped at 0.355, just after 1.522 diameters of verified travel. The saved field showed that the positive core was still present with local charge +0.967 but its equivalent radius had dipped to 2.985 cells, just below the three-cell cutoff.

In a diagnostic continuation from that saved field, the positive core returned above three cells by the next sample, 0.3575. Following the two nearby connected regions across the brief cutoff, their spacing then contracted by 16.20% after 1.643 diameters at 0.3725. Both cores were again resolved there. The original 113-spacing run retains its tracking-limit classification. The follow-up explains the limit and independently shows that contraction also ended the recovered trajectory well before the target.

[113-spacing trajectory](../../../results/genesis_v3_fixed_rule/wide_unrotated_travel_113.json) · [113-spacing endpoint diagnostic](../../../results/genesis_v3_fixed_rule/wide_unrotated_size_check_113.json) · [129-spacing trajectory](../../../results/genesis_v3_fixed_rule/wide_unrotated_travel_129.json)

### Can strain sustain the contracting pair?

Replay the saved mature seed-405 fixed-rule checkpoints from the damping diagnostic at 113×113 and 129×129. Hold the full orientation field, unit domain, zero damping, gradient penalty 0.0002, and easy-axis strength 225 matched. Use the strain parameters from the prepared-knot interaction test without tuning. Compare no strain, instantaneous equilibrium strain, and dynamic strain initialized in that same equilibrium with zero velocity. Follow the same opposite-charge cores by component overlap and require three initial core diameters of midpoint travel with at most 15% spacing change. Sample every 0.0025 through time 0.3 unless a gate ends the branch earlier.

**Failure for sustainment at the tested coupling.** All branches exceeded 15% contraction while both cores remained resolved. The no-strain branches reproduced the archived conservative separation trajectories to within 10⁻⁸ in relative separation change. Instantaneous and dynamic strain failed at the same sampled time on each grid and gave nearly the same travel distance. On 113×113 both reduced the distance relative to the uncoupled control. On 129×129 all three branches failed at the same sample.

| Grid | No strain | Instantaneous strain | Dynamic strain |
|---|---:|---:|---:|
| 113×113 | 0.677 diameters at 0.0325 | 0.263 at 0.0225 | 0.260 at 0.0225 |
| 129×129 | 0.131 diameters at 0.0200 | 0.128 at 0.0200 | 0.127 at 0.0200 |

The prepared-knot wave interaction still reproduces exactly on 65×65 with the shared strain equations. This sustainment comparison tests one coupling and one checkpoint family. It supplies no reason to advance this coupling to assembly as a remedy for contraction.

[113×113 branches](../../../results/genesis_v3_strain_wave/sustain_113.json) · [129×129 branches](../../../results/genesis_v3_strain_wave/sustain_129.json)

```powershell
foreach ($size in 113, 129) {
    .venv\Scripts\python.exe -B -m src.genesis_v3.strain_sustain --checkpoint "results/genesis_v3_fixed_rule/damping_handoff_$size.npz" --output "results/genesis_v3_strain_wave/sustain_$size.json"
}
```

### Can strain help a traveling pair form?

Start all three branches from seed-405 orientation disorder with bias −0.12, gradient penalty 0.0002, easy-axis strength 225, no damping, and 0.125 of north padding on each side. Use 129×129 and 161×161 interior grids. The dynamic strain starts at equilibrium for the same initial orientation as the instantaneous branch, with zero strain velocity. Both branches use the previously tested strain coefficients. The orientation-only control uses the same precession rule and physical grid spacing. Hold each rule fixed throughout.

Screen through time 0.025 with samples every 0.0005. Stop at a sampled net-charge violation or ambiguous charge reading, and track wall ancestry and mature local opposite charges of magnitude at least 0.90. Continue a qualifying pair if it reaches the time cap with both cores tracked, using the three-diameter and 15% spacing criteria. This is an exploratory seed comparison. The energy field in the raw output measures orientation energy, which can change through coupling.

**No demonstrated formation advantage.** The three launch records and timesteps matched at each resolution. On 129×129 all three branches showed wall candidates at 0.0005 and lost neutrality at 0.0015, before a mature pair was observed. On 161×161 all three stayed neutral, reached the first shared-wall mature-pair criterion at 0.0055, and lost tracking at the next sample, 0.006. The positive core remained resolved at that sample. None of the branches tracked a pair far enough to test sustained travel, and loss of tracking does not establish the negative knot's fate. These gates stopped the runs before 0.025, so this comparison does not determine whether later qualifying pairs could form. The tested strain parameters produced no detectable advantage at these checkpoints.

The padded strain operator uses the original lattice spacing. A direct launch check verified that equilibrium wave and instantaneous orientation rates were identical and that the residual strain acceleration was below 10⁻⁹.

[129 off](../../../results/genesis_v3_strain_wave/formation_129_off.json) · [129 instantaneous](../../../results/genesis_v3_strain_wave/formation_129_instant.json) · [129 wave](../../../results/genesis_v3_strain_wave/formation_129_wave.json) · [161 off](../../../results/genesis_v3_strain_wave/formation_161_off.json) · [161 instantaneous](../../../results/genesis_v3_strain_wave/formation_161_instant.json) · [161 wave](../../../results/genesis_v3_strain_wave/formation_161_wave.json)

### Surroundings probe at fixed position

Use the contracting handoff on the original domain. Preserve the field exactly within radius 0.10 of the segment joining the core centers. Outside that region, taper either the polar angle to zero or rotate the transverse orientation by π. Both changes finish at radius 0.155. The second intervention preserves local tilt amplitude, while it can change bond energy across the transition band. The cores, their charge disks, and their distance to the fixed perimeter are identical at launch. Use the unchanged conservative continuation and compare with the native field on both grids.
