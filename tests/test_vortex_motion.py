"""Periodic identity, matched interventions and forecast isolation checks."""

from __future__ import annotations

from dataclasses import replace
import unittest
from unittest.mock import patch

import numpy as np

from src.genesis_audit.v1_adapter import V1Adapter
from src.genesis_motion.evaluation import evaluate, shuffle_structure
from src.genesis_motion.experiment import Config, collect
from src.genesis_motion.observations import PeriodicTracker, Track, choose_pair, delta, disk, erase_structure, features


class MotionObservationTests(unittest.TestCase):
    def test_periodic_displacement_uses_short_direction(self):
        np.testing.assert_allclose(delta(np.array([.5, 4]), np.array([15.5, 4]), 16), [1, 0])

    def test_tracker_keeps_identity_across_periodic_edge(self):
        tracker = PeriodicTracker(16)
        first, second = np.zeros((16, 16), dtype=int), np.zeros((16, 16), dtype=int)
        first[5, 15], second[5, 0] = 1, 1
        with patch("src.genesis_motion.observations.winding", side_effect=[first, second]):
            old = tracker.update(first, 0)
            new = tracker.update(second, 5)
        self.assertEqual(list(old), list(new))
        self.assertAlmostEqual(next(iter(new.values())).vx, .2)

    def test_ambiguous_match_ends_identity_without_gap_bridging(self):
        tracker = PeriodicTracker(16)
        first, second, third = [np.zeros((16, 16), dtype=int) for _ in range(3)]
        first[5, 4] = first[5, 6] = second[5, 5] = third[5, 5] = 1
        with patch("src.genesis_motion.observations.winding", side_effect=[first, second, third]):
            original = set(tracker.update(first, 0))
            new = set(tracker.update(second, 5))
            again = set(tracker.update(third, 10))
        self.assertTrue(original.isdisjoint(new))
        self.assertEqual(new, again)

    def test_reset_is_local_smooth_and_preserves_theta(self):
        state = V1Adapter().create(32, 5)
        theta = state.theta.copy()
        for field in ("tau", "ux", "uy", "C"):
            getattr(state, field)[:] = 1
        erase_structure(state, np.array([0, 0]), 5)
        mask, _, _ = disk(32, 0, 0, 5)
        np.testing.assert_array_equal(state.theta, theta)
        self.assertEqual(state.tau[0, 0], 0)
        self.assertTrue(np.all(state.tau[~mask] == 1))
        self.assertTrue(0 < state.tau[0, 1] < 1)
        self.assertEqual(state.tau[0, 1], state.tau[0, 31])

    def test_features_are_matched_capacity_and_read_only(self):
        state = V1Adapter().create(32, 6)
        snapshot = V1Adapter.snapshot(state)
        original = {k: v.copy() for k, v in snapshot.items()}
        a, b = Track(1, 1, 15.5, 16.5, 0, 100), Track(2, -1, 20.5, 16.5, 0, 100)
        f = features(snapshot, a, b, 100)
        self.assertEqual(f["field_matched"].shape, (24,))
        self.assertEqual(f["structural"].shape, (24,))
        for k in snapshot:
            np.testing.assert_array_equal(snapshot[k], original[k])

    def test_selection_uses_present_compression_and_age(self):
        snapshot = V1Adapter.snapshot(V1Adapter().create(32, 1))
        tracks = {1: Track(1, 1, 8.5, 8.5, 0, 100), 2: Track(2, -1, 12.5, 8.5, 0, 100)}
        self.assertEqual(choose_pair(tracks, snapshot, 100, 50, 3, 10), (1, 2))
        self.assertIsNone(choose_pair(tracks, snapshot, 100, 101, 3, 10))


class MotionEvaluationTests(unittest.TestCase):
    def test_structure_shuffle_cannot_cross_seed_or_branch(self):
        x = np.arange(16 * 24).reshape(16, 24)
        seeds = np.repeat([1, 2], 8)
        branches = np.tile(np.repeat([0, 1], 4), 2)
        out = shuffle_structure(x, seeds, branches, np.random.default_rng(3))
        np.testing.assert_array_equal(out[:, :16], x[:, :16])
        for seed in (1, 2):
            for branch in (0, 1):
                mask = (seeds == seed) & (branches == branch)
                self.assertEqual(sorted(map(tuple, x[mask, -8:])), sorted(map(tuple, out[mask, -8:])))

    def test_identical_representations_do_not_clear_motion_gate(self):
        rng = np.random.default_rng(7)
        seeds = np.repeat(np.arange(1, 10), 12)
        x = rng.normal(size=(108, 24))
        arrays = {"seed": seeds, "branch": np.zeros(108), "survived": np.ones(108, dtype=bool), "motion": rng.normal(size=(108, 2))}
        for model in ("kinematic", "local_field", "field_matched", "structural"):
            arrays[model] = x.copy()
        r = evaluate(arrays, (1, 2, 3), {"test": (4, 5, 6), "replication": (7, 8, 9)}, bootstrap=20)
        self.assertFalse(r["gate_passes"])
        for cohort in r["cohorts"].values():
            self.assertEqual(cohort["motion"]["comparisons"]["field_matched"]["relative_gain"], 0)
            self.assertFalse(cohort["continuation"]["passes"])

    def test_cohort_overlap_is_rejected(self):
        with self.assertRaises(ValueError):
            replace(Config(), test=(1001, 2001, 2002)).validate()

    def test_small_collection_retains_matched_start_and_trajectory_shapes(self):
        config = Config(n=32, burn=100, tracker_warmup=50, follow=30, horizon=10, interval=5, minimum_age=5, maximum_pair_distance=12.)
        result = collect(19, config, True)
        self.assertIsNotNone(result)
        for branch in result["branches"].values():
            self.assertEqual(branch["positions"].shape, (7, 2, 2))
            np.testing.assert_array_equal(branch["theta"][0], result["snapshot"]["theta"].astype(np.float32))
            for row in branch["records"]:
                if row["survived"]:
                    self.assertTrue(np.isfinite(row["motion"]).all())


if __name__ == "__main__":
    unittest.main()
