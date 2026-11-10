"""Formula language, numerical failure handling, persistence and real editor controls."""
from dataclasses import replace
import json
import os
from pathlib import Path
import tempfile
import unittest

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

import numpy as np
from PyQt5.QtWidgets import QApplication

from src.physarum_lab.domain.formulas import Expression, FormulaError, FormulaField, FormulaSpec
from src.physarum_lab.domain.model import Rules, Simulation
from src.physarum_lab.application.session import Session
from src.physarum_lab.adapters.storage import load_bundle, save_bundle
from src.physarum_lab.adapters.formula_editor import EXAMPLES, preview_image
from src.physarum_lab.adapters.desktop import StudioWindow

SMALL = Rules(size=64, agents=1200, sensor_distance=4, flow=.5)
ROOT = Path(__file__).resolve().parents[1]


def compare(test, a, b):
    test.assertEqual(a.tick, b.tick)
    test.assertEqual(a.rng.bit_generator.state, b.rng.bit_generator.state)
    for key in ('x', 'y', 'heading', 'trail', 'density'):
        np.testing.assert_array_equal(getattr(a, key), getattr(b, key))


class ExpressionTests(unittest.TestCase):
    def test_arithmetic_constants_functions_and_broadcast(self):
        x, y = np.array([[.2, .4, .6]]), np.array([[-.3], [.7]])
        actual = Expression('sin(pi*x)^2 + cos(tau*y)**2 + t').evaluate(x, y, .4)
        np.testing.assert_allclose(actual, np.sin(np.pi*x)**2 + np.cos(2*np.pi*y)**2 + .4, atol=2e-7)
        self.assertEqual(Expression('0.5').evaluate(x, y, 0).shape, (2, 3))
        np.testing.assert_allclose(Expression('min(x,y) + max(x,y)').evaluate(x, y, 0), x+y, atol=1e-7)

    def test_conditions_and_bounded_math(self):
        x = np.array([-.5, .5])
        actual = Expression('where(x > 0 and not (y > 0), sqrt(abs(x)), clip(x,-0.2,0.2))').evaluate(x, 0, 0)
        np.testing.assert_allclose(actual, [-.2, np.sqrt(.5)], atol=1e-7)

    def test_python_access_and_excessive_expressions_are_rejected(self):
        expressions = ['__import__("os")', 'x.__class__', 'x[0]', '(lambda: 1)()',
                       '[x for x in y]', 'open("foo")', 'sin(x, y)', 'unknown(x)',
                       'sin(x, other=1)', '"hello"', '1j', 'True', 'z+1',
                       '+'.join(['x']*100), 'sin('*30 + 'x' + ')'*30, '9'*500]
        for source in expressions:
            with self.subTest(source=source), self.assertRaises(FormulaError):
                Expression(source)

    def test_undefined_values_and_exponents_fail_cleanly(self):
        for source in ('1/0', 'sqrt(-1)', 'log(0)', 'exp(1000)', 'x**100', '(-1)**0.5'):
            with self.subTest(source=source), self.assertRaises(FormulaError):
                Expression(source).evaluate(np.array([0., 1.]), 0, 0)

    def test_coordinates_scale_time_and_static_cache(self):
        spec = FormulaSpec(expression='x + 2*y + t', scale=2, time_speed=.5)
        field = FormulaField(spec)
        actual = field.sample(np.array([0., 32., 64.]), 32, 64, 120)[0]
        np.testing.assert_array_equal(actual, [-1., 1., 3.])
        static = FormulaField(FormulaSpec(expression='sin(pi*x)'))
        self.assertIs(static.grid(64, 0), static.grid(64, 100))
        dynamic = FormulaField(FormulaSpec(expression='sin(pi*x+t)'))
        self.assertFalse(np.array_equal(dynamic.grid(64, 0)[0], dynamic.grid(64, 100)[0]))


