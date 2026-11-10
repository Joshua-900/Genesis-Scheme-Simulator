import os
from pathlib import Path
import tempfile
import unittest

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

import numpy as np
from PyQt5.QtWidgets import QApplication

from src.physarum_lab.adapters.desktop import StudioWindow
from src.physarum_lab.adapters.render import Look
from src.physarum_lab.adapters.storage import load_bundle, save_bundle
from src.physarum_lab.application.session import Session
from src.physarum_lab.domain.chase import Chase
from src.physarum_lab.domain.formulas import FormulaError, FormulaSpec
from src.physarum_lab.domain.model import Rules, Simulation

RULES = Rules(size=48, agents=501)


class ChaseTests(unittest.TestCase):
    def test_follow_changes_amber_trajectory_and_erasure_is_local(self):
        control = Chase(7, RULES, follow=0, erase=0)
        chase = Chase(7, RULES, follow=0, erase=.6)
        control.step(5)
        chase.step(5)
        self.assertEqual(chase.population, RULES.agents)
        self.assertEqual(chase.amber.density.sum(), RULES.agents // 2)
        self.assertLess(chase.trail.sum(), control.trail.sum())
        a = Chase(7, RULES, follow=0, erase=0)
        b = Chase(7, RULES, follow=8, erase=0)
        a.step(10)
        b.step(10)
        np.testing.assert_array_equal(a.x, b.x)
        self.assertFalse(np.array_equal(a.amber.x, b.amber.x))

    def test_amber_formula_failure_cannot_advance_ivory(self):
        chase = Chase(7, RULES)
        chase.set_formula(FormulaSpec(expression='1/(t-1)'), 'amber')
        chase.step(59)
        previous = chase.snapshot()
        with self.assertRaises(FormulaError):
            chase.step()
        self.assertEqual((chase.tick, chase.amber.tick), (59, 59))
        self.assertEqual(chase.rng.bit_generator.state, previous['rng'])
        np.testing.assert_array_equal(chase.trail, previous['trail'])

    def test_roundtrip_preserves_both_fields_and_scheduled_release(self):
        session = Session(Chase(7, RULES), guidance=1, target_guidance=1, release_at=8)
        session.simulation.set_formula(FormulaSpec(expression='sin(x+t)'), 'ivory')
        session.advance(5)
        root = Path(__file__).resolve().parents[1] / 'work'
        with tempfile.TemporaryDirectory(dir=root) as tmp:
            path = save_bundle(session, Look(), Path(tmp) / 'chase')
            saved, _ = load_bundle(path)
            session.advance(8)
            saved.advance(8, force=True)
        self.assertEqual(saved.guidance, session.guidance)
        self.assertLess(saved.guidance, 1)
        self.assertEqual(saved.target_guidance, 0)
        for a, b in ((session.simulation, saved.simulation),
                     (session.simulation.amber, saved.simulation.amber)):
            self.assertEqual(a.formula.spec, b.formula.spec)
            np.testing.assert_array_equal(a.trail, b.trail)
            np.testing.assert_array_equal(a.x, b.x)
            self.assertEqual(a.rng.bit_generator.state, b.rng.bit_generator.state)

    def test_desktop_switch_and_formula_target(self):
        app = QApplication.instance() or QApplication([])
        solo = Session(Simulation(7, RULES), playing=False)
        window = StudioWindow(solo)
        window.timer.stop()
        try:
            window.chase_button.click()
            chase = window.session.simulation
            self.assertIsInstance(chase, Chase)
            self.assertEqual(window.session.release_at, 90)
            window.follow.setValue(5)
            self.assertEqual(chase.follow, 5)
            window.open_formula_editor()
            editor = window.formula_editor
            editor.target.setCurrentIndex(editor.target.findData('amber'))
            editor.scalar.setPlainText('sin(y+t)')
            editor.apply()
            self.assertEqual(chase.amber.formula.spec.expression, 'sin(y+t)')
            self.assertNotEqual(chase.formula.spec.expression, 'sin(y+t)')
            window.chase_button.click()
            self.assertIs(window.session, solo)
        finally:
            window.close()
            window.deleteLater()
            app.processEvents()
