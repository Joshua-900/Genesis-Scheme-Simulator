"""Native creative sandbox; timer and editing controls never alter the rules."""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import matplotlib
import numpy as np
from PyQt5.QtCore import QPointF, QRectF, Qt, QTimer, QUrl, pyqtSignal
from PyQt5.QtGui import QColor, QFont, QFontDatabase, QImage, QPainter, QPen, QPixmap
from PyQt5.QtWidgets import (
    QApplication, QComboBox, QFrame, QHBoxLayout, QLabel, QLineEdit, QMainWindow,
    QPushButton, QSizePolicy, QSlider, QVBoxLayout, QWidget, QScrollArea, QTabWidget, QDoubleSpinBox, QCheckBox,
)

from .export import export_bundle, pixels
from .model import LABELS, LANES, ROOT, Sandbox
from .lab_model import LabSandbox
from .render import dash_pixels,phase_colors
from .torus import TorusScene


class FieldCanvas(QWidget):
    started = pyqtSignal()
    stamped = pyqtSignal(float, float)
    finished = pyqtSignal()
    camera_changed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(260,260)
        self.setSizePolicy(QSizePolicy.Expanding,QSizePolicy.Expanding)
        self.setMouseTracking(True)
        self.image = None
        self.n, self.radius, self.editable,self.zoom = 64, 4, True,1
        self.hover = None
        self.gpu = None
        self.gpu_attempted = False
        self.scene = TorusScene()
        self.style = 'dashes'
        self.state = None
        self.field = 'theta'
        self.seams = False
        self.preview = False
        self.drag = None
        self.settle = QTimer(self)
        self.settle.setSingleShot(True)
        self.settle.timeout.connect(self.render_torus)

    def gpu_failed(self):
        if self.gpu is not None:self.gpu.native.hide()
        self.gpu = None
        self.settle.start(1)

    def render_torus(self, preview=False):
        if self.style != 'torus' or self.state is None:return
        if not self.gpu_attempted:
            self.gpu_attempted = True
            if QApplication.platformName() != 'offscreen':
                try:
                    from .torus_gl import TorusGPU
                    self.gpu = TorusGPU(self,self.gpu_failed)
                    self.gpu.native.setAttribute(Qt.WA_TransparentForMouseEvents)
                except Exception:
                    import logging
                    logging.exception('Torus GPU unavailable; using software')
                    self.gpu_failed()
        if self.gpu is not None:
            self.gpu.native.setGeometry(self.rect());self.gpu.native.show()
            self.gpu.set_field(self.state,self.field,self.scene,self.seams)
            self.update();return
        limit = 460 if preview or self.preview else 800
        ratio = min(1., limit/max(self.width(),self.height()))
        width,height = max(1,round(self.width()*ratio)),max(1,round(self.height()*ratio))
        rgb = self.scene.render(self.state,self.field,width,height,self.seams)
        self.image = QImage(rgb.data,width,height,3*width,QImage.Format_RGB888).copy()
        self.update()

    def resizeEvent(self,event):
        super().resizeEvent(event)
        if self.style == 'torus':self.settle.start(120)

    def set_field(self, state, field,style='dashes'):
        self.style,self.state,self.field = style,state,field
        self.n = len(state['theta'])
        self.editable = field == 'theta'
        if style == 'torus':
            self.setCursor(Qt.CrossCursor if self.editable else Qt.OpenHandCursor)
            self.render_torus()
            return
        if self.gpu is not None:self.gpu.native.hide()
        self.viewport_image=style=='dashes' and field=='theta'
        rgb = dash_pixels(state,zoom=self.zoom) if self.viewport_image else pixels(state,field)
        self.n = len(state['theta']);side=len(rgb)
        self.image = QImage(rgb.data,side,side,3*side,QImage.Format_RGB888).copy()
        self.editable = field == 'theta'
        self.setCursor(Qt.CrossCursor if self.editable else Qt.ForbiddenCursor)
        self.update()

    def square(self):
        side = min(self.width(),self.height())-2
        return QRectF((self.width()-side)/2,(self.height()-side)/2,side,side)

    def cell(self, position):
        if self.style == 'torus':
            return self.scene.pick_screen(position.x(),position.y(),self.width(),self.height(),self.n)
        rect = self.square()
        if not rect.contains(position):
            return None
        x = min(self.n-1,int(self.n/2+((position.x()-rect.left())/rect.width()-.5)*self.n/self.zoom))
        y = self.n-1-min(self.n-1,int(self.n/2+((position.y()-rect.top())/rect.height()-.5)*self.n/self.zoom))
        return x,y

    def paintEvent(self,event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)
        rect = self.square()
        if self.style == 'torus':
            if self.gpu is not None:return
            if self.image is not None:painter.drawImage(QRectF(self.rect()),self.image)
            if self.hover is not None and self.editable and self.cell(self.hover) is not None:
                painter.setRenderHint(QPainter.Antialiasing)
                painter.setPen(QPen(QColor('#d4fffa'),1))
                painter.drawEllipse(self.hover,5,5)
            return
        if self.image is not None:
            width=self.image.width();crop=width if self.viewport_image else width/self.zoom
            painter.drawImage(rect,self.image,QRectF((width-crop)/2,(width-crop)/2,crop,crop))
        painter.setPen(QPen(QColor('#40555e'),1))
        painter.drawRect(rect)
        if self.hover is not None and self.editable and rect.contains(self.hover):
            painter.setRenderHint(QPainter.Antialiasing)
            radius = self.radius*rect.width()*self.zoom/self.n
            painter.setPen(QPen(QColor('#0b1318'),3))
            painter.drawEllipse(self.hover,radius,radius)
            painter.setPen(QPen(QColor('#ffffff'),1))
            painter.drawEllipse(self.hover,radius,radius)

    def mousePressEvent(self,event):
        if self.style == 'torus' and event.button() == Qt.RightButton:
            self.drag = event.localPos();self.setCursor(Qt.ClosedHandCursor);return
        point = self.cell(event.localPos())
        if event.button() == Qt.LeftButton and point is not None and self.editable:
            self.started.emit()
            self.stamped.emit(*point)

    def mouseMoveEvent(self,event):
        if self.drag is not None and event.buttons() & Qt.RightButton:
            delta = event.localPos()-self.drag;self.drag = event.localPos()
            self.scene.orbit(delta.x()*.45,delta.y()*.45)
            self.render_torus(True);self.camera_changed.emit();self.settle.start(140)
            return
        self.hover = event.localPos()
        self.update()
        point = self.cell(event.localPos())
        if event.buttons() & Qt.LeftButton and self.editable:
            if point is not None:self.stamped.emit(*point)
            else:self.finished.emit()

    def mouseReleaseEvent(self,event):
        if event.button() == Qt.RightButton:
            self.drag = None
            self.setCursor(Qt.CrossCursor if self.editable else Qt.OpenHandCursor)
            self.settle.start(30)
        if event.button() == Qt.LeftButton:
            self.finished.emit()

    def wheelEvent(self,event):
        if self.style != 'torus':return super().wheelEvent(event)
        self.scene.zoom = float(np.clip(self.scene.zoom*1.15**(event.angleDelta().y()/120),.65,3.5))
        self.render_torus(True);self.camera_changed.emit();self.settle.start(140)
        event.accept()

    def leaveEvent(self,event):
        self.hover = None
        self.update()