class FormulaModelTests(unittest.TestCase):
    def test_vector_current_crosses_axis_between_valid_grid_samples(self):
        simulation = Simulation(7, SMALL)
        simulation.x[0] = SMALL.size / 2
        simulation.y[0] = SMALL.size * .75
        simulation.set_formula(FormulaSpec(
            response='flow', velocity_x='sin(4*pi*x+t)-y/x',
            velocity_y='x*t/pi-cos(t*x*y)-tau*y', scale=1.2, time_speed=.6,
        ))
        simulation.step(3, guidance=.1)
        self.assertEqual(simulation.tick, 3)
        self.assertTrue(np.isfinite(simulation.x).all())

    def test_all_examples_preview_and_evolve(self):
        for title, spec in EXAMPLES.items():
            with self.subTest(title=title):
                image, low, high = preview_image(FormulaField(spec), 18)
                self.assertEqual(image.size, (256, 256))
                self.assertTrue(np.isfinite([low, high]).all())
                s = Simulation(7, SMALL)
                s.set_formula(spec)
                s.step(4, guidance=.8)
                self.assertEqual(s.tick, 4)
                self.assertTrue(np.isfinite(s.trail).all())

    def test_rejected_apply_does_not_replace_previous_formula_or_state(self):
        s = Simulation(7, SMALL)
        s.set_formula(FormulaSpec(expression='x*x+y*y-.3'))
        old, wave = s.formula, s.wave.copy()
        before = Simulation.restore(s.snapshot())
        with self.assertRaises(FormulaError):
            s.set_formula(FormulaSpec(expression='sqrt(-1)'))
        self.assertIs(s.formula, old)
        np.testing.assert_array_equal(s.wave, wave)
        compare(self, s, before)

    def test_future_numerical_error_preserves_tick_rng_and_transition(self):
        s = Simulation(7, SMALL)
        s.set_formula(FormulaSpec(expression='1/(t-1)'))
        session = Session(s, target_guidance=1)
        session.advance(59)
        before = Simulation.restore(s.snapshot())
        guidance, wave = session.guidance, s.wave.copy()
        with self.assertRaises(FormulaError):
            session.advance()
        compare(self, s, before)
        self.assertEqual(session.guidance, guidance)
        np.testing.assert_array_equal(s.wave, wave)

    def test_zero_high_and_low_responses_actually_steer(self):
        rules = replace(SMALL, size=128, agents=5000, flow=0, jitter=.02)
        positions = {}
        for response in ('zero', 'high', 'low'):
            s = Simulation(7, rules)
            s.set_formula(FormulaSpec(expression='sin(pi*x)', response=response))
            s.step(140, guidance=1)
            value = np.sin(np.pi * (s.x / 128 * 2 - 1))
            positions[response] = float(np.mean(value))
            if response == 'zero':
                self.assertLess(float(np.mean(value**2)), .15)
        self.assertGreater(positions['high'], .35)
        self.assertLess(positions['low'], -.35)

    def test_constant_vector_current_changes_displacement_and_release_restores_builtin(self):
        rules = replace(SMALL, flow=0, jitter=0)
        a, b = Simulation(7, rules), Simulation(7, rules)
        a.set_formula(FormulaSpec(response='flow', velocity_x='1', velocity_y='0'))
        b.set_formula(FormulaSpec(response='flow', velocity_x='0', velocity_y='0'))
        a.step(guidance=1)
        b.step(guidance=1)
        displacement = (a.x-b.x+32)%64-32
        np.testing.assert_allclose(displacement, 3, atol=1e-5)
        a.set_formula(None)
        self.assertIsNone(a.formula)
        a.set_formula(FormulaSpec())
        a.set_modes(4, 7)
        self.assertIsNone(a.formula)

    def test_save_load_exact_continuation_and_legacy_bundle(self):
        root = ROOT/'work/formula_tests'
        root.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=root) as temp:
            for response in ('zero', 'flow'):
                session = Session(Simulation(8, SMALL), target_guidance=.8)
                session.simulation.set_formula(FormulaSpec(response=response))
                session.advance(13)
                from src.physarum_lab.adapters.render import Look
                folder = save_bundle(session, Look(), Path(temp)/response)
                loaded, _ = load_bundle(folder)
                self.assertEqual(loaded.simulation.formula.spec, session.simulation.formula.spec)
                session.advance(7)
                loaded.advance(7, force=True)
                compare(self, session.simulation, loaded.simulation)
            # Version-one bundles had no formula member in the snapshot.
            path = folder/'bundle.json'
            metadata = json.loads(path.read_text())
            metadata['version'] = 1
            metadata['simulation'].pop('formula')
            path.write_text(json.dumps(metadata))
            legacy, _ = load_bundle(path)
            self.assertIsNone(legacy.simulation.formula)


class FormulaEditorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_preview_apply_error_and_return_to_modes(self):
        window = StudioWindow(Session(Simulation(7, SMALL), playing=False))
        window.show()
        self.app.processEvents()
        window.timer.stop()
        try:
            window.formula_button.click()
            editor = window.formula_editor
            self.app.processEvents()

            before = Simulation.restore(window.session.simulation.snapshot())
            editor.scalar.setPlainText('sin(6*x+t)*cos(4*y-t)')
            editor.preview_button.click()
            self.assertFalse(editor.preview_label.pixmap().isNull())
            self.assertIsNone(window.session.simulation.formula)
            compare(self, before, window.session.simulation)
            editor.apply_button.click()
            self.assertEqual(window.session.simulation.formula.spec.expression, editor.scalar.toPlainText())
            self.assertFalse(window.modes.isEnabled())
            self.assertEqual(window.session.target_guidance, 1)
            editor.scalar.setPlainText('1/0')
            editor.apply_button.click()
            self.assertIn('undefined', editor.status.text().lower())
            self.assertNotEqual(window.session.simulation.formula.spec.expression, '1/0')
            editor.response.setCurrentIndex(editor.response.findData('flow'))
            editor.u.setPlainText('-y')
            editor.v.setPlainText('x')
            editor.apply_button.click()
            self.assertEqual(window.session.simulation.formula.spec.response, 'flow')
            window.step_once()
            editor.builtin.click()
            self.assertIsNone(window.session.simulation.formula)
            self.assertTrue(window.modes.isEnabled())
        finally:
            window.close()
            window.deleteLater()
            self.app.processEvents()

    def test_step_handles_a_future_formula_error_without_advancing(self):
        simulation = Simulation(7, SMALL)
        simulation.set_formula(FormulaSpec(expression='1/(t-1)'))
        session = Session(simulation, playing=False, target_guidance=1)
        session.advance(59, force=True)
        window = StudioWindow(session)
        window.timer.stop()
        try:
            before = Simulation.restore(simulation.snapshot())
            window.step_button.click()
            compare(self, simulation, before)
            self.assertIn('paused', window.message.text())
        finally:
            window.close()
            window.deleteLater()
            self.app.processEvents()


if __name__ == '__main__':
    unittest.main()
