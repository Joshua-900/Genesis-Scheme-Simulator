"""Interactive view of a growing membrane and its recent outlines."""
from collections import deque

from PyQt5.QtCore import QPointF, Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QColor, QPainter, QPainterPath, QPen, QRadialGradient
from PyQt5.QtWidgets import (
    QApplication, QCheckBox, QHBoxLayout, QLabel, QLineEdit, QMainWindow,
    QPushButton, QSlider, QVBoxLayout, QWidget,
)

from ..domain.membrane import Membrane


class MembraneView(QWidget):
    painted = pyqtSignal(float, float)

    def __init__(self, model):
        super().__init__()
        self.model = model
        self.history = deque(maxlen=40)
        self.show_history = True
        self.setMinimumSize(360, 360)
        self.setCursor(Qt.CrossCursor)

    def transform(self):
        return self.width() / 2, self.height() / 2, min(self.width(), self.height()) * .49

    def outline(self, points, cx, cy, scale):
        path = QPainterPath()
        path.moveTo(cx + scale * points[0, 0], cy - scale * points[0, 1])
        for x, y in points[1:]:
            path.lineTo(cx + scale * x, cy - scale * y)
        path.closeSubpath()
        return path

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        cx, cy, scale = self.transform()
        backdrop = QRadialGradient(QPointF(cx, cy), scale * 1.7)
        backdrop.setColorAt(0, QColor('#152229'))
        backdrop.setColorAt(1, QColor('#070c12'))
        painter.fillRect(self.rect(), backdrop)
        if self.show_history:
            for index, points in enumerate(self.history):
                age = (index + 1) / len(self.history)
                painter.setPen(QPen(QColor(109, 172, 167, round(6 + 62 * age**2)), .8))
                painter.drawPath(self.outline(points, cx, cy, scale))
        path = self.outline(self.model.points, cx, cy, scale)
        painter.setPen(QPen(QColor(224, 178, 99, 40), 5))
        painter.drawPath(path)
        painter.setPen(QPen(QColor('#ffedc6'), 1.5))
        painter.drawPath(path)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(255, 156, 83, 160))
        for x, y in self.model.points[self.model.paint > .25][::2]:
            painter.drawEllipse(QPointF(cx + scale * x, cy - scale * y), 2, 2)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.paint_growth(event.localPos())

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.LeftButton:
            self.paint_growth(event.localPos())

    def paint_growth(self, position):
        cx, cy, scale = self.transform()
        self.painted.emit((position.x() - cx) / scale, (cy - position.y()) / scale)


