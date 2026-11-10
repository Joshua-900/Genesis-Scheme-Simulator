"""Behavioral contracts for the independent Physarum studio."""
from dataclasses import replace
import os
from pathlib import Path
import tempfile
import unittest

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
os.environ.setdefault('OPENBLAS_NUM_THREADS', '1')

import numpy as np
from PyQt5.QtCore import QPoint, QPointF, Qt
from PyQt5.QtTest import QTest
from PyQt5.QtWidgets import QApplication

from src.physarum_lab.application.session import Session
from src.physarum_lab.domain.model import Rules, Simulation
from src.physarum_lab.domain.fields import current_velocity, wave_field
from src.physarum_lab.adapters.render import Look, render
from src.physarum_lab.adapters.storage import load_bundle, save_bundle
from src.physarum_lab.adapters.desktop import StudioWindow

SMALL = Rules(size=64, agents=1500, sensor_distance=5, crowding=.5, flow=.7)
WORK = Path(__file__).resolve().parents[1] / 'work/physarum_tests'


def compare(test, first, second):
    test.assertEqual(first.tick, second.tick)
    test.assertEqual(first.rules, second.rules)
    for name in ('x', 'y', 'heading', 'trail', 'density'):
        np.testing.assert_array_equal(getattr(first, name), getattr(second, name))
    test.assertEqual(first.rng.bit_generator.state, second.rng.bit_generator.state)


class PhysicsTests(unittest.TestCase):
    def test_seed_and_step_partition_are_reproducible(self):
        a, b = Simulation(7, SMALL), Simulation(7, SMALL)
        a.step(20, guidance=.6)
        b.step(8, guidance=.6)
        b.step(12, guidance=.6)
        compare(self, a, b)
        c = Simulation(8, SMALL)
        self.assertFalse(np.array_equal(a.x, c.x))

    def test_positions_wrap_and_deposits_conserve_population(self):
        s = Simulation(2, replace(SMALL, flow=4))
        s.x[:] = np.nextafter(np.float32(64), np.float32(0))
        s.y[:] = np.float32(.00000001)
        expected = 0.
        for _ in range(30):
            s.step()
            self.assertTrue(((s.x >= 0) & (s.x < 64) & (s.y >= 0) & (s.y < 64)).all())
            self.assertEqual(float(s.density.sum()), SMALL.agents)
            expected = (expected + SMALL.agents) * s.rules.retention
            self.assertAlmostEqual(float(s.trail.sum()), expected, delta=expected * 2e-6)

    def test_wave_guidance_concentrates_agents_near_nodes(self):
        rules = Rules(size=128, agents=6000, sensor_distance=4, jitter=.05, crowding=.4)
        free, guided = Simulation(11, rules), Simulation(11, rules)
        free.step(220)
        guided.step(220, guidance=1.)
        def cost(s):
            return float(np.mean(s.wave[s.y.astype(int), s.x.astype(int)]**2))
        self.assertLess(cost(guided), cost(free) * .6)

    def test_currents_are_periodic_and_numerically_divergence_free(self):
        x = np.array([11., 25., 41.])
        y = np.array([5., 18., 33.])
        vx, vy = current_velocity(x, y, 64, 100)
        bx, by = current_velocity(x + 64, y + 64, 64, 100)
        np.testing.assert_allclose(vx, bx, atol=1e-12)
        np.testing.assert_allclose(vy, by, atol=1e-12)
        eps = .0001
        divergence = ((current_velocity(x + eps, y, 64, 100)[0] - current_velocity(x - eps, y, 64, 100)[0])
                      + (current_velocity(x, y + eps, 64, 100)[1] - current_velocity(x, y - eps, 64, 100)[1])) / (2 * eps)
        np.testing.assert_allclose(divergence, 0, atol=1e-8)

    def test_stir_is_local_periodic_and_does_not_change_positions_or_trail(self):
        s = Simulation(4, SMALL)
        s.x[:2], s.y[:2] = [1, 63], [32, 32]
        before = s.snapshot()
        s.disturb(0, 32, radius=5)
        self.assertTrue((s.heading[:2] != before['heading'][:2]).all())
        dx = (before['x'] + 32) % 64 - 32
        dy = (before['y'] - 32 + 32) % 64 - 32
        far = np.hypot(dx, dy) >= 5
        np.testing.assert_array_equal(s.heading[far], before['heading'][far])
        np.testing.assert_array_equal(s.x, before['x'])
        np.testing.assert_array_equal(s.trail, before['trail'])
        self.assertEqual(s.tick, 0)

    def test_snapshot_is_owned_and_restores_exact_continuation(self):
        s = Simulation(5, SMALL)
        s.step(15, guidance=.4)
        saved = s.snapshot()
        restored = Simulation.restore(saved)
        saved['x'][:] = 0
        self.assertFalse(np.array_equal(s.x, saved['x']))
        s.step(9, guidance=.8)
        restored.step(9, guidance=.8)
        compare(self, s, restored)

    def test_invalid_rules_steps_and_snapshots_are_rejected(self):
        for patch in ({'agents': 1.5}, {'size': 0}, {'speed': float('nan')},
                      {'retention': 1.}, {'mode_n': 3}, {'flow': -1}):
            with self.subTest(patch=patch), self.assertRaises(ValueError):
                replace(SMALL, **patch)
        s = Simulation(1, SMALL)
        for count, guidance in ((-1, 0), (1, 1.1), (1, float('nan'))):
            with self.assertRaises(ValueError):
                s.step(count, guidance)
        snapshot = s.snapshot()
        snapshot['trail'][0, 0] = np.nan
        with self.assertRaises(ValueError):
            Simulation.restore(snapshot)

    def test_mode_changes_preserve_state_and_random_generator(self):
        s = Simulation(3, SMALL)
        before = s.snapshot()
        s.set_modes(4, 7)
        np.testing.assert_array_equal(s.wave, wave_field(64, 4, 7))
        for key in ('x', 'y', 'heading', 'trail', 'density'):
            np.testing.assert_array_equal(getattr(s, key), before[key])
        self.assertEqual(s.rng.bit_generator.state, before['rng'])


