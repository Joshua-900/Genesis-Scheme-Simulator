import tempfile
import unittest
from pathlib import Path

import numpy as np

from src.physarum_lab.adapters.render import Look
from src.physarum_lab.adapters.storage import load_bundle, save_bundle
from src.physarum_lab.application.genesis_pair import GenesisPair
from src.physarum_lab.domain.formulas import FormulaSpec
from src.physarum_lab.domain.genesis_source import FrozenGenesis
from src.physarum_lab.domain.model import Rules


def source():
    return FrozenGenesis(7, 270, {'C': np.eye(16), 'ux': np.ones((16, 16)),
                                  'uy': np.zeros((16, 16))})


class GenesisComparisonTests(unittest.TestCase):
    def test_live_source_updates_formula_cache_and_can_freeze_again(self):
        from src.genesis_sandbox.model import Sandbox

        genesis = Sandbox(7, 16)
        genesis.advance(12)
        state = genesis.states['geometry_on']
        source = FrozenGenesis(7, genesis.update, state)
        pair = GenesisPair(7, Rules(size=32, agents=400), source, genesis)
        formula = pair.guided.simulation.formula
        initial = formula.grid(32, 0)[0].copy()
        theta = state['theta'].copy()
        pair.advance()
        self.assertEqual(genesis.update, 12)
        pair.evolving = True
        pair.advance()
        self.assertEqual(pair.feed.tick, 13)
        self.assertFalse(np.array_equal(state['theta'], theta))
        changed = formula.grid(32, 2)[0]
        self.assertFalse(np.array_equal(initial, changed))
        pair.evolving = False
        pair.advance()
        self.assertEqual(genesis.update, 13)
        self.assertIs(changed, formula.grid(32, 3)[0])
        self.assertEqual(pair.guided.simulation.tick, pair.control.simulation.tick)

    def test_zero_strength_keeps_lanes_matched_and_steering_separates_them(self):
        snapshot = source()
        pair = GenesisPair(7, Rules(size=32, agents=400), snapshot)
        for session in (pair.guided, pair.control):
            session.guidance = 0
            session.guide(0)
        pair.advance()
        guided, control = pair.guided.simulation, pair.control.simulation
        np.testing.assert_array_equal(guided.x, control.x)
        np.testing.assert_array_equal(guided.amber.trail, control.amber.trail)
        for session in (pair.guided, pair.control):
            session.guide(.45)
        for _ in range(8):
            pair.advance()
        self.assertEqual(guided.tick, control.tick)
        self.assertFalse(np.array_equal(guided.x, control.x))
        np.testing.assert_array_equal(snapshot.fields['ux'], 1)
        with self.assertRaises(ValueError):
            snapshot.fields['ux'].setflags(write=True)

    def test_source_formula_survives_bundle_reload_in_both_populations(self):
        pair = GenesisPair(7, Rules(size=32, agents=400), source())
        pair.set_formula(FormulaSpec(expression='C - .1'), 'amber')
        pair.advance()
        root = Path(__file__).resolve().parents[1] / 'work'
        with tempfile.TemporaryDirectory(dir=root) as tmp:
            bundle = save_bundle(pair.guided, Look(), Path(tmp) / 'guided')
            loaded, _ = load_bundle(bundle)
        original = pair.guided
        original.advance(force=True)
        loaded.advance(force=True)
        np.testing.assert_array_equal(loaded.simulation.trail, original.simulation.trail)
        np.testing.assert_array_equal(loaded.simulation.amber.x, original.simulation.amber.x)
        self.assertEqual(loaded.simulation.genesis.tick, 270)
        self.assertIs(loaded.simulation.amber.genesis, loaded.simulation.genesis)