class MembraneWindow(QMainWindow):
    def __init__(self, seed=7, parent=None):
        super().__init__(parent, Qt.Window)
        self.model = Membrane(seed)
        self.playing = True
        self.setWindowTitle('Membrane Studio')
        self.resize(1180, 820)
        self.setStyleSheet('''
            QWidget { background: #101820; color: #e7e5d8; font-size: 13px; }
            QPushButton, QLineEdit { background: #223038; border: 1px solid #3d555a;
                                     border-radius: 5px; padding: 8px; }
            QPushButton:hover { background: #33464b; }
        ''')
        central = QWidget()
        self.setCentralWidget(central)
        layout = QHBoxLayout(central)
        layout.setContentsMargins(18, 18, 18, 18)
        sidebar = QWidget()
        sidebar.setFixedWidth(245)
        controls = QVBoxLayout(sidebar)
        controls.setContentsMargins(0, 5, 10, 0)
        controls.setSpacing(12)
        title = QLabel('GROWING MEMBRANE')
        title.setStyleSheet('font-size: 20px; font-weight: bold; color: #ffedc6;')
        controls.addWidget(title)
        hint = QLabel('Drag along the ivory edge to add local growth. Amber marks show where your brush is active.')
        hint.setWordWrap(True)
        controls.addWidget(hint)
        self.play = QPushButton('Pause')
        self.play.clicked.connect(self.toggle)
        step = QPushButton('Step')
        step.clicked.connect(self.step_once)
        reset = QPushButton('Reset ring')
        reset.clicked.connect(self.reset)
        for button in (self.play, step, reset):
            controls.addWidget(button)
        controls.addWidget(QLabel('Base growth'))
        self.growth = QSlider(Qt.Horizontal)
        self.growth.setRange(0, 200)
        self.growth.setValue(100)
        controls.addWidget(self.growth)
        traces = QCheckBox('Show contour history')
        traces.setChecked(True)
        traces.toggled.connect(self.toggle_history)
        controls.addWidget(traces)
        controls.addWidget(QLabel('Growth multiplier  f(x, y, t)'))
        self.formula = QLineEdit()
        self.formula.setPlaceholderText('1 + .8*sin(8*x - 2*t)')
        self.formula.setMaxLength(512)
        self.formula.returnPressed.connect(self.apply_formula)
        controls.addWidget(self.formula)
        self.apply = QPushButton('Apply growth formula')
        self.apply.clicked.connect(self.apply_formula)
        controls.addWidget(self.apply)
        self.status = QLabel()
        self.status.setWordWrap(True)
        controls.addWidget(self.status)
        self.message = QLabel('An empty formula uses uniform growth.')
        self.message.setWordWrap(True)
        controls.addWidget(self.message)
        controls.addStretch()
        layout.addWidget(sidebar)
        self.canvas = MembraneView(self.model)
        self.canvas.painted.connect(self.paint_growth)
        layout.addWidget(self.canvas, 1)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.advance)
        self.timer.start(30)
        self.refresh()

    def refresh(self):
        self.play.setText('Pause' if self.playing else 'Play')
        count = len(self.model.points)
        capped = count >= self.model.max_nodes
        limit = '\nGrowth limit reached. Apply & regrow to try a new formula.' if capped else ''
        self.status.setText(f'Tick {self.model.tick:,}   /   {count:,} points{limit}')
        if capped:
            self.apply.setText('Apply & regrow')
        elif not self.playing:
            self.apply.setText('Apply & play')
        else:
            self.apply.setText('Apply growth formula')
        self.canvas.update()

    def toggle(self):
        self.playing = not self.playing
        self.refresh()

    def advance(self, count=3, *, force=False):
        if not self.playing and not force:
            return
        try:
            for _ in range(count):
                self.model.step(self.growth.value() / 100)
                if self.model.tick % 9 == 0:
                    self.canvas.history.append(self.model.points.copy())
        except ValueError as exc:
            self.playing = False
            self.message.setText(f'Growth paused. {exc}')
        self.refresh()

    def step_once(self):
        self.playing = False
        self.advance(1, force=True)

    def reset(self):
        self.model = Membrane(self.model.seed)
        self.canvas.model = self.model
        self.canvas.history.clear()
        self.formula.clear()
        self.message.setText('Ring reset. Base growth is uniform.')
        self.refresh()

    def apply_formula(self):
        capped = len(self.model.points) >= self.model.max_nodes
        model = Membrane(self.model.seed, self.model.max_nodes) if capped else self.model
        try:
            model.set_formula(self.formula.text())
        except ValueError as exc:
            self.message.setText(str(exc))
            return
        if capped:
            self.model = model
            self.canvas.model = model
            self.canvas.history.clear()
        self.playing = True
        message = 'Growing a fresh ring.' if capped else 'Growth formula applied.'
        if self.growth.value() == 0:
            message += ' Raise Base growth to see the formula take effect.'
        self.message.setText(message)
        self.refresh()

    def paint_growth(self, x, y):
        self.model.brush(x, y)
        self.canvas.update()

    def toggle_history(self, enabled):
        self.canvas.show_history = enabled
        self.canvas.update()

    def closeEvent(self, event):
        self.timer.stop()
        super().closeEvent(event)


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Open Membrane Studio.')
    parser.add_argument('--seed', type=int, default=7)
    args = parser.parse_args()
    if args.seed < 0:
        parser.error('Seed must be nonnegative.')
    app = QApplication([])
    window = MembraneWindow(args.seed)
    window.show()
    raise SystemExit(app.exec_())
