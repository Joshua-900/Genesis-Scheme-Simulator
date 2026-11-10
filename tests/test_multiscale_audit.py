"""Scientific validity and engine-preservation checks for the isolated audit."""

from __future__ import annotations

from dataclasses import replace
import tempfile
from pathlib import Path
import unittest

import numpy as np

from genesis_multiscale_audit import AuditConfig, run
from genesis_v1_compression_ablation import RULES, make_params
from src.genesis_audit.analysis import (
    FULL_FEATURES, descriptors, evaluate_dataset, feature_vectors, observational_controls,
    response_targets, ridge_predict, shuffled_context, square_masks, winding,
)
from src.genesis_audit.v1_adapter import V1Adapter
from src.genesis_grid import diagnostics, rules_locking, step


class DescriptorTests(unittest.TestCase):
    def setUp(self):
        self.state = V1Adapter().create(16, 7)
        self.snapshot = V1Adapter.snapshot(self.state)

    def test_periodic_winding_matches_existing_detector(self):
        expected = diagnostics.detect_vortices(self.state)[2]
        actual = winding(self.snapshot["theta"])
        np.testing.assert_array_equal(actual, expected)
        self.assertEqual(actual.sum(), 0)
        np.testing.assert_array_equal(winding(self.snapshot["theta"] + .73), actual)

    def test_block_mean_treats_angle_wrap_circularly(self):
        self.snapshot["theta"][:] = .01
        self.snapshot["theta"][:, ::2] = 2 * np.pi - .01
        d = descriptors(self.snapshot, np.ones((16, 16), dtype=bool), winding(self.snapshot["theta"]))
        self.assertGreater(d["coherence"], .999)

    def test_nested_and_planar_masks_have_same_footprint_without_mutation(self):
        before = {k: v.copy() for k, v in self.snapshot.items()}
        for center in ((0, 0), (15, 15), (8, 8)):
            masks = square_masks(16, center, (2, 4, 8))
            self.assertEqual([int(m.sum()) for m in masks], [4, 16, 64])
            features = feature_vectors(self.snapshot, center, (2, 4, 8))
            for track in features.values():
                self.assertEqual(track["multiscale"].shape, track["planar_shells"].shape)
        for key in before:
            np.testing.assert_array_equal(self.snapshot[key], before[key])

    def test_zero_and_wrapped_responses(self):
        equal = {k: v.copy() for k, v in self.snapshot.items()}
        equal["theta"] += 2 * np.pi
        np.testing.assert_allclose(response_targets(self.snapshot, equal, (0, 0)), 0, atol=1e-7)
        equal["theta"] = self.snapshot["theta"] + np.pi
        np.testing.assert_allclose(response_targets(self.snapshot, equal, (0, 0)), 2)

    def test_controls_preserve_expected_marginals_and_do_not_mutate(self):
        before = self.snapshot["theta"].copy()
        controls = observational_controls(self.snapshot, np.random.default_rng(6))
        np.testing.assert_array_equal(np.sort(controls["spatial_permutation"]["theta"].ravel()), np.sort(before.ravel()))
        self.assertTrue(np.isin(controls["independent_angles"]["theta"], before).all())
        np.testing.assert_array_equal(before, self.snapshot["theta"])