def caption(text):
    label = QLabel(text)
    label.setObjectName('caption')
    label.setWordWrap(True)
    return label


class SandboxWindow(QMainWindow):
    def __init__(self, model=None, export_root=None):
        super().__init__()
        self.model = LabSandbox.upgrade(model) if model is not None else LabSandbox()
        self.export_root = Path(export_root) if export_root else ROOT/'work/sandbox_exports'
        self.last_export = None
        self.playing, self.remaining, self.last_cell = False, 0, None
        self.setWindowTitle('Field Lab · Dash experiments')
        self.resize(1360,900)
        self.setMinimumSize(1000,760)
        family = 'Segoe UI'
        if family not in QFontDatabase().families():
            # Windows offscreen/sandbox sessions can expose no system fonts.
            # Matplotlib already ships these fonts with the project environment.
            for filename in ('DejaVuSans.ttf','DejaVuSans-Bold.ttf'):
                QFontDatabase.addApplicationFont(str(Path(matplotlib.get_data_path())/'fonts/ttf'/filename))
            family = 'DejaVu Sans'
        self.setFont(QFont(family,10))
        self.setStyleSheet('''
            QWidget { background:#0b111b; color:#e6eef0; }
            QFrame#panel { background:#101b29; border:1px solid #293d54; border-radius:8px; }
            QLabel { background:transparent; }
            QLabel#caption { color:#aabdc5; font-size:12px; }
            QLabel#title { font-size:26px; font-weight:600; }
            QLabel#lane { font-size:18px; font-weight:600; }
            QLabel#status { color:#b4e7d6; font-size:16px; font-weight:600; }
            QPushButton { background:#233740; border:1px solid #415761; padding:10px; border-radius:5px; }
            QPushButton:hover { background:#304a55; }
            QPushButton:pressed { background:#42616e; }
            QPushButton#primary { background:#b4e7d6; color:#142a25; font-weight:600; border:none; }
            QComboBox, QLineEdit { background:#1b2d35; border:1px solid #415761; padding:7px; border-radius:4px; }
            QSlider::groove:horizontal { height:4px; background:#3c555f; }
            QSlider::handle:horizontal { width:14px; margin:-6px 0; background:#b4e7d6; border-radius:7px; }
            QTabWidget::pane { border:1px solid #293d54; }
            QTabBar::tab { background:#182638; padding:9px; }
            QTabBar::tab:selected { background:#30435b; color:#aaf4e7; }
            QDoubleSpinBox { background:#1b2d35; padding:6px; border:1px solid #415761; }
            QScrollArea { border:none; }
            QScrollBar:vertical { background:#0b111b; width:8px; }
            QScrollBar::handle:vertical { background:#345068; min-height:30px; border-radius:4px; }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height:0; }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background:none; }
            QCheckBox::indicator { width:14px; height:14px; border:1px solid #587186; background:#101b29; }
            QCheckBox::indicator:checked { background:#9be7d7; }
        ''')
        root = QWidget()
        self.setCentralWidget(root)
        outer = QVBoxLayout(root)
        outer.setContentsMargins(24,20,24,20)
        outer.setSpacing(16)
        header = QHBoxLayout()
        title_box = QVBoxLayout()
        title = QLabel('FIELD / LAB');title.setObjectName('title')
        title_box.addWidget(title)
        title_box.addWidget(caption('Living dashes · real vacancies · fresh arrivals'))
        header.addLayout(title_box)
        header.addStretch()
        self.zoom=QComboBox();self.zoom.addItem('Full field',1);self.zoom.addItem('2× detail',2);self.zoom.addItem('4× detail',4)
        # New sessions begin with the whole torus in view.
        self.zoom.currentIndexChanged.connect(self.refresh);header.addWidget(self.zoom)
        self.compare=QCheckBox('Compare geometry')
        self.compare.setChecked(model is not None and not isinstance(model,LabSandbox))
        self.compare.toggled.connect(self.refresh);header.addWidget(self.compare)
        self.status = QLabel();self.status.setObjectName('status')
        header.addWidget(self.status)
        outer.addLayout(header)
        body = QHBoxLayout();body.setSpacing(20)
        outer.addLayout(body,1)
        sidebar = QWidget();sidebar.setFixedWidth(246)
        controls = QVBoxLayout(sidebar);controls.setContentsMargins(0,0,0,0);controls.setSpacing(12)
        scroll=QScrollArea();scroll.setWidgetResizable(True);scroll.setWidget(sidebar)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff);scroll.setFixedWidth(270)
        body.addWidget(scroll)
        controls.addWidget(caption('VACANCY EXPERIMENT  ·  MATCHED PAIR'))
        self.play_button = QPushButton('Play');self.play_button.setObjectName('primary')
        self.play_button.clicked.connect(self.toggle_play)
        controls.addWidget(self.play_button)
        row = QHBoxLayout()
        self.step_button = QPushButton('Step +1');self.step_button.clicked.connect(self.step_once)
        self.grow_button = QPushButton('Grow +1000');self.grow_button.clicked.connect(self.grow)
        row.addWidget(self.step_button);row.addWidget(self.grow_button);controls.addLayout(row)
        controls.addWidget(caption('Updates per frame'))
        self.speed = QComboBox()
        for count in (1,5,10,25):self.speed.addItem(str(count),count)
        self.speed.setCurrentIndex(1);controls.addWidget(self.speed)
        seed_row = QHBoxLayout()
        self.seed = QLineEdit(str(self.model.seed));self.seed.setAccessibleName('Seed');self.seed.setMaximumWidth(110)
        self.reset_button = QPushButton('Reset seed');self.reset_button.clicked.connect(self.reset_seed)
        seed_row.addWidget(self.seed);seed_row.addWidget(self.reset_button)
        controls.addWidget(caption('Seed'));controls.addLayout(seed_row)
        self.tabs=QTabWidget();controls.addWidget(self.tabs)
        paint_tab=QWidget();paint_controls=QVBoxLayout(paint_tab);paint_controls.setContentsMargins(8,12,8,12)
        presence_tab=QWidget();presence_controls=QVBoxLayout(presence_tab);presence_controls.setContentsMargins(8,12,8,12)
        self.tabs.addTab(paint_tab,'Paint');self.tabs.addTab(presence_tab,'Drop / add')
        paint_controls.setSpacing(8);presence_controls.setSpacing(8)
        self.mode = QComboBox()
        self.mode.addItem('Set orientation','set');self.mode.addItem('Turn orientation','turn')
        self.mode.addItem('Erase dashes','erase');self.mode.addItem('Add fresh dashes','restore')
        paint_controls.addWidget(self.mode)
        self.angle_label = QLabel();paint_controls.addWidget(self.angle_label)
        self.angle = QSlider(Qt.Horizontal);self.angle.setRange(0,360);self.angle.setValue(90)
        self.angle.valueChanged.connect(self.brush_changed);paint_controls.addWidget(self.angle)
        legend = np.tile(np.linspace(0,2*np.pi,230),(12,1))
        rgb = phase_colors(legend).astype(np.uint8)
        swatch = QLabel();swatch.setPixmap(QPixmap.fromImage(QImage(rgb.data,230,12,690,QImage.Format_RGB888).copy()))
        paint_controls.addWidget(swatch);paint_controls.addWidget(caption('Dash palette · 0° to 360°'))
        self.radius_label = QLabel();paint_controls.addWidget(self.radius_label)
        self.radius = QSlider(Qt.Horizontal);self.radius.setRange(1,12);self.radius.setValue(4)
        self.radius.valueChanged.connect(self.brush_changed);paint_controls.addWidget(self.radius)
        paint_controls.addWidget(caption('Paint either field; both receive the same edit. Brush strokes pause growth.'))
        paint_controls.addStretch()
        self.drop_rate=QDoubleSpinBox();self.return_rate=QDoubleSpinBox()
        for spin,value in ((self.drop_rate,self.model.drop_probability),(self.return_rate,self.model.return_probability)):
            spin.setRange(0,5);spin.setDecimals(2);spin.setSingleStep(.1);spin.setSuffix('%');spin.setValue(value*100)
            spin.valueChanged.connect(self.rates_changed)
        presence_controls.addWidget(caption('Drop-out chance per present dash / tick'))
        presence_controls.addWidget(self.drop_rate)
        presence_controls.addWidget(caption('Return chance per absent site / tick'))
        presence_controls.addWidget(self.return_rate)
        self.density_hint=caption('');presence_controls.addWidget(self.density_hint)
        self.flicker_button=QPushButton('Flicker + Play');self.flicker_button.clicked.connect(self.flicker)
        presence_controls.addWidget(self.flicker_button)
        self.calm_button=QPushButton('Stop random switching');self.calm_button.clicked.connect(lambda:self.set_rates(0,0))
        presence_controls.addWidget(self.calm_button)
        presence_row=QHBoxLayout()
        self.drop_one_button=QPushButton('Drop one');self.drop_one_button.clicked.connect(lambda:self.one_presence(False))
        self.add_one_button=QPushButton('Add one');self.add_one_button.clicked.connect(lambda:self.one_presence(True))
        self.drop_one_button.setToolTip('Remove one randomly chosen visible dash.')
        self.add_one_button.setToolTip('Fill one randomly chosen visible hole with a fresh dash.')
        presence_row.addWidget(self.drop_one_button);presence_row.addWidget(self.add_one_button);presence_controls.addLayout(presence_row)
        burst_row=QHBoxLayout()
        self.punch_button=QPushButton('Drop 5%');self.punch_button.clicked.connect(self.punch)
        self.refill_button=QPushButton('Refill holes');self.refill_button.clicked.connect(self.refill)
        burst_row.addWidget(self.punch_button);burst_row.addWidget(self.refill_button);presence_controls.addLayout(burst_row)
        presence_controls.addWidget(caption('Absent = no dash, no bonds, no stored state. Returns start with fresh random angles.'))
        presence_controls.addStretch()
        self.view = QComboBox();self.view.addItem('Orientation θ','theta');self.view.addItem('Compression C','C')
        self.view.addItem('Angular activity','activity')
        self.view.currentIndexChanged.connect(self.refresh)
        self.render_style=QComboBox()
        self.render_style.addItem('3D torus','torus');self.render_style.addItem('Flat luminous dashes','dashes');self.render_style.addItem('Classic heatmap','classic')
        if model is not None and not isinstance(model,LabSandbox):self.render_style.setCurrentIndex(1)
        self.seams=QCheckBox('Show coordinate seams')
        self.seams.setToolTip('Alignment and geometry wrap; legacy dipole and triad links stop at these seams.')
        self.seams.toggled.connect(self.refresh)
        self.home_camera=QPushButton('Reset camera');self.home_camera.clicked.connect(self.reset_camera)
        self.render_style.currentIndexChanged.connect(self.refresh)
        viewbar=QHBoxLayout()
        viewbar.addWidget(self.render_style);viewbar.addWidget(self.view)
        viewbar.addWidget(self.seams);viewbar.addStretch();viewbar.addWidget(self.home_camera)
        outer.insertLayout(1,viewbar)
        controls.addStretch()
        self.export_button = QPushButton('Export PNG + recipe');self.export_button.clicked.connect(self.export)
        self.export_link = QLabel();self.export_link.setWordWrap(True);self.export_link.setOpenExternalLinks(True)
        self.canvases = [];self.panels=[]
        for index,name in enumerate(LANES):
            panel = QFrame();panel.setObjectName('panel')
            box = QVBoxLayout(panel);box.setContentsMargins(14,16,14,12);box.setSpacing(8)
            label = QLabel(LABELS[index]);label.setObjectName('lane');box.addWidget(label)
            box.addWidget(caption('Structure feedback + vacancy experiment' if index == 0 else 'Same holes and arrivals · geometry feedback off'))
            canvas = FieldCanvas();canvas.started.connect(self.begin_stroke)
            canvas.stamped.connect(self.paint_at);canvas.finished.connect(self.end_stroke)
            canvas.camera_changed.connect(lambda c=canvas:self.sync_camera(c))
            box.addWidget(canvas,1)
            box.addWidget(caption('Right-drag: orbit   /   Wheel: zoom   /   Left-drag: paint the surface'))
            self.canvases.append(canvas);self.panels.append(panel);body.addWidget(panel,1)
        self.message = caption('Start with Grow +1000 to form a texture, then paint. Both lanes begin with identical angles.')
        footer=QHBoxLayout();footer.addWidget(self.export_button);footer.addWidget(self.export_link,1)
        outer.addLayout(footer)
        outer.addWidget(self.message)
        self.timer = QTimer(self);self.timer.setInterval(33);self.timer.timeout.connect(self.tick);self.timer.start()
        self.brush_changed();self.refresh();self.update_density_hint()

    def brush_changed(self):
        self.angle_label.setText(f'Angle  {self.angle.value()}°')
        self.radius_label.setText(f'Radius  {self.radius.value()} cells')
        for canvas in getattr(self,'canvases',[]):
            canvas.radius = self.radius.value();canvas.update()

    def refresh(self):
        field = self.view.currentData()
        torus=self.render_style.currentData()=='torus'
        self.setWindowTitle('Field Lab - '+('3D torus' if torus else 'Flat field'))
        self.zoom.setEnabled(not torus);self.zoom.setVisible(not torus)
        self.seams.setEnabled(torus);self.home_camera.setEnabled(torus)
        self.panels[1].setVisible(self.compare.isChecked())
        for index,(name,canvas) in enumerate(zip(LANES,self.canvases)):
            if index==1 and not self.compare.isChecked():continue
            canvas.zoom=self.zoom.currentData()
            canvas.seams=self.seams.isChecked()
            canvas.preview=self.playing or self.remaining>0
            canvas.set_field(self.model.states[name],field,self.render_style.currentData())
        active = self.playing or self.remaining > 0
        self.play_button.setText('Pause' if active else 'Play')
        suffix = f' · {self.remaining} queued' if self.remaining else ''
        self.status.setText(f'{"GROWING" if active else "PAUSED"} · UPDATE {self.model.update:,}{suffix}')
        self.status.setToolTip(f'Seed {self.model.seed} · {self.model.n} × {self.model.n} · discrete updates')
        self.message.setText(
            f'Seed {self.model.seed} · {self.model.update:,} ticks · {int(self.model.active.sum()):,}/{self.model.n**2:,} present · '
            f'↓ {self.model.dropped:,} departures  ↑ {self.model.arrived:,} arrivals · '
            + ('Angle = direction + color. Pink rings mark departures; pale flashes mark arrivals.' if field == 'theta'
               else 'Fixed-scale field view · switch to Orientation to edit.'))

    def sync_camera(self,source):
        for canvas in self.canvases:
            if canvas is not source:
                canvas.scene = TorusScene(**source.scene.camera())
                if canvas.isVisible():canvas.render_torus(True)

    def reset_camera(self):
        for canvas in self.canvases:canvas.scene=TorusScene()
        self.refresh()

    def pause(self):
        self.playing,self.remaining = False,0

    def toggle_play(self):
        if self.playing or self.remaining:self.pause()
        else:self.playing = True
        self.refresh()

    def tick(self):
        if not self.playing and not self.remaining:return
        count = self.speed.currentData()
        if self.remaining:count = min(count,self.remaining)
        try:
            self.model.advance(count)
            if self.remaining:self.remaining -= count
            self.refresh()
        except Exception as exc:
            self.pause();self.refresh();self.message.setText(f'Growth stopped: {exc}')

    def step_once(self):
        self.pause();self.model.advance(1);self.refresh()

    def grow(self):
        self.playing = False;self.remaining = 1000;self.refresh()

    def reset_seed(self):
        try:
            replacement = LabSandbox(int(self.seed.text()),self.model.n)
            replacement.set_rates(self.drop_rate.value()/100,self.return_rate.value()/100)
        except ValueError as exc:
            self.message.setText(f'Cannot reset: {exc}');return
        self.pause();self.model = replacement;self.last_cell = None;self.refresh()

    def begin_stroke(self):
        self.pause();self.last_cell = None;self.refresh()

    def paint_at(self,x,y):
        if self.view.currentData() != 'theta':return
        target = (int(x),int(y))
        if target == self.last_cell:return
        if self.last_cell is None:points = [target]
        else:
            delta=np.array(target)-self.last_cell
            if self.render_style.currentData()=='torus':delta=(delta+self.model.n//2)%self.model.n-self.model.n//2
            distance=int(np.max(np.abs(delta)))
            points=[tuple(np.rint(p).astype(int)%self.model.n) for p in np.linspace(self.last_cell,np.array(self.last_cell)+delta,distance+1)[1:]]
        for px,py in points:
            mode=self.mode.currentData()
            if mode in ('erase','restore'):self.model.presence_brush(px,py,self.radius.value(),mode=='restore')
            else:self.model.paint(px,py,self.radius.value(),np.deg2rad(self.angle.value()),mode)
        self.last_cell = target;self.refresh()

    def end_stroke(self):self.last_cell = None

    def export(self):
        self.pause();self.refresh()
        stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
        path = self.export_root/f'{stamp}_seed{self.model.seed}_u{self.model.update}'
        try:
            self.last_export = export_bundle(self.model,path,self.view.currentData(),self.render_style.currentData(),self.zoom.currentData(),self.compare.isChecked(),self.canvases[0].scene.camera(),self.seams.isChecked())
            url = QUrl.fromLocalFile(str((path/'pattern.png').resolve())).toString()
            self.export_link.setText(f'<a style="color:#b4e7d6" href="{url}">Open saved image ↗</a>')
            self.export_link.setToolTip(str(path.resolve()))
            self.message.setText(f'Saved PNG, full fields and replay recipe: {path}')
        except Exception as exc:self.message.setText(f'Export failed: {exc}')

    def closeEvent(self,event):
        self.timer.stop()
        for canvas in self.canvases:
            canvas.settle.stop()
            if canvas.gpu is not None:canvas.gpu.close()
        super().closeEvent(event)

    def rates_changed(self):
        self.model.set_rates(self.drop_rate.value()/100,self.return_rate.value()/100)
        self.update_density_hint();self.refresh()

    def update_density_hint(self):
        p,q=self.drop_rate.value(),self.return_rate.value()
        self.density_hint.setText(f'Expected long-run occupancy: {100*q/(p+q):.0f}%' if p+q else 'No automatic departures or arrivals.')

    def set_rates(self,drop,restore):
        for spin,value in ((self.drop_rate,drop),(self.return_rate,restore)):
            spin.blockSignals(True);spin.setValue(value*100);spin.blockSignals(False)
        self.rates_changed()

    def flicker(self):
        self.set_rates(.002,.006);self.playing=True;self.remaining=0;self.refresh()

    def one_presence(self,restore):
        n=self.model.n;span=n/self.zoom.currentData()
        rows,cols=np.indices((n,n));low=(n-span)/2;high=(n+span)/2
        visible=(cols>=low)&(cols<high)&(rows>=low)&(rows<high)
        if self.render_style.currentData()=='torus':
            visible=np.zeros((n,n),bool)
            canvas=self.canvases[0]
            ratio=360/max(canvas.width(),canvas.height())
            mapping=canvas.scene.geometry(max(1,round(canvas.width()*ratio)),max(1,round(canvas.height()*ratio)))
            if mapping is not None:
                cells=(mapping['uv']/(2*np.pi)*n).astype(int)%n
                visible[cells[:,1],cells[:,0]]=True
        choices=np.argwhere(visible & (~self.model.active if restore else self.model.active))
        if len(choices):
            cell=choices[self.model.interaction_rng.integers(len(choices))]
            self.model.presence([cell[::-1]],restore)
        self.refresh()

    def punch(self):
        self.model.random_presence(max(1,round(self.model.active.sum()*.05)));self.refresh()

    def refill(self):
        self.model.random_presence(int((~self.model.active).sum()),True);self.refresh()
