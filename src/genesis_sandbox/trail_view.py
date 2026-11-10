"""Linked planar and projected views of historical tracer samples."""
import math

import numpy as np
from PyQt5.QtCore import QPointF, QRectF, Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QColor, QImage, QPainter, QPen, QPixmap, QPolygonF
from PyQt5.QtWidgets import (
    QCheckBox, QHBoxLayout, QLabel, QMainWindow, QPushButton, QSlider, QSpinBox, QVBoxLayout, QWidget,
)

from .render import phase_colors
from .tracers import MAX_BALLS, TrailSession, height, sample_field


class TrailPane(QWidget):
    dropped = pyqtSignal(float, float)
    picked = pyqtSignal(object)

    def __init__(self, session, raised=False):
        super().__init__()
        self.session = session
        self.raised = raised
        self.selected = None
        self.image = None
        self.relief = raised
        self.show_arrows = True
        self.height_scale = .65
        self.relief_cache = None
        self.press = self.previous = None
        self.dragged = False
        self.reset_camera()
        self.setMinimumSize(360, 330)

    def reset_camera(self):
        self.yaw, self.pitch, self.zoom = -.65, .56, 1.
        n = self.session.model.n
        self.focus = (n / 2, n / 2, None)
        self.update()

    def focus_sample(self):
        if self.selected is not None:
            sample = self.selected
            self.focus = (sample.x, sample.y, float(height(sample.compression)))
            self.zoom = 3.
            self.update()

    def square(self):
        side = min(self.width(), self.height()) - 42
        return QRectF((self.width() - side) / 2, (self.height() - side) / 2, side, side)

    def project(self, xyz):
        n = self.session.model.n
        x, y, z = np.moveaxis(np.asarray(xyz), -1, 0)
        if not self.raised:
            rect = self.square()
            return np.stack((rect.left() + x / n * rect.width(),
                             rect.bottom() - y / n * rect.height(), z), axis=-1)
        focus_x, focus_y, focus_z = self.focus
        x, y = (x - focus_x) / n, (y - focus_y) / n
        z = z * .7 * self.height_scale
        z -= .18 * self.height_scale if focus_z is None else focus_z * .7 * self.height_scale
        c, s = math.cos(self.yaw), math.sin(self.yaw)
        east, north = c*x - s*y, s*x + c*y
        pitch_cos, pitch_sin = math.cos(self.pitch), math.sin(self.pitch)
        scale = min(self.width(), self.height()) * .66 * self.zoom
        return np.stack((self.width()/2 + scale*east,
                         self.height()/2 - scale*(pitch_sin*north + pitch_cos*z),
                         pitch_cos*north - pitch_sin*z), axis=-1)

    def refresh(self):
        if not self.raised:
            state = self.session.state
            strength = height(state['C'])[..., None]
            color = phase_colors(state['theta'])
            rgb = np.array([5, 12, 20]) + color * .045 + strength * np.array([82, 123, 128])
            if 'active' in state:
                rgb[~state['active']] = (5, 12, 20)
            rgb = np.ascontiguousarray(rgb[::-1].astype(np.uint8))
            n = self.session.model.n
            self.image = QImage(rgb.data, n, n, rgb.strides[0], QImage.Format_RGB888).copy()
        self.update()

    def traces(self):
        for ball in self.session.balls:
            samples = tuple(ball.trail)
            xy = np.array([(sample.x, sample.y) for sample in samples])
            z = height([sample.compression for sample in samples])
            yield samples, self.project(np.column_stack((xy, z)))

    def draw_floor(self, painter):
        n = self.session.model.n
        for value in np.linspace(0, n, 9):
            painter.setPen(QPen(QColor('#39525d' if value in (0, n) else '#23343e'), 1))
            for line in (((value, 0, 0), (value, n, 0)), ((0, value, 0), (n, value, 0))):
                a, b = self.project(line)
                painter.drawLine(QPointF(*a[:2]), QPointF(*b[:2]))
        a, b = self.project(((0, 0, 0), (0, 0, 1)))
        painter.setPen(QPen(QColor('#72918f'), 1, Qt.DashLine))
        painter.drawLine(QPointF(*a[:2]), QPointF(*b[:2]))
        painter.drawText(QPointF(b[0] + 5, b[1]), 'C = 1')

    def draw_relief(self, painter):
        key = (self.session.model.update, self.width(), self.height(), self.focus,
               self.yaw, self.pitch, self.zoom, self.height_scale)
        if self.relief_cache is not None and self.relief_cache[0] == key:
            painter.drawPixmap(0, 0, self.relief_cache[1])
            return
        n = self.session.model.n
        compression = self.session.state['C']
        z = height(np.pad(compression, ((0, 1), (0, 1)), mode='wrap'))
        x, y = np.meshgrid(np.arange(n + 1), np.arange(n + 1))
        vertices = self.project(np.stack((x, y, z), axis=-1))
        faces = np.stack((vertices[:-1, :-1], vertices[:-1, 1:],
                          vertices[1:, 1:], vertices[1:, :-1]), axis=-2).reshape(-1, 4, 3)
        mean_height = (z[:-1, :-1] + z[:-1, 1:] + z[1:, 1:] + z[1:, :-1]) * .25
        slope_x = ((z[:-1, 1:] - z[:-1, :-1]) + (z[1:, 1:] - z[1:, :-1])) * .5
        slope_y = ((z[1:, :-1] - z[:-1, :-1]) + (z[1:, 1:] - z[:-1, 1:])) * .5
        slope_x *= n * .7 * self.height_scale
        slope_y *= n * .7 * self.height_scale
        diffuse = np.clip((.42 * slope_x - .32 * slope_y + .85) /
                          np.sqrt(1 + slope_x**2 + slope_y**2), 0, 1)
        base = np.array([22, 43, 54]) + mean_height[..., None] * np.array([65, 101, 91])
        colors = np.clip(base * (.48 + .67 * diffuse[..., None]), 0, 255).astype(int).reshape(-1, 3)
        visible = ((faces[:, :, 0].max(axis=1) >= 0) & (faces[:, :, 0].min(axis=1) <= self.width()) &
                   (faces[:, :, 1].max(axis=1) >= 0) & (faces[:, :, 1].min(axis=1) <= self.height()))
        indices = np.flatnonzero(visible)
        indices = indices[np.argsort(faces[indices, :, 2].mean(axis=1))[::-1]]
        image = QPixmap(self.size())
        image.fill(Qt.transparent)
        surface = QPainter(image)
        surface.setPen(Qt.NoPen)
        for index in indices:
            surface.setBrush(QColor(*colors[index]))
            surface.drawPolygon(QPolygonF([QPointF(*point[:2]) for point in faces[index]]))
        surface.end()
        self.relief_cache = (key, image)
        painter.drawPixmap(0, 0, image)

    def draw_arrows(self, painter):
        if not self.show_arrows or not self.session.balls:
            return
        anchor = self.selected or self.session.balls[0].trail[-1]
        n = self.session.model.n
        painter.setPen(QPen(QColor('#91ebe3'), 1.35, Qt.SolidLine, Qt.RoundCap))
        for ox in (-3, 0, 3):
            for oy in (-3, 0, 3):
                x, y = anchor.x + ox, anchor.y + oy
                if not (0 <= x < n and 0 <= y < n):
                    continue
                ux, uy, compression, _ = sample_field(self.session.state, (x, y))
                norm = math.hypot(ux, uy)
                if norm < .004:
                    continue
                z = float(height(compression)) + .018 if self.raised and self.relief else .018
                length = 2.5 / (.13 + norm)
                start, end = self.project(((x, y, z), (x + ux*length, y + uy*length, z)))[:, :2]
                vector = end - start
                pixels = np.linalg.norm(vector)
                if pixels < 3:
                    continue
                unit = vector / pixels
                head = min(5., pixels * .4)
                normal = np.array([-unit[1], unit[0]])
                painter.drawLine(QPointF(*start), QPointF(*end))
                for side in (-1, 1):
                    wing = end - unit*head + normal*head*.55*side
                    painter.drawLine(QPointF(*end), QPointF(*wing))

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor('#090f17'))
        painter.setRenderHint(QPainter.Antialiasing)
        if self.raised:
            self.draw_floor(painter)
            if self.relief:
                self.draw_relief(painter)
        elif self.image is not None:
            painter.setRenderHint(QPainter.SmoothPixmapTransform)
            painter.drawImage(self.square(), self.image)
            painter.setPen(QPen(QColor('#344c59'), 1))
            painter.drawRect(self.square())
        self.draw_arrows(painter)

        segments, heads = [], []
        for samples, coordinates in self.traces():
            colors = phase_colors(np.array([sample.angle for sample in samples]))
            for index in range(1, len(samples)):
                if not samples[index].wrapped:
                    start, end = coordinates[index - 1:index + 1]
                    age = 1 - min(1., (self.session.model.update - samples[index].tick) / 600)
                    segments.append((end[2], start, end, colors[index], age))
            heads.append((coordinates[-1], colors[-1]))
        if self.raised:
            segments.sort(key=lambda segment: segment[0], reverse=True)
        for _, start, end, rgb, age in segments:
            color = QColor(*(int(channel) for channel in rgb), round(30 + 215 * age))
            painter.setPen(QPen(color, 1.2 + 1.3 * age, Qt.SolidLine, Qt.RoundCap))
            painter.drawLine(QPointF(*start[:2]), QPointF(*end[:2]))
        for point, rgb in heads:
            color = QColor(*(int(channel) for channel in rgb))
            center = QPointF(*point[:2])
            painter.setPen(Qt.NoPen)
            color.setAlpha(75)
            painter.setBrush(color)
            painter.drawEllipse(center, 9, 9)
            painter.setBrush(QColor('#f9f5df'))
            painter.drawEllipse(center, 4, 4)
        if self.selected is not None:
            sample = self.selected
            live_height = 0.
            if self.raised and self.relief:
                _, _, compression, _ = sample_field(self.session.state, (sample.x, sample.y))
                live_height = float(height(compression))
            base, point = self.project(((sample.x, sample.y, live_height),
                                        (sample.x, sample.y, height(sample.compression))))
            painter.setPen(QPen(QColor('#ffedbc'), 1, Qt.DashLine))
            painter.drawLine(QPointF(*base[:2]), QPointF(*point[:2]))
            painter.setPen(QPen(QColor('#ffedbc'), 2))
            painter.setBrush(Qt.NoBrush)
            painter.drawEllipse(QPointF(*point[:2]), 7, 7)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.press = self.previous = event.localPos()
            self.dragged = False

    def mouseMoveEvent(self, event):
        if self.raised and self.press is not None and event.buttons() & Qt.LeftButton:
            point = event.localPos()
            if (point - self.press).manhattanLength() > 4:
                self.dragged = True
            if self.dragged:
                delta = point - self.previous
                self.yaw += delta.x() * .009
                self.pitch = float(np.clip(self.pitch + delta.y() * .009, .08, 1.55))
                self.update()
            self.previous = point

    def mouseReleaseEvent(self, event):
        if event.button() != Qt.LeftButton or self.press is None:
            return
        self.press = None
        point = event.localPos()
        if self.dragged:
            return
        if self.raised:
            nearest, distance = None, 13.
            for samples, coordinates in self.traces():
                distances = np.hypot(coordinates[:, 0] - point.x(), coordinates[:, 1] - point.y())
                index = int(np.argmin(distances))
                if distances[index] < distance:
                    nearest, distance = samples[index], distances[index]
            if nearest is not None:
                self.picked.emit(nearest)
        else:
            rect = self.square()
            if rect.contains(point):
                n = self.session.model.n
                self.dropped.emit((point.x() - rect.left()) / rect.width() * n,
                                  (rect.bottom() - point.y()) / rect.height() * n)

    def wheelEvent(self, event):
        if self.raised:
            self.zoom = float(np.clip(self.zoom * 1.15**(event.angleDelta().y()/120), .6, 5.))
            self.update()


