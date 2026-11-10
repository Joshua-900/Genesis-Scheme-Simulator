"""Vacancies change actual connectivity; random switching and exports replay."""
import copy
import json
import os
from pathlib import Path
import tempfile
import unittest

os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
import numpy as np
from PIL import Image
from PyQt5.QtCore import Qt,QPoint
from PyQt5.QtTest import QTest
from PyQt5.QtWidgets import QApplication

from src.genesis_sandbox import vacancies
from src.genesis_sandbox.model import ROOT,LANES,Sandbox
from src.genesis_sandbox.lab_model import LabSandbox
from src.genesis_sandbox.export import export_bundle
from src.genesis_sandbox.render import dash_pixels
from src.genesis_sandbox.ui import SandboxWindow


def temporary():
    p=ROOT/'work/vacancy_tests';p.mkdir(parents=True,exist_ok=True)
    return tempfile.TemporaryDirectory(dir=p)


class VacancyTests(unittest.TestCase):
    def test_all_occupied_trajectory_is_classic_bitwise(self):
        classic=Sandbox(7,16);lab=LabSandbox(7,16)
        classic.advance(80);lab.advance(80)
        for name in LANES:
            for key in vacancies.FIELDS:np.testing.assert_array_equal(classic.states[name][key],lab.states[name][key])

    def test_removed_state_is_cleared_and_return_is_a_fresh_shared_angle(self):
        lab=LabSandbox(1,16);lab.advance(10)
        lab.presence([[3,4]])
        for state in lab.states.values():
            self.assertFalse(state['active'][4,3])
            for key in vacancies.FIELDS:self.assertEqual(state[key][4,3],0.)
        lab.presence([[3,4]],True,[1.234])
        for state in lab.states.values():
            self.assertTrue(state['active'][4,3]);self.assertEqual(state['theta'][4,3],1.234)
            for key in ('tau','ux','uy','C'):self.assertEqual(state[key][4,3],0.)

    def test_hole_payload_has_no_effect_on_active_cells(self):
        lab=LabSandbox(9,16);lab.presence([[7,8],[8,8]])
        a=copy.deepcopy(lab.states[LANES[0]]);b=copy.deepcopy(a)
        for key in vacancies.FIELDS:b[key][~b['active']]=np.nan
        for _ in range(15):
            vacancies.step(a,lab.parameters[LANES[0]]);vacancies.step(b,lab.parameters[LANES[0]])
        for key in vacancies.FIELDS:np.testing.assert_array_equal(a[key],b[key])

    def test_complete_hole_barriers_disconnect_the_two_regions(self):
        lab=LabSandbox(5,16)
        lab.presence([[x,y] for y in range(16) for x in (7,15)])
        a=copy.deepcopy(lab.states[LANES[0]]);b=copy.deepcopy(a)
        b['theta'][:,8:15]=(b['theta'][:,8:15]+1.1)%(2*np.pi)
        for _ in range(15):
            vacancies.step(a,lab.parameters[LANES[0]]);vacancies.step(b,lab.parameters[LANES[0]])
        for key in vacancies.FIELDS:np.testing.assert_array_equal(a[key][:,:7],b[key][:,:7])

    def test_simultaneous_switching_does_not_return_newly_removed_sites(self):
        lab=LabSandbox(2,16);lab.set_rates(1.,1.)
        lab.advance(1);self.assertEqual(int(lab.active.sum()),0)
        for state in lab.states.values():
            for key in vacancies.FIELDS:np.testing.assert_array_equal(state[key],np.zeros((16,16)))
        lab.advance(1);self.assertEqual(int(lab.active.sum()),256)
        self.assertEqual((lab.dropped,lab.arrived),(256,256))

    def test_switching_density_follows_the_two_state_formula(self):
        lab=LabSandbox(4,16);lab.set_rates(.02,.06)
        counts=[]
        for tick in range(220):
            lab.advance()
            if tick>=100:counts.append(lab.active.mean())
        self.assertAlmostEqual(float(np.mean(counts)),.06/(.02+.06),delta=.05)

    def test_event_recipe_replays_exactly_and_can_continue(self):
        lab=LabSandbox(42,16);lab.set_rates(.03,.06);lab.advance(9)
        lab.random_presence(8);lab.random_presence(3,True)
        lab.presence_brush(4,5,2);lab.paint(7,8,3,.6,'set');lab.advance(7)
        lab.presence_brush(4,5,2,True);lab.set_rates(.01,.02);lab.advance(5)
        with temporary() as tmp:
            folder=Path(tmp)/'lab'
            export_bundle(lab,folder,'theta','dashes')
            recipe=json.loads((folder/'recipe.json').read_text())
            replay=LabSandbox.replay(recipe)
            self.assertEqual(recipe['version'],2)
            for name in LANES:
                for key in lab.states[name]:np.testing.assert_array_equal(lab.states[name][key],replay.states[name][key])
            self.assertEqual((lab.dropped,lab.arrived),(replay.dropped,replay.arrived))
            lab.advance(3);replay.advance(3)
            lab.random_presence(1,True);replay.random_presence(1,True)
            for name in LANES:
                for key in lab.states[name]:np.testing.assert_array_equal(lab.states[name][key],replay.states[name][key])

    def test_old_version_one_recipes_remain_replayable(self):
        classic=Sandbox(7,16);classic.advance(5);classic.paint(4,5)
        replay=Sandbox.replay(json.loads(json.dumps(classic.recipe())))
        np.testing.assert_array_equal(classic.states[LANES[0]]['theta'],replay.states[LANES[0]]['theta'])

    def test_absent_dash_has_no_glyph_when_event_flash_fades(self):
        lab=LabSandbox(1,16);lab.presence([[3,4]])
        state=lab.states[LANES[0]];state['flash'][:]=0
        rgb=dash_pixels(state,8)
        hole=rgb[(15-4)*8:(16-4)*8,3*8:4*8]
        np.testing.assert_array_equal(hole,np.broadcast_to([3,8,15],hole.shape))


class VacancyUiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.app=QApplication.instance() or QApplication([])

    def test_zoomed_erase_add_mapping_and_visible_view_export(self):
        with temporary() as tmp:
            w=SandboxWindow(LabSandbox(1,16),Path(tmp));w.show();self.app.processEvents();w.timer.stop()
            try:
                w.render_style.setCurrentIndex(w.render_style.findData('dashes'));w.zoom.setCurrentIndex(1);w.radius.setValue(1);w.mode.setCurrentIndex(2)
                self.app.processEvents();canvas=w.canvases[0];r=canvas.square()
                x,y=5,6;span=8
                point=QPoint(int(r.left()+((x+.5-8)/span+.5)*r.width()),
                             int(r.top()+((15-y+.5-8)/span+.5)*r.height()))
                QTest.mouseClick(canvas,Qt.LeftButton,pos=point)
                self.assertFalse(w.model.active[y,x]);self.assertEqual(int(w.model.active.sum()),255)
                w.mode.setCurrentIndex(3);QTest.mouseClick(canvas,Qt.LeftButton,pos=point)
                self.assertTrue(w.model.active[y,x]);self.assertEqual(int(w.model.active.sum()),256)
                w.export_button.click()
                recipe=json.loads((w.last_export/'recipe.json').read_text())
                self.assertEqual(recipe['view_zoom'],2);self.assertFalse(recipe['compare_view'])
                with Image.open(w.last_export/'pattern.png') as image:self.assertEqual(image.width,688)
            finally:w.close();w.deleteLater();self.app.processEvents()

    def test_controls_change_presence_while_playing_and_export_current_style(self):
        with temporary() as tmp:
            w=SandboxWindow(LabSandbox(1,16),Path(tmp));w.show();self.app.processEvents();w.timer.stop()
            try:
                w.tabs.setCurrentIndex(1);self.app.processEvents()
                w.playing=True
                w.drop_one_button.click()
                self.assertEqual(int(w.model.active.sum()),255);self.assertTrue(w.playing)
                w.add_one_button.click();self.assertEqual(int(w.model.active.sum()),256)
                w.flicker_button.click();self.assertAlmostEqual(w.model.drop_probability,.002)
                self.assertAlmostEqual(w.model.return_probability,.006);self.assertIn('75%',w.density_hint.text())
                w.tick();w.calm_button.click();self.assertEqual(w.model.drop_probability,0.)
                QTest.mouseClick(w.export_button,Qt.LeftButton)
                recipe=json.loads((w.last_export/'recipe.json').read_text())
                self.assertEqual(recipe['render_style'],'torus');self.assertFalse(w.playing)
                replay=LabSandbox.replay(recipe)
                np.testing.assert_array_equal(w.model.active,replay.active)
            finally:w.close();w.deleteLater();self.app.processEvents()


if __name__=='__main__':unittest.main()
