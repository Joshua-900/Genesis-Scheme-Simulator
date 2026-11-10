"""Reproduce native GPU checks from the repository root. No computer-use needed."""
import os,sys,json,time
from pathlib import Path
os.environ['QT_QPA_PLATFORM']='windows'
os.environ['OPENBLAS_NUM_THREADS']='1'
sys.path.insert(0,str(Path.cwd()))
import numpy as np
from PIL import Image
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer,Qt,QPoint,QPointF,QEvent
from PyQt5.QtGui import QMouseEvent,QWheelEvent
from PyQt5.QtTest import QTest
from src.physarum_lab.adapters.desktop import StudioWindow
from src.physarum_lab.adapters.storage import load_bundle,save_bundle
from src.physarum_lab.adapters.render import render
root=Path('results/physarum_lab_2026-11-02')
app=QApplication([])
session,look=load_bundle(root/'flow_state')
w=StudioWindow(session,look,root/'native_exports');w.show();w.timer.stop()
def capture():
 try:
  w.refresh();app.processEvents();c=w.canvas
  assert c.gpu is not None,'Native GPU did not initialize'
  def frame():
   c.gpu.native.repaint();app.processEvents()
   q=c.gpu.native.grabFramebuffer().convertToFormat(17)
   ptr=q.bits();ptr.setsize(q.byteCount())
   return np.frombuffer(ptr,np.uint8).reshape(q.height(),q.width(),4)[:,:,:3].copy()
  rgb=frame();assert np.count_nonzero(rgb.max(axis=2)>80)>5000
  h,b=rgb.shape[:2];side=min(h,b);x=(b-side)//2;y=(h-side)//2
  art=rgb[y:y+side,x:x+side]
  Image.fromarray(art).save(root/'native_artwork.png');w.grab().save(str(root/'window.png'))
  reference=np.asarray(render(w.session.simulation,w.look,side=side))
  mae=float(np.mean(abs(art.astype(float)-reference)))
  assert mae<9,(mae,'GPU and reference disagree')
  before=w.session.simulation.snapshot()
  w.palette.setCurrentText('Ember');app.processEvents();other=frame()
  assert np.mean(abs(rgb.astype(float)-other))>2
  assert w.session.simulation.rng.bit_generator.state==before['rng']
  wheel=QWheelEvent(QPointF(300,300),QPointF(c.mapToGlobal(QPoint(300,300))),QPoint(),QPoint(0,120),Qt.NoButton,Qt.NoModifier,Qt.NoScrollPhase,False)
  app.sendEvent(c,wheel);assert c.zoom>1
  QTest.mousePress(c,Qt.RightButton,pos=QPoint(300,300))
  app.sendEvent(c,QMouseEvent(QEvent.MouseMove,QPointF(350,325),Qt.NoButton,Qt.RightButton,Qt.NoModifier))
  QTest.mouseRelease(c,Qt.RightButton,pos=QPoint(350,325))
  assert not np.array_equal(c.center,[.5,.5])
  assert w.session.simulation.tick==before['tick']
  w.fit_view();w.palette.setCurrentText('Pearl')
  w.gather.click();assert w.session.target_guidance==1
  for _ in range(20):w.session.advance(force=True)
  assert abs(w.session.guidance-.2)<1e-6
  w.export();assert w.last_export is not None
  restored,appearance=load_bundle(w.last_export)
  assert restored.guidance==w.session.guidance
  # Restore the flowing demo for a useful ready-to-explore launch state.
  w.load_state(root/'flow_state');w.timer.stop()
  w.session.playing=True
  start=time.perf_counter()
  for _ in range(80):w.tick();app.processEvents()
  elapsed=time.perf_counter()-start
  assert w.session.simulation.tick==before['tick']+80
  w.session.playing=False;w.refresh()
  records={}
  for phase in ('flow','gather','release'):
   saved,_=load_bundle(root/f'{phase}_state');s=saved.simulation
   records[phase]=dict(tick=s.tick,guidance=saved.guidance,
     mean_squared_wave_at_agents=float(np.mean(s.wave[s.y.astype(int),s.x.astype(int)]**2)))
  qa=dict(platform=app.platformName(),gpu=True,gpu_reference_mean_absolute_error=mae,
    native_palette_change=True,native_zoom_pan=True,camera_preserves_tick=True,
    native_guidance_transition=True,native_export_restore=True,
    measured_updates=80,update_display_seconds=elapsed,updates_per_second=80/elapsed,
    seed=before['seed'],agents=w.session.simulation.rules.agents,size=w.session.simulation.rules.size,
    phases=records,animation='real simulation evolution, sampled every 16 ticks; playback is time-compressed')
  (root/'qa.json').write_text(json.dumps(qa,indent=2)+'\n',encoding='utf-8')
  print(json.dumps(qa,indent=2),flush=True)
 except Exception:
  import traceback;traceback.print_exc();sys.exit(1)
 finally:w.close();app.quit()
QTimer.singleShot(600,capture)
app.exec_()
