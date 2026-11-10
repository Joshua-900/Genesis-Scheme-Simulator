"""Qt controls and interaction. No simulation equations live in this module."""
from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path
import time

import numpy as np
from PyQt5.QtCore import QRectF, Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QFont, QFontDatabase, QImage, QPainter
from PyQt5.QtWidgets import (
    QApplication, QCheckBox, QComboBox, QDoubleSpinBox, QFileDialog, QFormLayout, QFrame, QHBoxLayout,
    QLabel, QLineEdit, QMainWindow, QPushButton, QScrollArea, QSlider,
    QVBoxLayout, QWidget,
)

from ..application.session import Session
from ..application.genesis_pair import GenesisPair
from ..domain.chase import Chase
from ..domain.formulas import FormulaError
from ..domain.model import PRESETS, Simulation
from .render import Look, PALETTES, guide_overlay, render
from .storage import load_bundle, save_bundle


class FieldView(QWidget):
    stirred = pyqtSignal(float, float)

    def __init__(self):
        super().__init__()
        self.setMinimumSize(400, 400)
        self.setMouseTracking(True)
        self.setCursor(Qt.CrossCursor)
        self.zoom, self.center = 1., np.array([.5, .5])
        self.gpu, self.attempted = None, False
        self.simulation, self.look, self.image = None, Look(), None
        self.show_guide, self.drag = False, None
        self.resize_timer = QTimer(self)
        self.resize_timer.setSingleShot(True)
        self.resize_timer.timeout.connect(self.present)

    def fallback(self):
        if self.gpu is not None:
            self.gpu.native.hide()
        self.gpu = None
        self.resize_timer.start(1)

    def present(self, simulation=None, look=None):
        if simulation is not None:
            self.simulation = simulation
        if look is not None:
            self.look = look
        if self.simulation is None:
            return
        if not self.attempted:
            self.attempted = True
            if QApplication.platformName() != 'offscreen':
                try:
                    from .gpu import DensityCanvas
                    self.gpu = DensityCanvas(self, self.fallback)
                    self.gpu.native.setAttribute(Qt.WA_TransparentForMouseEvents)
                except Exception:
                    import logging
                    logging.exception('GPU unavailable; using software')
                    self.fallback()
        if self.gpu is not None:
            self.gpu.native.setGeometry(self.rect())
            self.gpu.native.show()
            self.gpu.present(self.simulation, self.look, self.zoom, self.center, self.show_guide)
        else:
            rgb = np.ascontiguousarray(np.asarray(render(self.simulation, self.look)))
            if self.show_guide:
                alpha = .3 * guide_overlay(self.simulation)[::-1]
                rgb = np.ascontiguousarray(np.clip(rgb * (1 - alpha[:, :, None]) + np.array([189, 107, 56]) * alpha[:, :, None], 0, 255).astype(np.uint8))
            self.image = QImage(rgb.data, rgb.shape[1], rgb.shape[0], rgb.strides[0], QImage.Format_RGB888).copy()
            self.software_rgb = rgb
        self.update()

    def square(self):
        side = min(self.width(), self.height())
        return QRectF((self.width() - side) / 2, (self.height() - side) / 2, side, side)

    def position(self, point):
        rect = self.square()
        if not rect.contains(point) or self.simulation is None:
            return None
        uv = np.array([(point.x() - rect.center().x()) / rect.width(),
                       (rect.center().y() - point.y()) / rect.height()]) / self.zoom + self.center
        return tuple((uv % 1 * self.simulation.rules.size).tolist())

    def paintEvent(self, event):
        if self.gpu is not None or self.image is None:
            return
        painter = QPainter(self)
        painter.fillRect(self.rect(), Qt.black)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)
        # Software view uses the same periodic crop and pan as the shader.
        from PIL import Image
        side = self.image.width()
        tiled = Image.fromarray(np.tile(self.software_rgb, (3, 3, 1)))
        span = side / self.zoom
        cx, cy = (1 + self.center[0]) * side, (2 - self.center[1]) * side
        rgb = np.ascontiguousarray(tiled.crop((cx - span / 2, cy - span / 2, cx + span / 2, cy + span / 2)))
        crop = QImage(rgb.data, rgb.shape[1], rgb.shape[0], rgb.strides[0], QImage.Format_RGB888).copy()
        painter.drawImage(self.square(), crop)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.resize_timer.start(80)

    def mousePressEvent(self, event):
        if event.button() == Qt.RightButton:
            self.drag = event.localPos()
        elif event.button() == Qt.LeftButton:
            point = self.position(event.localPos())
            if point is not None:
                self.stirred.emit(*point)

    def mouseMoveEvent(self, event):
        if self.drag is not None and event.buttons() & Qt.RightButton:
            delta = event.localPos() - self.drag
            self.drag = event.localPos()
            self.center = (self.center + np.array([-delta.x(), delta.y()]) / self.square().width() / self.zoom) % 1
            self.present()
        elif event.buttons() & Qt.LeftButton:
            point = self.position(event.localPos())
            if point is not None:
                self.stirred.emit(*point)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.RightButton:
            self.drag = None

    def wheelEvent(self, event):
        self.zoom = float(np.clip(self.zoom * 1.15**(event.angleDelta().y() / 120), 1, 6))
        self.present()