class TrailWindow(QMainWindow):
    def __init__(self, model, demo=True):
        super().__init__()
        self.session = TrailSession(model)
        self.playing = False
        if demo:
            self.session.advance(125)
            self.session.drop(model.n * .625, model.n * .375, 3)
            self.session.advance(145)
        self.setWindowTitle('Genesis · Sheet & Trails')
        self.resize(1280, 760)
        self.setStyleSheet('''
            QWidget { background:#101820; color:#e6e7de; font-size:13px; }
            QPushButton { background:#253841; border:1px solid #465b63;
                          padding:8px 14px; border-radius:5px; }
            QPushButton:hover { background:#35505a; }
        ''')
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(20, 18, 20, 18)
        heading = QLabel('GENESIS / SHEET & TRAILS')
        heading.setStyleSheet('font-size:23px; font-weight:bold; color:#ffedbc')
        layout.addWidget(heading)
        toolbar = QHBoxLayout()
        self.play = QPushButton('Pause')
        self.play.clicked.connect(self.toggle)
        step = QPushButton('Step')
        step.clicked.connect(self.step_once)
        clear = QPushButton('Clear trails')
        clear.clicked.connect(self.clear)
        camera = QPushButton('Reset view')
        self.ball_count = QSpinBox()
        self.ball_count.setRange(1, MAX_BALLS)
        self.ball_count.setValue(3)
        self.ball_count.setAccessibleName('Balls per drop')
        self.ball_count.setToolTip('Up to 24 balls on the sheet. New drops replace the oldest balls at the limit.')
        for control in (self.play, step, clear, camera, QLabel('Balls per drop'), self.ball_count):
            toolbar.addWidget(control)
        toolbar.addStretch()
        self.status = QLabel()
        toolbar.addWidget(self.status)
        layout.addLayout(toolbar)
        panels = QHBoxLayout()
        self.sheet = TrailPane(self.session)
        self.sculpture = TrailPane(self.session, raised=True)
        self.sheet.dropped.connect(self.drop)
        self.sculpture.picked.connect(self.select)
        camera.clicked.connect(self.sculpture.reset_camera)
        view_tools = QHBoxLayout()
        relief = QCheckBox('Compression relief')
        relief.setChecked(True)
        relief.toggled.connect(self.toggle_relief)
        arrows = QCheckBox('Displacement arrows')
        arrows.setChecked(True)
        arrows.toggled.connect(self.toggle_arrows)
        self.height_label = QLabel('Height 0.65×')
        height_slider = QSlider(Qt.Horizontal)
        height_slider.setRange(0, 160)
        height_slider.setValue(65)
        height_slider.setFixedWidth(145)
        height_slider.setAccessibleName('Compression height')
        height_slider.valueChanged.connect(self.change_height)
        self.zoom_sample = QPushButton('Zoom to sample')
        self.zoom_sample.clicked.connect(self.sculpture.focus_sample)
        for control in (relief, arrows, self.height_label, height_slider, self.zoom_sample):
            view_tools.addWidget(control)
        view_tools.addStretch()
        layout.addLayout(view_tools)
        for title, pane in (('LIVE SHEET  /  Compression map · Click to drop', self.sheet),
                            ('COMPRESSION HEIGHT  /  Drag to orbit · Wheel to zoom · Click a trail to inspect', self.sculpture)):
            panel = QVBoxLayout()
            label = QLabel(title)
            label.setWordWrap(True)
            panel.addWidget(label)
            panel.addWidget(pane, 1)
            panels.addLayout(panel, 1)
        layout.addLayout(panels, 1)
        self.detail = QLabel('Relief shows current compression. Trails show compression recorded over time. Cyan arrows show the local displacement that steers the balls.')
        self.detail.setWordWrap(True)
        layout.addWidget(self.detail)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.tick)
        self.timer.start(45)
        self.refresh()

    def refresh(self):
        self.play.setText('Pause' if self.playing else 'Play')
        self.status.setText(f'Tick {self.session.model.update:,}  /  {len(self.session.balls)} balls')
        sample = self.sculpture.selected
        self.zoom_sample.setEnabled(sample is not None)
        if sample is not None:
            _, _, current, _ = sample_field(self.session.state, (sample.x, sample.y))
            self.detail.setText(f'Sample at tick {sample.tick:,}  /  x {sample.x:.2f}  /  y {sample.y:.2f}'
                                f'  /  recorded C {sample.compression:.4g}  /  current C {current:.4g}'
                                f'  /  recorded angle {math.degrees(sample.angle):.1f}°')
        self.sheet.refresh()
        self.sculpture.refresh()

    def toggle_relief(self, enabled):
        self.sculpture.relief = enabled
        self.sculpture.update()

    def toggle_arrows(self, enabled):
        for pane in (self.sheet, self.sculpture):
            pane.show_arrows = enabled
            pane.update()

    def change_height(self, value):
        self.sculpture.height_scale = value / 100
        self.height_label.setText(f'Height {value / 100:.2f}×')
        self.sculpture.update()

    def tick(self):
        if self.playing:
            self.session.advance(2)
            self.refresh()

    def toggle(self):
        self.playing = not self.playing
        self.refresh()

    def step_once(self):
        self.playing = False
        self.session.advance()
        self.refresh()

    def drop(self, x, y):
        self.session.drop(x, y, self.ball_count.value())
        self.refresh()

    def clear(self):
        self.session.balls.clear()
        self.sheet.selected = self.sculpture.selected = None
        self.detail.setText('Click the sheet to drop a ball and start a new trail.')
        self.refresh()

    def select(self, sample):
        self.playing = False
        self.sheet.selected = self.sculpture.selected = sample
        self.refresh()

    def closeEvent(self, event):
        self.timer.stop()
        super().closeEvent(event)
