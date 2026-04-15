# ui_vispy.py



# VisPy + PyQt5 front-end for the modular Genesis Dash Grid.

# Tries to visually match ui_matplotlib3.py:

# - symmetric dashes

# - compression-driven contour shells

# - parameter sliders

# - GPU-friendly core state (via backend.xp)

from .backend import xp, to_cpu
from .core import GenesisState, GenesisParams, step
from . import rules_alignment
from . import rules_phase
from . import rules_dipoles
from . import rules_triads
from . import rules_curvature
from . import rules_compression
from . import relax

from vispy import app, scene
import numpy as np

from PyQt5.QtWidgets import (
QApplication,
QMainWindow,
QWidget,
QVBoxLayout,
QHBoxLayout,
QLabel,
QSlider,
)
from PyQt5.QtCore import Qt

from scipy.ndimage import gaussian_filter
from skimage import measure

# =========================

# Config

# =========================

N = 256          # grid size
DT = 0.05       # time step
DASH_LEN = 0.45 # dash length in grid units
CLICK_RADIUS = 2  # (currently unused; add mouse disturb later if you like)

# =========================

# Init state, params, rules

# =========================


state = GenesisState(N, DT)
params = GenesisParams()
# Ensure all slider params exist and are float
if not hasattr(params, 'alignment'):
    params.alignment = 1.0
if not hasattr(params, 'tension'):
    params.tension = 1.0
if not hasattr(params, 'geometry'):
    params.geometry = 1.0
if not hasattr(params, 'phase'):
    params.phase = 1.0
if not hasattr(params, 'dipole'):
    params.dipole = 1.0
if not hasattr(params, 'triad'):
    params.triad = 1.0
if not hasattr(params, 'curvature'):
    params.curvature = 1.0
# Add random disturbance to theta for visible initial movement
state.theta += 0.5 * (xp.random.rand(N, N) - 0.5)

rules = [
rules_alignment.alignment_rule,
rules_phase.phase_rule,
rules_dipoles.dipole_rule,
rules_triads.triad_rule,
rules_curvature.curvature_rule,
rules_compression.compression_rule,
relax.relaxation_rule,
]

# =========================

# Dash geometry helper

# =========================

def build_dash_segments(theta):
    """
    Build symmetric dash segments from theta field.
    Returns array shape (N^2, 2, 2) in CPU numpy for VisPy Line(connect='segments').
    """
    ny, nx = theta.shape
    ys, xs = xp.mgrid[0:ny, 0:nx]

    u = xp.cos(theta)
    v = xp.sin(theta)

    half = DASH_LEN * 0.5
    x0 = xs - half * u
    y0 = ys - half * v
    x1 = xs + half * u
    y1 = ys + half * v

    segs = xp.stack(
        [xp.stack([x0, y0], axis=-1), xp.stack([x1, y1], axis=-1)],
        axis=-2,
    )
    return to_cpu(segs.reshape(-1, 2, 2))

# =========================

# Main Window

# =========================

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Genesis Dash Grid - VisPy")
        self.resize(800, 800)
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)

        # Left: vertical slider panel
        self.slider_panel = QWidget()
        self.slider_layout = QVBoxLayout(self.slider_panel)
        self.sliders = []
        self.slider_labels = []
        # Only show sliders for these user-facing parameters, with user-friendly labels
        slider_specs = [
            ("Align (a)", "alignment"),
            ("Tension (y)", "tension"),
            ("Geometry (k)", "geometry"),
            ("Phase", "phase"),
            ("Dipoles", "dipole"),
            ("Triads", "triad"),
            ("Curvature", "curvature"),
        ]
        self.sliders = []
        self.slider_labels = []
        for label_text, pname in slider_specs:
            if hasattr(params, pname):
                label = QLabel(f"{label_text}: {getattr(params, pname):.2f}")
                slider = QSlider(Qt.Horizontal)
                slider.setMinimum(0)
                slider.setMaximum(100)
                slider.setValue(int(getattr(params, pname) * 100))
                slider.valueChanged.connect(lambda val, pn=pname, l=label, lt=label_text: self.on_slider_change(pn, val, l, lt))
            else:
                label = QLabel(f"{label_text}: 0.00 (not available)")
                slider = QSlider(Qt.Horizontal)
                slider.setMinimum(0)
                slider.setMaximum(100)
                slider.setValue(0)
                slider.setEnabled(False)
            self.slider_layout.addWidget(label)
            self.slider_layout.addWidget(slider)
            self.sliders.append(slider)
            self.slider_labels.append(label)

        # Add Contour Persistence slider (not in params)
        self.contour_persist_label = QLabel("Contour persistence: 40")
        self.contour_persist_slider = QSlider(Qt.Horizontal)
        self.contour_persist_slider.setMinimum(1)
        self.contour_persist_slider.setMaximum(200)
        self.contour_persist_slider.setValue(40)
        self.contour_persist_slider.valueChanged.connect(self.on_contour_persist_change)
        self.slider_layout.addWidget(self.contour_persist_label)
        self.slider_layout.addWidget(self.contour_persist_slider)

        self.slider_panel.setMinimumWidth(220)
        main_layout.addWidget(self.slider_panel)

        # Right: large VisPy canvas
        self.canvas = scene.SceneCanvas(keys='interactive', bgcolor='white', parent=central_widget, size=(800, 800))
        main_layout.addWidget(self.canvas.native)
        main_layout.setStretch(0, 0)  # sidebar fixed
        main_layout.setStretch(1, 1)  # canvas expands

        # Add a viewbox for dashes
        self.view = self.canvas.central_widget.add_view()
        self.view.camera = scene.PanZoomCamera(aspect=1)
        self.view.camera.set_range(x=(0, N), y=(0, N))

        # Draw initial dashes
        self.dash_segments = build_dash_segments(state.theta)
        self.dash_visual = scene.Line(pos=self.dash_segments.reshape(-1, 2), color='black', width=2, connect='segments', parent=self.view.scene)

        # Timer for animation
        self.timer = app.Timer(interval=0.03, connect=self.on_timer, start=True)

    def on_slider_change(self, pname, value, label, label_text):
        setattr(params, pname, value / 100.0)
        label.setText(f"{label_text}: {getattr(params, pname):.2f}")

    def on_contour_persist_change(self, value):
        self.contour_persist_label.setText(f"Contour persistence: {value}")
        # TODO: connect this value to your contour buffer logic if/when implemented

    def on_timer(self, event):
        step(state, params, rules)
        self.dash_segments = build_dash_segments(state.theta)
        self.dash_visual.set_data(pos=self.dash_segments.reshape(-1, 2))

# =========================

# Main entry

# =========================

if __name__ == "__main__":
    import sys
    appQt = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    appQt.exec_()