class SessionTests(unittest.TestCase):
    def test_pause_and_gradual_transition_are_tick_based(self):
        a = Session(Simulation(7, SMALL), playing=False)
        a.guide(1.)
        a.advance(20)
        self.assertEqual((a.guidance, a.simulation.tick), (0., 0))
        a.advance(20, force=True)
        self.assertAlmostEqual(a.guidance, .2)
        a.guide(0.)
        a.advance(10, force=True)
        self.assertAlmostEqual(a.guidance, .1)

    def test_transition_batching_does_not_change_results(self):
        a = Session(Simulation(7, SMALL), target_guidance=1.)
        b = Session(Simulation(7, SMALL), target_guidance=1.)
        a.advance(40)
        for _ in range(4):
            b.advance(10)
        compare(self, a.simulation, b.simulation)
        self.assertEqual(a.guidance, b.guidance)


class PresentationTests(unittest.TestCase):
    def test_render_is_finite_changes_palette_and_preserves_state(self):
        s = Simulation(1, SMALL)
        s.step(30)
        before = s.snapshot()
        image = render(s, Look(), side=256)
        ember = render(s, Look(palette='Ember'), side=256)
        self.assertEqual(image.size, (256, 256))
        self.assertFalse(np.array_equal(image, ember))
        for key in ('x', 'y', 'heading', 'trail', 'density'):
            np.testing.assert_array_equal(getattr(s, key), before[key])
        self.assertEqual(s.rng.bit_generator.state, before['rng'])

    def test_bundle_restores_look_transition_and_exact_continuation(self):
        WORK.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=WORK) as tmp:
            a = Session(Simulation(4, SMALL), target_guidance=.8)
            a.advance(18)
            look = Look(palette='Ember', exposure=2.1)
            folder = save_bundle(a, look, Path(tmp) / 'bundle')
            b, loaded_look = load_bundle(folder)
            self.assertFalse(b.playing)
            self.assertEqual(loaded_look, look)
            self.assertEqual(a.guidance, b.guidance)
            a.advance(10)
            b.advance(10, force=True)
            compare(self, a.simulation, b.simulation)
            with self.assertRaises(FileExistsError):
                save_bundle(a, look, folder)
            (folder / 'state.npz').write_bytes(b'broken')
            with self.assertRaisesRegex(ValueError, 'checksum'):
                load_bundle(folder)


class DesktopTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        WORK.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=WORK)
        self.w = StudioWindow(Session(Simulation(7, SMALL), playing=False), output=Path(self.temp.name))
        self.w.show()
        self.app.processEvents()
        self.w.timer.stop()

    def tearDown(self):
        self.w.close()
        self.w.deleteLater()
        self.app.processEvents()
        self.temp.cleanup()

    def test_play_step_guidance_modes_and_reseed(self):
        w = self.w
        QTest.mouseClick(w.play, Qt.LeftButton)
        w.tick()
        self.assertEqual(w.session.simulation.tick, 1)
        QTest.mouseClick(w.step_button, Qt.LeftButton)
        self.assertFalse(w.session.playing)
        self.assertEqual(w.session.simulation.tick, 2)
        w.gather.click()
        self.assertEqual(w.session.target_guidance, 1.)
        self.assertEqual(w.session.guidance, 0.)
        w.modes.setCurrentIndex(2)
        self.assertEqual((w.session.simulation.rules.mode_m, w.session.simulation.rules.mode_n), (4, 7))
        w.current.setValue(220)
        self.assertEqual(w.session.simulation.rules.flow, 2.2)
        w.seed.setText('99')
        w.reset_button.click()
        self.assertEqual((w.session.simulation.seed, w.session.simulation.rules.agents), (99, SMALL.agents))
        w.seed.setText('-1')
        w.reset_button.click()
        self.assertEqual(w.session.simulation.seed, 99)

    def test_stir_mapping_and_look_controls_preserve_tick_and_seed(self):
        w = self.w
        w.session.simulation.step(10)
        w.refresh()
        s = w.session.simulation
        w.canvas.zoom = 2
        w.canvas.center = np.array([.4, .6])
        rect = w.canvas.square()
        point = QPoint(round(rect.center().x()), round(rect.center().y()))
        x, y = w.canvas.position(QPointF(point))
        self.assertAlmostEqual(x, .4 * 64, delta=.2)
        self.assertAlmostEqual(y, .6 * 64, delta=.2)
        before = s.snapshot()
        w.palette.setCurrentText('Ember')
        w.exposure.setValue(210)
        self.assertEqual(s.rng.bit_generator.state, before['rng'])
        self.assertEqual(s.tick, 10)
        # Put an agent inside the brush to make the interaction unambiguous.
        s.x[0], s.y[0] = x + 1, y
        heading = s.heading[0]
        QTest.mouseClick(w.canvas, Qt.LeftButton, pos=point)
        self.assertNotEqual(s.heading[0], heading)

    def test_export_and_load_restore_controls_without_resetting_saved_state(self):
        w = self.w
        w.palette.setCurrentText('Ember')
        w.exposure.setValue(210)
        w.modes.setCurrentIndex(2)
        w.guidance.setValue(80)
        w.session.advance(15, force=True)
        w.export_button.click()
        self.assertIsNotNone(w.last_export)
        before = w.session.simulation.snapshot()
        w.palette.setCurrentText('Moon')
        w.exposure.setValue(50)
        w.load_state(w.last_export)
        self.assertEqual(w.look, Look(palette='Ember', exposure=2.1))
        self.assertEqual(w.modes.currentData(), (4, 7))
        self.assertEqual(w.guidance.value(), 80)
        self.assertFalse(w.session.playing)
        np.testing.assert_array_equal(w.session.simulation.trail, before['trail'])
        self.assertEqual(w.session.simulation.tick, 15)


if __name__ == '__main__':
    unittest.main()