class EvaluationTests(unittest.TestCase):
    def test_context_shuffle_respects_seed_and_preserves_local_inputs(self):
        x = np.arange(60).reshape(10, 6)
        seeds = np.repeat([1, 101], 5)
        actual = shuffled_context(x, seeds, 2, np.random.default_rng(8))
        np.testing.assert_array_equal(actual[:, :2], x[:, :2])
        for seed in (1, 101):
            self.assertEqual(sorted(map(tuple, actual[seeds == seed, 2:])), sorted(map(tuple, x[seeds == seed, 2:])))

    def test_test_rows_do_not_affect_training_standardization(self):
        rng = np.random.default_rng(9)
        x = rng.normal(size=(30, 4))
        y = x[:, :2]
        test = rng.normal(size=(3, 4))
        a = ridge_predict(x, y, test, 1.)
        b = ridge_predict(x, y, np.vstack((test, np.full((1, 4), 1e9))), 1.)
        np.testing.assert_allclose(a, b[:3])

    def test_equal_representations_cannot_pass_gate(self):
        rng = np.random.default_rng(11)
        seeds = np.repeat(np.arange(1, 10), 5)
        arrays = {"seed": seeds, "targets": rng.normal(size=(45, 3))}
        for track, count in (("theta_only", 5), ("full_state_summaries", len(FULL_FEATURES))):
            x = rng.normal(size=(45, count * 2))
            for model in ("multiscale", "planar_shells"):
                arrays[f"{track}__{model}"] = x.copy()
            arrays[f"{track}__local"] = x[:, :count].copy()
        result = evaluate_dataset(arrays, (1, 2, 3), {"test": (4, 5, 6), "replication": (7, 8, 9)}, 10., .05, .7, 50)
        self.assertFalse(result["primary_gate_passes"])
        for track in result["tracks"].values():
            for cohort in track["cohorts"].values():
                self.assertEqual(cohort["comparisons"]["planar_shells"]["relative_loss_reduction"], 0.)


class PreservationTests(unittest.TestCase):
    def test_adapter_has_exact_existing_v1_preset_parity(self):
        adapter = V1Adapter()
        state = adapter.create(16, 21)
        baseline = adapter.clone(state)
        params = make_params(.1)
        for _ in range(20):
            step(baseline, params, RULES, post=rules_locking.locking_postprocess)
        adapter.advance(state, 20)
        for field in ("theta", "tau", "ux", "uy", "C"):
            np.testing.assert_array_equal(getattr(state, field), getattr(baseline, field))

    def test_clone_and_snapshot_are_detached(self):
        adapter = V1Adapter()
        state = adapter.create(16, 2)
        before = state.theta.copy()
        clone = adapter.clone(state)
        adapter.perturb(clone, (0, 0), .3, 1.5)
        adapter.advance(clone, 3)
        snapshot = adapter.snapshot(state)
        snapshot["theta"][:] = 0
        np.testing.assert_array_equal(state.theta, before)

    def test_creation_does_not_consume_global_rng(self):
        np.random.seed(3)
        expected = np.random.random(4)
        np.random.seed(3)
        V1Adapter().create(16, 7)
        np.testing.assert_array_equal(np.random.random(4), expected)

    def test_geometry_ablation_has_no_displacement(self):
        adapter = V1Adapter("geometry_ablation")
        state = adapter.create(16, 3)
        adapter.advance(state, 40)
        np.testing.assert_array_equal(state.ux, 0)
        np.testing.assert_array_equal(state.uy, 0)

    def test_invalid_cohorts_rejected_before_any_output(self):
        with self.assertRaises(ValueError):
            replace(AuditConfig(), test_seeds=(1, 2, 3)).validate()

    def test_tiny_end_to_end_run_preserves_sources_and_refuses_overwrite(self):
        config = AuditConfig(grid_sizes=(16,), modes=("v1",), sample_frames=(2,), scales=(2, 4, 8), train_seeds=(1, 2, 3),
            test_seeds=(101, 102, 103), replication_seeds=(201, 202, 203), centers_per_snapshot=2, horizon=2, bootstrap_draws=20)
        scratch = Path(__file__).resolve().parents[1] / "work"
        scratch.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=scratch) as directory:
            self.assertTrue(Path(directory).resolve().is_relative_to(scratch.resolve()))
            output = Path(directory) / "audit"
            report = run(config, output)
            self.assertTrue(report["engine_sources_unchanged"])
            self.assertTrue((output / "protocol.json").exists())
            with np.load(output / "N16/v1/seed_1.npz") as raw:
                self.assertEqual(raw["targets"].shape, (2, 3))
                self.assertEqual(raw["snapshot_theta"].shape, (1, 16, 16))
            with self.assertRaises(ValueError):
                run(config, output)


if __name__ == "__main__":
    unittest.main()
