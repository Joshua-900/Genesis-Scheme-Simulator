"""A readout of the actual theta grid that drives the Genesis feed."""
import numpy as np
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtWidgets import (
    QCheckBox, QComboBox, QDialog, QDoubleSpinBox, QFormLayout, QHBoxLayout,
    QLabel, QPushButton, QTabWidget, QVBoxLayout, QWidget,
)

from src.genesis_sandbox.render import phase_colors

RULE_GROUPS = (
    ('Motion', (
        ('Neighbor alignment', 'alpha0', 0, 4, 'Turning toward nearby angles.'),
        ('Tension buildup', 'gamma0', 0, 4, 'Fresh tension from the net pull of neighbors.'),
        ('Tension decay', 'decay_tau', 0, 4, 'How quickly stored tension fades.'),
        ('Theta step size', 'dt', 0, 2, 'Size of the angle update per tick. Tension and geometry still update at zero.'),
    )),
    ('Patterns', (
        ('Phase wells', 'well0', 0, 4, 'Pull toward four preferred angles.'),
        ('Dipole strength', 'dipole0', 0, 4, 'Head-to-tail interaction between neighboring dashes.'),
        ('Triad strength', 'tri0', 0, 4, 'Pull toward triangular angle arrangements.'),
        ('Triad tolerance', 'tri_sigma', .1, 3, 'How far angles can deviate from a triangle template and still interact.'),
    )),
    ('Geometry', (
        ('Tension to displacement', 'kappa0', 0, 4, 'How strongly tension builds the displacement that guides Ivory.'),
        ('Displacement decay', 'geom_decay', 0, 4, 'How quickly existing displacement fades.'),
        ('Curvature feedback', 'curv0', 0, 4, 'How strongly local bending of displacement turns the dashes.'),
        ('Compression push', 'shell_geom_gain', 0, 4, 'How strongly compression gradients reshape displacement.'),
        ('Compression tolerance', 'sigma_c', .1, 3, 'How broadly the model registers compression as the local area changes.'),
    )),
    ('Locking', (
        ('Compression lock', 'lock_strength', 0, 1.33, 'How strongly compression suppresses angle changes.'),
        ('Phase boost', 'phase_lock_gain', 0, 4, 'How much compression strengthens phase wells.'),
        ('Triad boost', 'tri_lock_gain', 0, 4, 'How much compression strengthens triad interactions.'),
    )),
)


class ThetaMonitor(QDialog):
    def __init__(self, studio, feed):
        super().__init__(studio)
        self.setWindowTitle('Genesis · Theta monitor')
        self.feed = feed
        self.reference = self.theta.copy()
        self.reference_tick = feed.tick
        layout = QVBoxLayout(self)
        controls = QHBoxLayout()
        self.live = QCheckBox('Evolve with chase')
        self.live.toggled.connect(studio.change_genesis_evolution)
        step = QPushButton('Step Genesis')
        step.clicked.connect(studio.step_genesis)
        reference = QPushButton('Capture reference')
        reference.clicked.connect(self.capture_reference)
        for widget in (self.live, step, reference):
            controls.addWidget(widget)
        layout.addLayout(controls)

        choices = QHBoxLayout()
        self.view = QComboBox()
        self.view.addItems(('Theta angles', 'Change since reference'))
        self.view.currentIndexChanged.connect(self.draw_field)
        self.scale = QComboBox()
        for degrees in (1, 5, 30, 180):
            self.scale.addItem(f'Full brightness at {degrees}°', degrees)
        self.scale.setCurrentIndex(1)
        self.scale.currentIndexChanged.connect(self.draw_field)
        choices.addWidget(self.view)
        choices.addWidget(self.scale)
        layout.addLayout(choices)
        self.image = QLabel()
        self.image.setAlignment(Qt.AlignCenter)
        body = QHBoxLayout()
        body.addWidget(self.image)
        body.addLayout(self.build_rule_panel())
        layout.addLayout(body)
        self.status = QLabel()
        self.status.setWordWrap(True)
        layout.addWidget(self.status)
        self.draw_field()

    def build_rule_panel(self):
        panel = QVBoxLayout()
        tabs = QTabWidget()
        panel.addWidget(tabs)
        self.rule_controls = {}
        for title, parameters in RULE_GROUPS:
            page = QWidget()
            form = QFormLayout(page)
            for label, key, minimum, maximum, tooltip in parameters:
                control = QDoubleSpinBox()
                control.setRange(minimum, maximum)
                control.setDecimals(2)
                control.setSingleStep(.1)
                control.setSuffix(' ×')
                control.setValue(1)
                control.setKeyboardTracking(False)
                control.setToolTip(tooltip)
                control.valueChanged.connect(lambda value, name=key: self.feed.scale_parameter(name, value))
                self.rule_controls[key] = control
                form.addRow(label, control)
            tabs.addTab(page, title)
        note = QLabel('1× is the original setting. Changes apply on the next Genesis tick.')
        note.setWordWrap(True)
        panel.addWidget(note)
        reset = QPushButton('Reset rule settings')
        reset.setToolTip('Restore the original coefficients and keep the current field.')
        reset.clicked.connect(self.reset_rules)
        panel.addWidget(reset)
        panel.addStretch()
        return panel

    def reset_rules(self):
        for control in self.rule_controls.values():
            control.setValue(1)

    @property
    def theta(self):
        return self.feed.model.states['geometry_on']['theta']

    def capture_reference(self):
        self.reference = self.theta.copy()
        self.reference_tick = self.feed.tick
        self.draw_field()

    def refresh(self, live):
        self.live.blockSignals(True)
        self.live.setChecked(live)
        self.live.blockSignals(False)
        self.draw_field()

    def draw_field(self):
        theta = self.theta
        delta = np.rad2deg((theta - self.reference + np.pi) % (2 * np.pi) - np.pi)
        magnitude = np.abs(delta)
        show_delta = self.view.currentIndex() == 1
        self.scale.setEnabled(show_delta)
        if show_delta:
            intensity = np.sqrt(np.clip(magnitude / self.scale.currentData(), 0, 1))
            rgb = np.array([5, 12, 20]) + intensity[..., None] * np.array([245, 168, 74])
        else:
            rgb = phase_colors(theta)
        rgb = np.ascontiguousarray(rgb[::-1].astype(np.uint8))
        n = len(theta)
        image = QImage(rgb.data, n, n, rgb.strides[0], QImage.Format_RGB888)
        self.image.setPixmap(QPixmap.fromImage(image).scaled(448, 448, Qt.KeepAspectRatio, Qt.FastTransformation))
        mode = 'Evolving with chase' if self.live.isChecked() else 'Held'
        comparison = (' · Reference is current' if show_delta and self.reference_tick == self.feed.tick else '')
        self.status.setText(f'{mode} · Genesis tick {self.feed.tick:,} · Reference tick {self.reference_tick:,}\n'
                            f'Angle change · mean {magnitude.mean():.3g}° · peak {magnitude.max():.3g}°'
                            f'{comparison}')