def label(text, *, muted=False):
    result = QLabel(text)
    result.setWordWrap(True)
    if muted:
        result.setObjectName('muted')
    return result


class StudioWindow(QMainWindow):
    def __init__(self, session: Session, look: Look | None = None, output: Path | None = None):
        super().__init__()
        self.session, self.look = session, look or Look()
        self.checkpoint = None
        self.presets = {name: replace(rules, size=session.simulation.rules.size,
                                      agents=(session.simulation.population if isinstance(session.simulation, Chase)
                                              else session.simulation.rules.agents))
                        for name, rules in PRESETS.items()}
        self.output = output or Path.cwd() / 'work/physarum_exports'
        self.last_export = None
        self.formula_editor = None
        self.solo_session = None
        self.genesis_pair = None
        self.theta_monitor = None
        self.before_genesis = None
        self.membrane_window = None
        self.last_frame, self.fps = time.perf_counter(), 0.
        self.setWindowTitle('Physarum Studio')
        self.resize(1440, 960)
        self.setMinimumSize(1060, 780)
        family = 'Segoe UI'
        if family not in QFontDatabase().families():
            import matplotlib
            font = Path(matplotlib.get_data_path()) / 'fonts/ttf/DejaVuSans.ttf'
            QFontDatabase.addApplicationFont(str(font))
            family = 'DejaVu Sans'
        self.setFont(QFont(family, 10))
        self.setStyleSheet('''
            QWidget { background:#0a1015; color:#dce3df; }
            QLabel { background:transparent; }
            QLabel#muted { color:#849996; font-size:12px; }
            QLabel#title { font-size:26px; font-weight:600; letter-spacing:3px; }
            QLabel#status { color:#c5d6bf; }
            QFrame#controls { background:#101a20; border-radius:8px; }
            QPushButton { background:#1c3037; border:1px solid #334b4d; border-radius:5px; padding:9px; }
            QPushButton:hover { background:#2a4549; }
            QPushButton#primary { background:#d9dfc6; color:#152322; font-weight:600; }
            QComboBox,QLineEdit { background:#18282e; padding:7px; border:1px solid #32464b; border-radius:4px; }
            QSlider::groove:horizontal { height:3px; background:#34474b; }
            QSlider::handle:horizontal { background:#d9dfc6; width:12px; margin:-5px 0; border-radius:6px; }
            QScrollArea { border:none; }
            QCheckBox::indicator { width:13px; height:13px; border:1px solid #627c7d; }
            QCheckBox::indicator:checked { background:#cbdcbe; }
            QScrollBar:vertical { background:#101a20; width:6px; }
            QScrollBar::handle:vertical { background:#405d60; min-height:24px; }
            QScrollBar::add-line:vertical,QScrollBar::sub-line:vertical { height:0; }
        ''')
        root = QWidget()
        self.setCentralWidget(root)
        outer = QVBoxLayout(root)
        outer.setContentsMargins(26, 24, 26, 18)
        outer.setSpacing(18)
        header = QHBoxLayout()
        title = label('PHYSARUM / STUDIO')
        title.setWordWrap(False)
        title.setObjectName('title')
        header.addWidget(title)
        header.addStretch()
        self.status = label('')
        self.status.setWordWrap(False)
        self.status.setObjectName('status')
        header.addWidget(self.status)
        outer.addLayout(header)
        body = QHBoxLayout()
        body.setSpacing(24)
        outer.addLayout(body, 1)
        sidebar = QFrame()
        sidebar.setObjectName('controls')
        sidebar.setFixedWidth(252)
        controls = QVBoxLayout(sidebar)
        controls.setContentsMargins(16, 18, 16, 18)
        controls.setSpacing(12)
        scroll = QScrollArea()
        scroll.setFixedWidth(268)
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setWidget(sidebar)
        body.addWidget(scroll)
        controls.addWidget(label('MOVEMENT', muted=True))
        row = QHBoxLayout()
        self.play = QPushButton('Pause')
        self.play.setObjectName('primary')
        self.play.clicked.connect(self.toggle)
        row.addWidget(self.play)
        self.step_button = QPushButton('Step')
        self.step_button.clicked.connect(self.step_once)
        row.addWidget(self.step_button)
        controls.addLayout(row)
        self.run_button = QPushButton('Run 100 ticks')
        self.run_button.clicked.connect(self.run_checkpoint)
        controls.addWidget(self.run_button)
        self.chase_button = QPushButton('Start Ivory & Amber')
        self.chase_button.clicked.connect(self.toggle_chase)
        controls.addWidget(self.chase_button)
        self.genesis_button = QPushButton('Compare Genesis steering')
        self.genesis_button.clicked.connect(self.toggle_genesis)
        controls.addWidget(self.genesis_button)
        self.genesis_source = label('', muted=True)
        controls.addWidget(self.genesis_source)
        self.evolve_genesis = QCheckBox('Evolve Genesis field')
        self.evolve_genesis.toggled.connect(self.change_genesis_evolution)
        controls.addWidget(self.evolve_genesis)
        self.theta_button = QPushButton('View theta field')
        self.theta_button.clicked.connect(self.open_theta_monitor)
        controls.addWidget(self.theta_button)
        membrane_button = QPushButton('Open Growing Membrane')
        membrane_button.clicked.connect(self.open_membrane)
        controls.addWidget(membrane_button)
        self.chase_controls = QWidget()
        chase_form = QFormLayout(self.chase_controls)
        chase_form.setContentsMargins(0, 0, 0, 0)
        self.follow = QDoubleSpinBox()
        self.follow.setRange(0, 8)
        self.follow.setSingleStep(.25)
        self.erase = QDoubleSpinBox()
        self.erase.setRange(0, 1)
        self.erase.setSingleStep(.05)
        chase_form.addRow('Amber follows', self.follow)
        chase_form.addRow('Amber erases', self.erase)
        self.layer = QComboBox()
        for title, value in (('Both', 'both'), ('Ivory only', 'ivory'), ('Amber only', 'amber')):
            self.layer.addItem(title, value)
        self.layer.setCurrentIndex(self.layer.findData(self.look.layer))
        self.layer.currentIndexChanged.connect(self.change_look)
        chase_form.addRow('Show trails', self.layer)
        self.follow.valueChanged.connect(self.change_interaction)
        self.erase.valueChanged.connect(self.change_interaction)
        controls.addWidget(self.chase_controls)
        self.preset = QComboBox()
        self.preset.addItems(self.presets)
        for name, rules in self.presets.items():
            if replace(rules, mode_m=session.simulation.rules.mode_m,
                       mode_n=session.simulation.rules.mode_n) == session.simulation.rules:
                self.preset.setCurrentText(name)
        controls.addWidget(self.preset)
        row = QHBoxLayout()
        self.seed = QLineEdit(str(session.simulation.seed))
        self.seed.setAccessibleName('Random seed')
        self.reset_button = QPushButton('Reseed')
        self.reset_button.clicked.connect(self.reset)
        row.addWidget(self.seed)
        row.addWidget(self.reset_button)
        controls.addLayout(row)
        self.preset.currentTextChanged.connect(self.reset)
        self.current_label = label('')
        controls.addWidget(self.current_label)
        self.current = QSlider(Qt.Horizontal)
        self.current.setRange(0, 400)
        self.current.setValue(round(session.simulation.rules.flow * 100))
        self.current.setAccessibleName('Current strength')
        self.current.valueChanged.connect(self.change_current)
        controls.addWidget(self.current)
        controls.addWidget(label('RESONANCE', muted=True))
        self.guidance_label = label('')
        controls.addWidget(self.guidance_label)
        self.guidance = QSlider(Qt.Horizontal)
        self.guidance.setRange(0, 100)
        self.guidance.setValue(round(session.target_guidance * 100))
        self.guidance.setAccessibleName('Field strength')
        self.guidance.valueChanged.connect(self.guide)
        controls.addWidget(self.guidance)
        row = QHBoxLayout()
        self.release = QPushButton('Release')
        self.release.clicked.connect(lambda: self.guidance.setValue(0))
        self.gather = QPushButton('Gather')
        self.gather.clicked.connect(lambda: self.guidance.setValue(100))
        self.gather.clicked.connect(self.guide)
        row.addWidget(self.release)
        row.addWidget(self.gather)
        controls.addLayout(row)
        self.modes = QComboBox()
        for m, n in ((3, 5), (2, 3), (4, 7), (5, 8), (3, 7)):
            self.modes.addItem(f'Wave modes  {m} : {n}', (m, n))
        pair = (session.simulation.rules.mode_m, session.simulation.rules.mode_n)
        if self.modes.findData(pair) < 0:
            self.modes.addItem(f'Wave modes  {pair[0]} : {pair[1]}', pair)
        self.modes.setCurrentIndex(self.modes.findData(pair))
        self.modes.currentIndexChanged.connect(self.change_modes)
        controls.addWidget(self.modes)
        self.formula_button = QPushButton('Formula editor…')
        self.formula_button.clicked.connect(self.open_formula_editor)
        controls.addWidget(self.formula_button)
        self.guide_overlay = QCheckBox('Reveal guiding pattern')
        self.guide_overlay.toggled.connect(self.refresh)
        controls.addWidget(self.guide_overlay)
        controls.addWidget(label('Guidance steers agents. Gather and release blend gradually. Open the formula editor to define your own fields.', muted=True))
        controls.addWidget(label('APPEARANCE', muted=True))
        self.palette = QComboBox()
        self.palette.addItems(PALETTES)
        self.palette.setCurrentText(self.look.palette)
        self.palette.currentTextChanged.connect(self.change_look)
        controls.addWidget(self.palette)
        self.exposure_label = label('')
        controls.addWidget(self.exposure_label)
        self.exposure = QSlider(Qt.Horizontal)
        self.exposure.setRange(10, 400)
        self.exposure.setValue(round(self.look.exposure * 100))
        self.exposure.setAccessibleName('Exposure')
        self.exposure.valueChanged.connect(self.change_look)
        controls.addWidget(self.exposure)
        self.fit = QPushButton('Fit whole field')
        self.fit.clicked.connect(self.fit_view)
        controls.addWidget(self.fit)
        controls.addStretch()
        self.canvas = FieldView()
        self.canvas.stirred.connect(self.stir)
        guided_panel = QVBoxLayout()
        guided_panel.setSpacing(8)
        self.guided_title = label('FORMULA GUIDANCE', muted=True)
        guided_panel.addWidget(self.guided_title)
        guided_panel.addWidget(self.canvas, 1)
        body.addLayout(guided_panel, 1)
        self.control_panel = QWidget()
        control_layout = QVBoxLayout(self.control_panel)
        control_layout.setContentsMargins(0, 0, 0, 0)
        control_layout.setSpacing(8)
        control_layout.addWidget(label('MATCHED CONTROL · ZERO GUIDANCE SIGNAL', muted=True))
        self.control_canvas = FieldView()
        self.control_canvas.stirred.connect(self.stir)
        control_layout.addWidget(self.control_canvas, 1)
        body.addWidget(self.control_panel, 1)
        footer = QHBoxLayout()
        self.export_button = QPushButton('Save artwork + state')
        self.export_button.clicked.connect(self.export)
        self.open_button = QPushButton('Open saved state')
        self.open_button.clicked.connect(self.open)
        footer.addWidget(self.export_button)
        footer.addWidget(self.open_button)
        footer.addStretch()
        footer.addWidget(label('Drag to stir  /  Wheel to inspect  /  Right-drag to pan', muted=True))
        outer.addLayout(footer)
        self.message = label('Moving agents weave trails; trails guide their next movement.', muted=True)
        outer.addWidget(self.message)
        self.timer = QTimer(self)
        self.timer.setInterval(20)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.on_timer)
        self.refresh()
        self.timer.start()

    def refresh(self):
        self.canvas.show_guide = self.guide_overlay.isChecked()
        self.canvas.present(self.session.simulation, self.look)
        self.play.setText('Pause' if self.session.playing else 'Play')
        s = self.session.simulation
        paired = self.genesis_pair is not None
        self.guided_title.setVisible(paired)
        self.control_panel.setVisible(paired)
        if paired:
            self.control_canvas.present(self.genesis_pair.control.simulation, self.look)
        self.genesis_button.setText('End Genesis comparison' if paired else 'Compare Genesis steering')
        self.genesis_source.setVisible(s.genesis is not None)
        self.evolve_genesis.setVisible(paired)
        self.theta_button.setVisible(paired and self.genesis_pair.feed is not None)
        evolving = paired and self.genesis_pair.evolving
        self.evolve_genesis.blockSignals(True)
        self.evolve_genesis.setChecked(evolving)
        self.evolve_genesis.blockSignals(False)
        if self.theta_monitor is not None and self.theta_monitor.isVisible():
            self.theta_monitor.refresh(evolving)
        if s.genesis is not None:
            mode = 'Live' if evolving else 'Frozen'
            self.genesis_source.setText(f'{mode} Genesis · seed {s.genesis.seed} · tick {s.genesis.tick}')
        for widget in (self.chase_button, self.preset):
            widget.setEnabled(not paired)
        self.reset_button.setText('Reseed agents' if paired else 'Reseed')
        chase = isinstance(s, Chase)
        custom = s.formula is not None or (chase and s.amber.formula is not None)
        self.chase_controls.setVisible(chase)
        self.chase_button.setText('Return to solo' if chase else 'Start Ivory & Amber')
        self.palette.setEnabled(not chase)
        self.modes.setEnabled(not custom)
        self.formula_button.setText('Formula editor · custom' if custom else 'Formula editor…')
        if chase:
            for widget, value in ((self.follow, s.follow), (self.erase, s.erase)):
                widget.blockSignals(True)
                widget.setValue(value)
                widget.blockSignals(False)
        self.guidance.blockSignals(True)
        self.guidance.setValue(round(self.session.target_guidance * 100))
        self.guidance.blockSignals(False)
        state = 'FLOWING' if self.session.playing else 'PAUSED'
        checkpoint = self.checkpoint
        running_to_checkpoint = checkpoint is not None and checkpoint[0] is self.session
        self.run_button.setEnabled(not running_to_checkpoint)
        if running_to_checkpoint:
            self.run_button.setText(f'Running to tick {checkpoint[1]:,}')
        else:
            self.run_button.setText('Run 100 ticks')
        population = s.population if chase else s.rules.agents
        self.status.setText(f'{state}   /   {s.tick:,} ticks   /   {population:,} agents')
        self.exposure_label.setText(f'Exposure  {self.look.exposure:.2f}')
        self.guidance_label.setText(f'Field strength  {self.guidance.value()}%')
        self.current_label.setText(f'Base current  {self.session.simulation.rules.flow:.2f}')

    def on_timer(self):
        started = time.perf_counter()
        self.tick()
        elapsed_ms = round((time.perf_counter() - started) * 1000)
        # Give Qt a chance to paint and handle input even when a step runs late.
        self.timer.start(max(1, 20 - elapsed_ms))

    def tick(self):
        if not self.session.playing:
            return
        try:
            checkpoint = self.checkpoint
            if checkpoint is not None and checkpoint[0] is self.session:
                remaining = checkpoint[1] - self.session.simulation.tick
                live = self.genesis_pair is not None and self.genesis_pair.evolving
                for _ in range(min(1 if live else 4, remaining)):
                    self.advance_scene()
                if self.session.simulation.tick == checkpoint[1]:
                    self.session.playing = False
                    self.checkpoint = None
            else:
                self.checkpoint = None
                self.advance_scene()
            self.refresh()
            now = time.perf_counter()
            self.fps = .9 * self.fps + .1 / max(now - self.last_frame, 1e-6)
            self.last_frame = now
            backend = 'GPU display' if self.canvas.gpu is not None else 'software display'
            self.status.setToolTip(f'{self.fps:.0f} updates/s / {backend}; fixed simulation steps')
        except Exception as exc:
            self.report_pause(exc)

    def toggle(self):
        self.checkpoint = None
        self.session.playing = not self.session.playing
        self.refresh()

    def run_checkpoint(self):
        self.checkpoint = (self.session, self.session.simulation.tick + 100)
        self.session.playing = True
        self.refresh()

    def step_once(self):
        self.checkpoint = None
        self.session.playing = False
        try:
            self.advance_scene()
            self.refresh()
        except ValueError as exc:
            self.report_pause(exc)

    def advance_scene(self):
        if self.genesis_pair is None:
            self.session.advance(force=True)
        else:
            self.genesis_pair.advance()

    def report_pause(self, exc):
        self.checkpoint = None
        self.session.playing = False
        self.refresh()
        self.message.setText(f'Simulation paused: {exc}')
        if isinstance(exc, FormulaError) and self.formula_editor is not None:
            self.formula_editor.error(f'Active formula paused at tick {self.session.simulation.tick:,}. {exc}',
                                      clear_preview=False)

    def guide(self):
        self.session.guide(self.guidance.value() / 100)
        if self.genesis_pair is not None:
            self.genesis_pair.control.guide(self.session.target_guidance)
        self.guidance_label.setText(f'Field strength  {self.guidance.value()}%')

    def change_modes(self):
        if self.genesis_pair is None:
            self.session.simulation.set_modes(*self.modes.currentData())
        else:
            self.genesis_pair.set_modes(*self.modes.currentData())
        self.refresh()

    def set_active_formula(self, spec, target, strength=None):
        simulation = self.session.simulation
        if self.genesis_pair is not None:
            self.genesis_pair.set_formula(spec, target)
        elif isinstance(simulation, Chase):
            simulation.set_formula(spec, target)
        else:
            simulation.set_formula(spec)
        if strength is not None:
            self.guidance.setValue(strength)
            self.guide()
        self.refresh()

    def open_formula_editor(self):
        if self.formula_editor is None:
            from .formula_editor import FormulaEditor
            self.formula_editor = FormulaEditor(self)
        self.formula_editor.sync_target()
        self.formula_editor.show()
        self.formula_editor.raise_()
        self.formula_editor.activateWindow()

    def change_current(self):
        s = self.session.simulation
        s.rules = replace(s.rules, flow=self.current.value() / 100)
        if isinstance(s, Chase):
            s.amber.rules = replace(s.amber.rules, flow=s.rules.flow)
        if self.genesis_pair is not None:
            control = self.genesis_pair.control.simulation
            control.rules = replace(control.rules, flow=s.rules.flow)
            control.amber.rules = replace(control.amber.rules, flow=s.amber.rules.flow)
        self.current_label.setText(f'Base current  {s.rules.flow:.2f}')

    def change_interaction(self):
        s = self.session.simulation
        if isinstance(s, Chase):
            s.set_interaction(self.follow.value(), self.erase.value())
        if self.genesis_pair is not None:
            self.genesis_pair.control.simulation.set_interaction(self.follow.value(), self.erase.value())

    def change_genesis_evolution(self, enabled):
        if self.genesis_pair is not None:
            self.genesis_pair.evolving = enabled
            self.refresh()

    def open_theta_monitor(self):
        if self.genesis_pair is None or self.genesis_pair.feed is None:
            return
        if self.theta_monitor is None:
            from .theta_monitor import ThetaMonitor
            self.theta_monitor = ThetaMonitor(self, self.genesis_pair.feed)
        self.theta_monitor.refresh(self.genesis_pair.evolving)
        self.theta_monitor.show()
        self.theta_monitor.raise_()

    def step_genesis(self):
        if self.genesis_pair is not None and self.genesis_pair.feed is not None:
            self.genesis_pair.evolving = False
            self.genesis_pair.feed.advance()
            self.refresh()

    def close_theta_monitor(self):
        if self.theta_monitor is not None:
            self.theta_monitor.close()
            self.theta_monitor.deleteLater()
            self.theta_monitor = None

    def toggle_genesis(self):
        if self.genesis_pair is not None:
            self.close_theta_monitor()
            self.session = self.before_genesis
            self.genesis_pair = self.before_genesis = None
            self.message.setText('Returned to your previous scene.')
        else:
            from src.genesis_sandbox.model import Sandbox
            from ..domain.genesis_source import FrozenGenesis

            try:
                seed = int(self.seed.text())
                rules = self.presets[self.preset.currentText()]
                genesis = Sandbox(seed % (2**32))
                genesis.advance(270)
                source = FrozenGenesis(genesis.seed, genesis.update, genesis.states['geometry_on'])
                pair = GenesisPair(seed, rules, source, genesis)
            except ValueError as exc:
                self.message.setText(str(exc))
                return
            self.before_genesis, self.genesis_pair = self.session, pair
            self.session = pair.guided
            self.message.setText('Both chases start from the same seed. Genesis steers ivory on the left. Press Play to compare.')
        self.current.blockSignals(True)
        self.current.setValue(round(self.session.simulation.rules.flow * 100))
        self.current.blockSignals(False)
        if self.formula_editor is not None:
            self.formula_editor.sync_target()
        self.fit_view()

    def open_membrane(self):
        if self.membrane_window is None:
            from .membrane_studio import MembraneWindow
            self.membrane_window = MembraneWindow(self.session.simulation.seed, self)
            self.membrane_window.setAttribute(Qt.WA_DeleteOnClose)
            self.membrane_window.destroyed.connect(self.clear_membrane_window)
        self.membrane_window.show()
        self.membrane_window.raise_()
        self.membrane_window.activateWindow()

    def clear_membrane_window(self):
        self.membrane_window = None

    def toggle_chase(self):
        s = self.session.simulation
        if isinstance(s, Chase):
            self.session = self.solo_session or Session(
                Simulation(s.seed, replace(s.rules, agents=s.population)))
            self.solo_session = None
            self.message.setText('Solo field ready.')
        else:
            try:
                chase = Chase(s.seed, s.rules)
            except ValueError as exc:
                self.message.setText(str(exc))
                return
            self.solo_session = self.session
            self.session = Session(chase, guidance=1., target_guidance=1., release_at=90)
            self.message.setText('Ivory & Amber · spiral releases at tick 90. Amber follows and erases ivory trails.')
        if self.formula_editor is not None:
            self.formula_editor.sync_target()
        self.current.blockSignals(True)
        self.current.setValue(round(self.session.simulation.rules.flow * 100))
        self.current.blockSignals(False)
        self.seed.setText(str(self.session.simulation.seed))
        self.fit_view()

    def change_look(self):
        self.look = replace(self.look, palette=self.palette.currentText(),
                            exposure=self.exposure.value() / 100, layer=self.layer.currentData())
        self.refresh()

    def fit_view(self):
        self.canvas.zoom, self.canvas.center = 1., np.array([.5, .5])
        self.control_canvas.zoom, self.control_canvas.center = 1., np.array([.5, .5])
        self.refresh()

    def stir(self, x, y):
        self.session.simulation.disturb(x, y, radius=self.session.simulation.rules.size * .055)
        if self.genesis_pair is not None:
            control = self.genesis_pair.control.simulation
            control.disturb(x, y, radius=control.rules.size * .055)
        self.refresh()

    def reset(self):
        try:
            if self.genesis_pair is not None:
                seed = int(self.seed.text())
                self.genesis_pair.reseed(seed)
                self.checkpoint = None
                self.refresh()
                self.message.setText(f'Agents reset to seed {seed} in both lanes. Genesis is held. Press Play to compare.')
                return
            rules = self.presets[self.preset.currentText()]
            previous = self.session.simulation
            if isinstance(previous, Chase):
                simulation = Chase(int(self.seed.text()), rules, previous.follow, previous.erase,
                                   genesis=previous.genesis)
                simulation.set_modes(*self.modes.currentData())
                for target, population in (('ivory', previous), ('amber', previous.amber)):
                    if population.formula is not None:
                        simulation.set_formula(population.formula.spec, target)
                self.session = Session(simulation, guidance=1., target_guidance=1., release_at=90)
                self.current.blockSignals(True)
                self.current.setValue(round(rules.flow * 100))
                self.current.blockSignals(False)
                self.fit_view()
                self.message.setText('New chase · spiral releases at tick 90.')
                return
            simulation = Simulation(int(self.seed.text()), rules, genesis=previous.genesis)
            simulation.set_modes(*self.modes.currentData())
            if self.session.simulation.formula is not None:
                simulation.set_formula(self.session.simulation.formula.spec)
            self.session = Session(simulation, target_guidance=self.guidance.value() / 100)
            self.current.blockSignals(True)
            self.current.setValue(round(rules.flow * 100))
            self.current.blockSignals(False)
            self.fit_view()
            self.message.setText('New seeded population. Structures develop as the agents move.')
        except ValueError as exc:
            self.message.setText(str(exc))

    def export(self):
        previous = self.session.playing
        self.session.playing = False
        try:
            stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
            self.last_export = save_bundle(self.session, self.look, self.output / stamp)
            self.message.setText(f'Saved 1600px artwork and resumable numerical state: {self.last_export}')
        except Exception as exc:
            self.message.setText(f'Save failed: {exc}')
        finally:
            self.session.playing = previous
            self.refresh()

    def open(self):
        path, _ = QFileDialog.getOpenFileName(self, 'Open Physarum state', str(self.output), 'Saved state (bundle.json)')
        if not path:
            return
        self.load_state(Path(path))

    def load_state(self, path: Path):
        try:
            session, look = load_bundle(path)
            self.close_theta_monitor()
            self.session, self.look = session, look
            self.genesis_pair = self.before_genesis = None
            self.solo_session = None
            widgets = (self.guidance, self.palette, self.exposure, self.modes, self.preset, self.current, self.layer)
            for widget in widgets:
                widget.blockSignals(True)
            self.seed.setText(str(self.session.simulation.seed))
            self.guidance.setValue(round(self.session.target_guidance * 100))
            self.palette.setCurrentText(self.look.palette)
            self.layer.setCurrentIndex(self.layer.findData(self.look.layer))
            self.exposure.setValue(round(self.look.exposure * 100))
            self.current.setValue(round(session.simulation.rules.flow * 100))
            pair = (session.simulation.rules.mode_m, session.simulation.rules.mode_n)
            if self.modes.findData(pair) < 0:
                self.modes.addItem(f'Wave modes  {pair[0]} : {pair[1]}', pair)
            self.modes.setCurrentIndex(self.modes.findData(pair))
            population = session.simulation.population if isinstance(session.simulation, Chase) else session.simulation.rules.agents
            self.presets = {name: replace(rules, size=session.simulation.rules.size,
                                          agents=population)
                            for name, rules in PRESETS.items()}
            for widget in widgets:
                widget.blockSignals(False)
            self.fit_view()
            if self.formula_editor is not None:
                self.formula_editor.sync_target()
                from ..domain.formulas import FormulaSpec
                self.formula_editor.set_spec(session.simulation.formula.spec if session.simulation.formula is not None else FormulaSpec())
            self.message.setText('Restored state, paused. Play continues from the saved random-generator state.')
        except Exception as exc:
            self.message.setText(f'Open failed: {exc}')

    def closeEvent(self, event):
        self.timer.stop()
        self.close_theta_monitor()
        self.control_canvas.resize_timer.stop()
        if self.control_canvas.gpu is not None:
            self.control_canvas.gpu.close()
        if self.membrane_window is not None:
            self.membrane_window.close()
        self.canvas.resize_timer.stop()
        if self.formula_editor is not None:
            self.formula_editor.close()
        if self.canvas.gpu is not None:
            self.canvas.gpu.close()
        super().closeEvent(event)
