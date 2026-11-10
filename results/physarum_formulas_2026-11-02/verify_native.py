import os,sys,json
from pathlib import Path
os.environ['QT_QPA_PLATFORM']='windows'
os.environ['OPENBLAS_NUM_THREADS']='1'
sys.path.insert(0,str(Path.cwd()))
from dataclasses import replace
import numpy as np
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer
from src.physarum_lab.adapters.desktop import StudioWindow
from src.physarum_lab.adapters.storage import save_bundle,load_bundle
from src.physarum_lab.domain.model import Simulation,PRESETS
from src.physarum_lab.application.session import Session
from src.physarum_lab.adapters.formula_editor import EXAMPLES
app=QApplication([])
root=Path('results/physarum_formulas_2026-11-02')
s=Simulation(7,replace(PRESETS['Silk'],size=512,agents=90000));s.step(160)
w=StudioWindow(Session(s,playing=False),output=root/'exports');w.show();w.timer.stop();w.formula_button.click()
e=w.formula_editor;e.move(900,35)
def capture():
 try:
  e.scalar.setPlainText('sin(12*sqrt(x*x + y*y) - 2*t)')
  before=s.snapshot();e.preview_button.click()
  assert s.formula is None and s.tick==before['tick']
  assert s.rng.bit_generator.state==before['rng']
  assert not e.preview_label.pixmap().isNull()
  e.apply_button.click();assert s.formula.spec.expression==e.scalar.toPlainText()
  e.grab().save(str(root/'editor.png'))
  for _ in range(160):w.session.advance(force=True)
  w.refresh();app.processEvents();assert w.canvas.gpu is not None
  w.canvas.gpu.native.grabFramebuffer().save(str(root/'formula_field.png'))
  w.grab().save(str(root/'window.png'))
  saved_spec=s.formula.spec
  e.scalar.setPlainText('__import__("os")');e.apply_button.click();assert s.formula.spec==saved_spec
  e.set_spec(EXAMPLES['Vortex current']);e.preview();e.apply();assert s.formula.spec.response=='flow'
  for _ in range(12):w.session.advance(force=True)
  w.refresh();app.processEvents();e.grab().save(str(root/'vector_editor.png'))
  w.export();assert w.last_export
  loaded,_=load_bundle(w.last_export)
  w.session.advance(5,force=True);loaded.advance(5,force=True)
  for key in ('x','y','heading','trail','density'):np.testing.assert_array_equal(getattr(s,key),getattr(loaded.simulation,key))
  qa=dict(platform=app.platformName(),gpu=True,scalar_apply=True,preview_preserves_state=True,
    invalid_expression_preserves_active_formula=True,vector_apply=True,exact_formula_continuation=True,
    export=str(w.last_export),tick=s.tick)
  (root/'qa.json').write_text(json.dumps(qa,indent=2)+'\n',encoding='utf-8');print(json.dumps(qa),flush=True)
 except Exception:
  import traceback;traceback.print_exc();sys.exit(1)
 finally:w.close();e.close();app.quit()
QTimer.singleShot(800,capture)
app.exec_()
