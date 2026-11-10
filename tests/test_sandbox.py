"""Check edit locality, paired controls, replay and native control wiring."""
import copy
import json
import os
from pathlib import Path
import tempfile
import unittest

os.environ.setdefault('QT_QPA_PLATFORM','offscreen')

import numpy as np
from PIL import Image
from PyQt5.QtCore import QEvent, QPoint, QPointF, Qt
from PyQt5.QtGui import QMouseEvent
from PyQt5.QtTest import QTest
from PyQt5.QtWidgets import QApplication

from src.genesis_sandbox.export import export_bundle, pixels
from src.genesis_sandbox.model import LANES, ROOT, Sandbox
from src.genesis_sandbox.ui import SandboxWindow


def workspace_temporary():
    directory = ROOT/'work/sandbox_tests'
    directory.mkdir(parents=True,exist_ok=True)
    return tempfile.TemporaryDirectory(dir=directory)


class SandboxModelTests(unittest.TestCase):
    def test_paint_changes_only_local_theta_and_matches_lanes(self):
        model = Sandbox(7,16)
        before = copy.deepcopy(model.states)
        model.paint(0,0,3,np.pi/2,'turn')
        rows,cols = np.indices((16,16))
        outside = np.hypot(cols,rows) >= 3
        for name in LANES:
            np.testing.assert_array_equal(model.states[name]['theta'][outside],before[name]['theta'][outside])
            for key in ('tau','ux','uy','C'):
                np.testing.assert_array_equal(model.states[name][key],before[name][key])
        np.testing.assert_array_equal(model.states[LANES[0]]['theta'],model.states[LANES[1]]['theta'])
        self.assertEqual(model.update,0)
        self.assertAlmostEqual((model.states[LANES[0]]['theta'][0,0]-before[LANES[0]]['theta'][0,0])%(2*np.pi),np.pi/2)

    def test_set_brush_takes_short_path_through_angle_seam(self):
        model = Sandbox(1,16)
        for state in model.states.values():state['theta'][:] = 2*np.pi-.1
        model.paint(8,8,4,.1,'set')
        for state in model.states.values():
            self.assertAlmostEqual(state['theta'][8,8],.1)
            self.assertLess(abs(np.angle(np.exp(1j*state['theta'][8,10]))),.11)

    def test_export_replay_recovers_both_full_states_exactly(self):
        model = Sandbox(42,16)
        model.advance(17);model.paint(4,5,3,.4,'set')
        model.paint(9,10,2,1.2,'turn');model.advance(9)
        model.paint(3,2,2,-.3,'turn');model.advance(4)
        with workspace_temporary() as temporary:
            folder = Path(temporary)/'bundle'
            export_bundle(model,folder,'C')
            recipe = json.loads((folder/'recipe.json').read_text())
            replay = Sandbox.replay(recipe)
            self.assertEqual(recipe['visible_field'],'C')
            self.assertEqual(replay.update,30)
            with np.load(folder/'fields.npz') as snapshot:
                for name in LANES:
                    for key,value in model.states[name].items():
                        np.testing.assert_array_equal(value,replay.states[name][key])
                        np.testing.assert_array_equal(value,snapshot[f'{name}_{key}'])
            with Image.open(folder/'pattern.png') as image:
                # Export uses nearest-neighbor scaling and the same fixed colors as the UI.
                np.testing.assert_array_equal(np.asarray(image)[94:734:40,24:664:40],pixels(model.states[LANES[0]],'C'))
            with self.assertRaises(FileExistsError):export_bundle(model,folder)
        np.testing.assert_array_equal(model.states['geometry_off']['ux'],np.zeros((16,16)))

    def test_replay_rejects_different_sources_and_out_of_order_edits(self):
        model = Sandbox(1,16);model.advance(4);model.paint(2,2)
        recipe = model.recipe();recipe['source_sha256'] = {}
        with self.assertRaisesRegex(ValueError,'fingerprints'):Sandbox.replay(recipe)
        recipe = model.recipe();recipe['edits'][0]['update'] = 5
        with self.assertRaisesRegex(ValueError,'ordered'):Sandbox.replay(recipe)


class SandboxUiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.temporary = workspace_temporary()
        self.window = SandboxWindow(Sandbox(1,16),Path(self.temporary.name))
        self.window.show();self.app.processEvents();self.window.timer.stop()

    def tearDown(self):
        self.window.close();self.window.deleteLater();self.app.processEvents()
        self.temporary.cleanup()

    def test_play_pause_step_queue_and_seed_reset(self):
        w = self.window
        QTest.mouseClick(w.play_button,Qt.LeftButton);w.tick()
        self.assertEqual(w.model.update,5)
        QTest.mouseClick(w.play_button,Qt.LeftButton);w.tick()
        self.assertEqual(w.model.update,5)
        QTest.mouseClick(w.step_button,Qt.LeftButton)
        self.assertEqual(w.model.update,6)
        QTest.mouseClick(w.grow_button,Qt.LeftButton);w.tick()
        self.assertEqual(w.remaining,995)
        w.seed.setText('42');QTest.mouseClick(w.reset_button,Qt.LeftButton)
        self.assertEqual((w.model.seed,w.model.update,w.remaining),(42,0,0))
        expected = Sandbox(42,16)
        np.testing.assert_array_equal(w.model.states[LANES[0]]['theta'],expected.states[LANES[0]]['theta'])
        w.seed.setText('-1');QTest.mouseClick(w.reset_button,Qt.LeftButton)
        self.assertEqual(w.model.seed,42)
        self.assertIn('Cannot reset',w.message.text())

    def test_native_click_and_drag_pause_and_edit_the_expected_rows(self):
        w = self.window;canvas = w.canvases[1]
        before = w.model.states[LANES[0]]['theta'].copy()
        w.mode.setCurrentIndex(1);w.radius.setValue(1)
        rect = canvas.square()
        def position(x,y):
            return QPoint(int(rect.left()+(x+.5)*rect.width()/16),int(rect.top()+(15-y+.5)*rect.height()/16))
        QTest.mouseClick(w.play_button,Qt.LeftButton)
        QTest.mousePress(canvas,Qt.LeftButton,pos=position(2,3))
        self.assertFalse(w.playing)
        move = QMouseEvent(QEvent.MouseMove,QPointF(position(5,3)),Qt.NoButton,Qt.LeftButton,Qt.NoModifier)
        self.app.sendEvent(canvas,move)
        QTest.mouseRelease(canvas,Qt.LeftButton,pos=position(5,3))
        after = w.model.states[LANES[0]]['theta']
        changed = np.argwhere(after != before)
        np.testing.assert_array_equal(changed,np.array([[3,2],[3,3],[3,4],[3,5]]))
        np.testing.assert_array_equal(after,w.model.states[LANES[1]]['theta'])
        self.assertEqual(w.model.update,0)
        w.view.setCurrentIndex(1)
        QTest.mouseClick(canvas,Qt.LeftButton,pos=position(8,8))
        np.testing.assert_array_equal(w.model.states[LANES[0]]['theta'],after)

    def test_export_control_saves_current_view_and_pauses(self):
        w = self.window
        w.model.advance(5);w.view.setCurrentIndex(1)
        QTest.mouseClick(w.play_button,Qt.LeftButton)
        QTest.mouseClick(w.export_button,Qt.LeftButton)
        self.assertFalse(w.playing)
        self.assertTrue((w.last_export/'pattern.png').is_file())
        recipe = json.loads((w.last_export/'recipe.json').read_text())
        self.assertEqual((recipe['visible_field'],recipe['update']),('C',5))


if __name__ == '__main__':unittest.main()
