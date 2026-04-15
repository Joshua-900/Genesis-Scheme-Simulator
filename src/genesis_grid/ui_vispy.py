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
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSlider
from PyQt5.QtCore import Qt

# =========================
# Config
# =========================
N  = 64      # grid size
DT = 0.05    # time step
DASH_LEN     = 0.45   # dash length in grid units
CLICK_RADIUS = 2      # mouse disturbance radius (cells)

# =========================
# Init state, params, rules
# =========================
state  = GenesisState(N, DT)
params = GenesisParams()
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
# PyQt5 + VisPy UI
# =========================
class MainWindow(QMainWindow):
    def set_contour_buffer_length(self, length):
        if length == -1:
            self.contour_buffer_length = float('inf')  # Never remove contours
        else:
            self.contour_buffer_length = length

    def on_contour_persist_change(self, val):
        # If slider is at max, set to infinite persistence
        if val == self.contour_persist_slider.maximum():
            self.set_contour_buffer_length(-1)
        else:
            self.set_contour_buffer_length(val)
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Genesis Dash Grid — VisPy + PyQt5")
        central = QWidget()
        self.setCentralWidget(central)
        layout = QHBoxLayout()
        central.setLayout(layout)

        # Left: Sliders
        slider_widget = QWidget()
        slider_layout = QVBoxLayout()
        slider_widget.setLayout(slider_layout)
        layout.addWidget(slider_widget)

        self.slider_defs = [
            ("alpha",  0.0, 1.0,  params.alpha,  "Align α"),
            ("gamma",  0.0, 0.2,  params.gamma,  "Tension γ"),
            ("kappa",  0.0, 0.05, params.kappa,  "Geometry κ"),
            ("phase",  0.0, 2.0,  params.phase,  "Phase"),
            ("dipole", 0.0, 1.5,  params.dipole, "Dipoles"),
            ("triads", 0.0, 2.0,  params.triads, "Triads"),
            ("curv",   0.0, 2.0,  params.curv,   "Curvature"),
        ]
        self.slider_objs = {}
        for name, vmin, vmax, v0, label in self.slider_defs:
            row = QHBoxLayout()
            lab = QLabel(label)
            slider = QSlider(Qt.Horizontal)
            slider.setMinimum(0)
            slider.setMaximum(1000)
            slider.setValue(int(1000 * (v0 - vmin) / (vmax - vmin)))
            slider.setFixedWidth(200)
            slider.valueChanged.connect(self.make_slider_callback(name, vmin, vmax))
            row.addWidget(lab)
            row.addWidget(slider)
            slider_layout.addLayout(row)
            self.slider_objs[name] = slider

        # Right: VisPy canvas
        self.canvas = scene.SceneCanvas(keys='interactive', show=False)
        layout.addWidget(self.canvas.native)
        view = self.canvas.central_widget.add_view()
        # Set camera for pixel-perfect grid, fixed aspect, and no zoom
        view.camera = scene.PanZoomCamera(rect=(0, 0, N, N), aspect=1.0, interactive=True)
        view.camera.set_range(x=(0, N), y=(0, N))
        view.camera.aspect = 1.0

        # Compression heatmap (higher contrast colormap)

        # Use high-contrast colormap, bicubic interpolation, and high alpha
        # Set background to white for clarity
        self.canvas.bgcolor = (0.97, 0.97, 0.97, 1.0)  # very light grey
        # Contours: dark grey, thinner, anti-aliased
        self.contours = scene.visuals.Line(pos=np.zeros((0, 2)), color=(0.25,0.25,0.25,1.0), width=1.2, parent=view.scene, method='gl', antialias=True)
        self.contours.visible = True
        # Dashes: dark grey, thinner, anti-aliased
        init_segs = build_dash_segments(state.theta)
        self.dashes = scene.visuals.Line(pos=init_segs.reshape(-1, 2), color=(0.25,0.25,0.25,1.0), width=1.0, parent=view.scene, connect='segments', method='gl', antialias=True)
        self.dashes.visible = True

        # Dash toggle state
        self.show_dashes = True

        # Timer for animation
        # Add slider for contour persistence
        self.contour_persist_slider = QSlider(Qt.Horizontal)
        self.contour_persist_slider.setMinimum(1)
        self.contour_persist_slider.setMaximum(200)
        self.contour_persist_slider.setValue(40)
        self.contour_persist_slider.setFixedWidth(200)
        self.contour_persist_slider.valueChanged.connect(self.on_contour_persist_change)
        persist_row = QHBoxLayout()
        persist_lab = QLabel("Contour Persistence")
        persist_row.addWidget(persist_lab)
        persist_row.addWidget(self.contour_persist_slider)
        slider_layout.addLayout(persist_row)
        self.timer = app.Timer(interval=0.03, connect=self.update, start=True)

        # Keyboard event for dash toggle
        self.canvas.events.key_press.connect(self.on_key_press)
        self.init_contour_buffer(length=15)  # Contours persist for 15 frames

    def init_contour_buffer(self, length=40):
        self.contour_buffer = []
        self.contour_buffer_length = length

    def make_slider_callback(self, name, vmin, vmax):
        def callback(val):
            value = vmin + (vmax - vmin) * (val / 1000.0)
            setattr(params, name, value)
        return callback

    def on_key_press(self, event):
        if event.key == 'D':
            self.show_dashes = not self.show_dashes
            self.dashes.visible = self.show_dashes
        if event.key == 'C':
            self.contours.visible = not self.contours.visible

    def update(self, event):
        # Debug output for state
        print('C min/max:', np.min(to_cpu(state.C)), np.max(to_cpu(state.C)))
        print('theta min/max:', np.min(to_cpu(state.theta)), np.max(to_cpu(state.theta)))
        step(state, params, rules)
        segs = build_dash_segments(state.theta)
        self.dashes.set_data(pos=segs.reshape(-1, 2))
        # Improved contour rendering: smooth compression field, multiple levels
        if self.contours.visible:
            # Match Matplotlib: use smoothed compression field and grid mesh
            from scipy.ndimage import gaussian_filter
            C = to_cpu(state.C)
            C_smooth = (
                0.05 * C +
                0.15 * (np.roll(C, 1, 0) + np.roll(C, -1, 0) +
                        np.roll(C, 1, 1) + np.roll(C, -1, 1)) +
                0.10 * (np.roll(np.roll(C, 1, 0), 1, 1) +
                        np.roll(np.roll(C, 1, 0), -1, 1) +
                        np.roll(np.roll(C, -1, 0), 1, 1) +
                        np.roll(np.roll(C, -1, 0), -1, 1))
            )
            C_smooth = gaussian_filter(C_smooth, sigma=1.2)
            levels = np.linspace(0.25, 0.80, 6)
            from skimage import measure
            all_contours = []
            for lvl in levels:
                cs = measure.find_contours(C_smooth, lvl)
                for c in cs:
                    # Map to grid mesh coordinates
                    mapped = np.column_stack([c[:, 1], c[:, 0]])
                    all_contours.append(mapped)
            if all_contours:
                all_pts = np.concatenate(all_contours, axis=0)
                self.contour_buffer.append(all_pts)
                if len(self.contour_buffer) > self.contour_buffer_length:
                    self.contour_buffer.pop(0)
                buffer_pts = np.concatenate(self.contour_buffer, axis=0)
                self.contours.set_data(pos=buffer_pts, color='black', width=1.0)
            else:
                if self.contour_buffer:
                    buffer_pts = np.concatenate(self.contour_buffer, axis=0)
                    self.contours.set_data(pos=buffer_pts, color='black', width=1.0)
                else:
                    self.contours.set_data(pos=np.zeros((0, 2)), color='black', width=1.0)

if __name__ == '__main__':
    import sys
    appQt = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    appQt.exec_()
