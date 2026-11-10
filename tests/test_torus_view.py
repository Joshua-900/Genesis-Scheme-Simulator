"""Geometry, presentation isolation and native interaction contracts for torus view."""
import os
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
os.environ.setdefault('GENESIS_USE_CUPY','False')
import copy,json,tempfile,unittest
from pathlib import Path
import numpy as np
from PyQt5.QtCore import Qt,QPoint,QPointF,QEvent
from PyQt5.QtGui import QMouseEvent,QWheelEvent
from PyQt5.QtTest import QTest
from PyQt5.QtWidgets import QApplication
from src.genesis_sandbox.torus import TorusScene,point,uv,TAU
from src.genesis_sandbox.lab_model import LabSandbox
from src.genesis_sandbox.model import LANES,ROOT
from src.genesis_sandbox.ui import SandboxWindow
from src.genesis_sandbox.export import export_bundle

class TorusTests(unittest.TestCase):
 def test_surface_identifies_both_periodic_edges_and_roundtrips(self):
  u=np.array([.1,1.2,3.4,6.1]);v=np.array([.3,2.,4.,6.])
  np.testing.assert_allclose(point(u+TAU,v),point(u,v),atol=1e-14)
  np.testing.assert_allclose(point(u,v+TAU),point(u,v),atol=1e-14)
  np.testing.assert_allclose(uv(point(u,v)),np.stack((u,v),axis=-1),atol=1e-14)

 def test_visible_pixels_pick_their_actual_uv_and_background_is_empty(self):
  s=TorusScene();m=s.geometry(160,120);n=16
  for index in np.linspace(0,len(m['pixels'])-1,30).astype(int):
   y,x=divmod(m['pixels'][index],160)
   self.assertEqual(s.pick(x,y,n),tuple((m['uv'][index]/TAU*n).astype(int)%n))
   self.assertEqual(s.pick_screen(x,y,160,120,n),s.pick(x,y,n))
  self.assertIsNone(s.pick(0,0,n));self.assertIsNone(s.pick(-1,0,n))
  # The center is a real opening for a face-on torus.
  s=TorusScene(tilt=90,roll=0);s.geometry(160,160)
  self.assertIsNone(s.pick(80,80,n))

 def test_render_changes_with_camera_and_vacancies_without_mutating_model(self):
  lab=LabSandbox(7,16);before=copy.deepcopy(lab.recipe())
  state=lab.states[LANES[0]];snapshot=copy.deepcopy(state)
  scene=TorusScene();a=scene.render(state,width=180,height=140)
  scene.orbit(35,10);b=scene.render(state,width=180,height=140)
  self.assertEqual(a.shape,(140,180,3));self.assertEqual(a.dtype,np.uint8)
  self.assertGreater(np.mean(abs(a.astype(float)-b)),3)
  for k in state:np.testing.assert_array_equal(state[k],snapshot[k])
  self.assertEqual(lab.recipe(),before)
  empty=copy.deepcopy(state);empty['active'][:]=False
  c=scene.render(empty,width=180,height=140)
  self.assertGreater(float(b.mean()),float(c.mean()))

 def test_torus_export_records_camera_and_replays_exact_dynamics(self):
  lab=LabSandbox(4,16);lab.advance(3);lab.presence([[2,3]])
  camera=dict(yaw=12.,tilt=65.,roll=-9.,zoom=1.2)
  root=ROOT/'work/torus_tests';root.mkdir(parents=True,exist_ok=True)
  with tempfile.TemporaryDirectory(dir=root) as tmp:
   folder=export_bundle(lab,Path(tmp)/'export',style='torus',compare=False,camera=camera,seams=True)
   recipe=json.loads((folder/'recipe.json').read_text())
   self.assertEqual(recipe['torus_camera'],camera);self.assertTrue(recipe['show_seams'])
   replay=LabSandbox.replay(recipe)
   for lane in LANES:
    for key in lab.states[lane]:np.testing.assert_array_equal(lab.states[lane][key],replay.states[lane][key])

class TorusUiTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.app=QApplication.instance() or QApplication([])
 def test_orbit_zoom_and_surface_erase_use_camera_without_advancing_time(self):
  w=SandboxWindow(LabSandbox(7,16));w.show();self.app.processEvents();w.timer.stop()
  try:
   c=w.canvases[0];self.assertEqual(c.style,'torus');self.assertFalse(w.zoom.isEnabled())
   before=copy.deepcopy(w.model.recipe());yaw=c.scene.yaw
   QTest.mousePress(c,Qt.RightButton,pos=QPoint(120,120))
   self.app.sendEvent(c,QMouseEvent(QEvent.MouseMove,QPointF(150,130),Qt.NoButton,Qt.RightButton,Qt.NoModifier))
   QTest.mouseRelease(c,Qt.RightButton,pos=QPoint(150,130))
   self.assertNotEqual(c.scene.yaw,yaw);self.assertEqual(w.model.recipe(),before)
   zoom=c.scene.zoom
   wheel=QWheelEvent(QPointF(150,130),QPointF(c.mapToGlobal(QPoint(150,130))),QPoint(),QPoint(0,120),Qt.NoButton,Qt.NoModifier,Qt.NoScrollPhase,False)
   self.app.sendEvent(c,wheel);self.assertGreater(c.scene.zoom,zoom)
   m=c.scene.mapping;i=len(m['pixels'])//2;y,x=divmod(m['pixels'][i],m['width'])
   screen=QPoint(round((x+.5)/m['width']*c.width()),round((y+.5)/m['height']*c.height()))
   cell=c.cell(QPointF(screen));self.assertIsNotNone(cell)
   w.radius.setValue(1);w.mode.setCurrentIndex(2)
   QTest.mouseClick(c,Qt.LeftButton,pos=screen)
   self.assertFalse(w.model.active[cell[1],cell[0]]);self.assertEqual(w.model.update,0)
   w.reset_camera();self.assertEqual(c.scene.camera(),TorusScene().camera())
  finally:w.close();w.deleteLater();self.app.processEvents()

if __name__=='__main__':unittest.main()
