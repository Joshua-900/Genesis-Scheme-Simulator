---
Area: Experiments
datetime_stamp: 2026-10-31T00:00:00-05:00
status: complete
confidence: vetted
tags:
  - genesis-scheme
  - v1
  - vortex-motion
  - negative-result
links:
  - "[[Experiments Index]]"
  - "[[V1 Vortex Motion Experiment]]"
  - "[[Audit Ledger]]"
  - "[[V1 Baseline Audit — 2026-10-31]]"
summary: Some matched structural resets alter vortex positions, but the first compact motion and continuation predictors fail their fresh-seed gates.
canonical: false
---

# V1 Vortex Motion Results — 2026-10-31

The isolated experiment completed on 24 fresh seeds, producing 8,102 forecast anchors. All branches start with identical θ and differ only in the specified joint structural-state intervention. V1/V2 and the historical tracker remain unchanged.

At +100 updates, 22 seeds retain both selected identities in every arm. Selected structural reset changes positions in 3/22; background reset gives zero divergence in all 22. The mean selected-minus-background RMS position divergence is 0.0964 sites, with paired-seed 95% bootstrap interval [0, 0.2250]. The conditional contrast did not clear its declared criterion.

**The compact structural motion model did not pass its full predictive gate.** A large gain over the poor matched-field predictor was insufficient: it lost to the no-motion and shuffled-structure references. The strict-continuation secondary gate also failed. Most horizon-surviving anchors have zero grid-resolved movement.

This retains the earlier causal local-structure result and adds limited trajectory observations; it does not establish an autonomous interaction law or a new physical dimension.

- [Detailed finding and limitations](../../../findings/2026-10-31_v1_vortex_motion.md)
- [Animated encounter](../../../results/vortex_motion_2026-10-31/encounter.gif)
- [All comparator tables and plots](../../../results/vortex_motion_2026-10-31/summary.md)
- [[V1 Vortex Motion Experiment]] documents modules, protocol, gates and reproduction.

All 28 tests passed and all 53 checked preserved engine source hashes matched. This is new coverage stacked on the closed baseline, not a repeat or replacement of its audit.
