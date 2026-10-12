"""Regression tests for the V1-to-V2 structural bridge."""

from __future__ import annotations

import unittest

import numpy as np

from src.genesis_grid import GenesisParams, GenesisState, rules_locking, step as v1_step
from src.genesis_grid.backend import to_cpu
from src.genesis_v2_integrated import IntegratedParams, IntegratedState, step as v2_step
from genesis_measure import RULES as V1_CENSUS_RULES


class V2IntegratedTests(unittest.TestCase):
    def test_zero_potential_coupling_has_v1_parity(self) -> None:
        """The bridge must not change V1 until a named V2 coupling is enabled."""
        np.random.seed(17)
        baseline = GenesisState(12, dt=0.05)
        bridge = IntegratedState(12, dt=0.05, seed=23)
        for name in ("theta", "tau", "ux", "uy", "C"):
            setattr(bridge, name, getattr(baseline, name).copy())

        v1_params = GenesisParams()
        v2_params = IntegratedParams()
        for _ in range(10):
            v1_step(baseline, v1_params, V1_CENSUS_RULES, post=rules_locking.locking_postprocess)
            v2_step(bridge, v2_params)

        for name in ("theta", "tau", "ux", "uy", "C"):
            np.testing.assert_allclose(to_cpu(getattr(bridge, name)), to_cpu(getattr(baseline, name)), rtol=0, atol=1e-12)

    def test_potentiality_can_change_actuality_without_replacing_v1_structure(self) -> None:
        state = IntegratedState(8, seed=5)
        before = to_cpu(state.theta).copy()
        params = IntegratedParams()
        params.potential_to_actual = 0.4
        v2_step(state, params)
        self.assertGreater(np.max(np.abs(to_cpu(state.theta) - before)), 1e-6)
        self.assertEqual(state.C.shape, state.theta.shape)
        self.assertEqual(state.tau.shape, state.theta.shape)

    def test_relation_memory_has_no_effect_until_explicitly_enabled(self) -> None:
        state = IntegratedState(8, seed=9)
        params = IntegratedParams()
        v2_step(state, params)
        self.assertEqual(float(np.max(to_cpu(state.rx))), 0.0)
        self.assertEqual(float(np.max(to_cpu(state.ry))), 0.0)

        params.relation_memory_rate = 0.4
        v2_step(state, params)
        self.assertGreater(float(np.max(to_cpu(state.rx))), 0.0)

    def test_relation_memory_tension_changes_the_inherited_tension_field(self) -> None:
        baseline = IntegratedState(8, seed=29)
        memory = IntegratedState(8, seed=29)
        baseline_params = IntegratedParams()
        memory_params = IntegratedParams()
        memory_params.relation_memory_rate = 0.3
        memory_params.relation_memory_decay = 0.05
        memory_params.relation_memory_tension = 0.2

        for _ in range(12):
            v2_step(baseline, baseline_params)
            v2_step(memory, memory_params)

        self.assertGreater(
            float(np.mean(np.abs(to_cpu(memory.tau) - to_cpu(baseline.tau)))),
            1e-8,
        )


if __name__ == "__main__":
    unittest.main()
