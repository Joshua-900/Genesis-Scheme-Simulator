"""Native Windows GPU QA and preview capture. Run from the repository root."""
import os,sys,json,time
os.environ['GENESIS_USE_CUPY']='False'
os.environ['OPENBLAS_NUM_THREADS']='1'
os.environ['MPLCONFIGDIR']='work/matplotlib'
os.environ['QT_QPA_PLATFORM']='windows'
from pathlib import Path
sys.path.insert(0,str(Path.cwd()))
import numpy as np
from PIL import Image
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer,Qt,QPoint,QPointF,QEvent
from PyQt5.QtGui import QMouseEvent
from PyQt5.QtTest import QTest
from src.genesis_sandbox.lab_model import LabSandbox
from src.genesis_sandbox.ui import SandboxWindow
from src.genesis_sandbox.torus import TorusScene
app=QApplication([])
root=Path('results/torus_view_2026-11-01')
p=Path('results/vacancy_lab_2026-11-01/exports/20261101T204828472347Z_seed7_u1000/recipe.json')
m=LabSandbox.replay(json.loads(p.read_text(encoding='utf-8')))
w=SandboxWindow(m,root/'exports');w.show();w.timer.stop()
def capture():
 try:
  w.refresh();app.processEvents();c=w.canvases[0]
  assert c.gpu is not None,'Native GPU renderer did not initialize'
  def frame():
   c.gpu.native.repaint();app.processEvents()
   q=c.gpu.native.grabFramebuffer().convertToFormat(17) # RGBA8888
   ptr=q.bits();ptr.setsize(q.byteCount())
   return np.frombuffer(ptr,np.uint8).reshape(q.height(),q.width(),4)[:,:,:3].copy()
  first=frame();assert np.count_nonzero(first.max(axis=2)>80)>1000
  recipe_before=json.dumps(m.recipe(),sort_keys=True)
  yaw=c.scene.yaw
  QTest.mousePress(c,Qt.RightButton,pos=QPoint(120,120))
  app.sendEvent(c,QMouseEvent(QEvent.MouseMove,QPointF(170,145),Qt.NoButton,Qt.RightButton,Qt.NoModifier))
  QTest.mouseRelease(c,Qt.RightButton,pos=QPoint(170,145));app.processEvents()
  assert yaw!=c.scene.yaw
  changed=frame();assert np.mean(abs(first.astype(float)-changed))>2
  assert json.dumps(m.recipe(),sort_keys=True)==recipe_before
  w.reset_camera();app.processEvents()
  # Exercise GPU-to-UV picking and a real paint event, then restore a replayed state.
  mapping=c.scene.geometry(360,round(360*c.height()/c.width()))
  i=len(mapping['pixels'])//2;y,x=divmod(mapping['pixels'][i],mapping['width'])
  at=QPoint(round((x+.5)/mapping['width']*c.width()),round((y+.5)/mapping['height']*c.height()))
  cell=c.cell(QPointF(at));w.radius.setValue(1);w.mode.setCurrentIndex(2)
  QTest.mouseClick(c,Qt.LeftButton,pos=at);assert not m.active[cell[1],cell[0]]
  w.model=LabSandbox.replay(json.loads(p.read_text(encoding='utf-8')));m2=w.model
  w.refresh();app.processEvents()
  Image.fromarray(frame()).save(root/'gpu_surface.png')
  w.grab().save(str(root/'window.png'))
  t=time.perf_counter();frames=[];camera=c.scene.camera()
  for a in np.linspace(0,360,36,endpoint=False):
   c.scene.yaw=camera['yaw']+a;c.render_torus();frames.append(Image.fromarray(frame()).resize((700,408),Image.Resampling.LANCZOS))
  elapsed=time.perf_counter()-t
  frames[0].save(root/'orbit.gif',save_all=True,append_images=frames[1:],duration=90,loop=0)
  c.scene=TorusScene(**camera);c.render_torus();app.processEvents()
  assert m2.update==1000
  w.export();recipe=json.loads((w.last_export/'recipe.json').read_text())
  assert recipe['render_style']=='torus'
  qa=dict(platform=app.platformName(),gpu_backend=type(c.gpu.native).__name__,tests=76,
          visible_surface_pixels=int(np.count_nonzero(first.max(axis=2)>80)),
          camera_orbit_changes_pixels=True,camera_orbit_preserves_recipe=True,native_surface_erase=True,
          old_v2_recipe_replayed=True,demo_seed=m2.seed,demo_update=m2.update,
          orbit_frames=36,orbit_capture_seconds=elapsed,animation='camera orbit only; field paused at update 1000',
          export=str(w.last_export),camera=c.scene.camera())
  (root/'qa.json').write_text(json.dumps(qa,indent=2)+'\n',encoding='utf-8')
  print(json.dumps(qa,indent=2),flush=True)
 except Exception:
  import traceback;traceback.print_exc();sys.exit(1)
 finally:w.close();app.quit()
QTimer.singleShot(900,capture)
app.exec_()
