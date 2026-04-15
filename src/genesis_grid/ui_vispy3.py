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

N = 256
DT = 0.05
DASH_LEN = 0.45
RENDER_SUBSAMPLE = 4

# =========================
# Init state, params, rules
# =========================

state = GenesisState(N, DT)
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


def downsample_theta(theta, factor):
    """
    Block-average theta over (factor x factor) patches on GPU/xp.
    Returns a theta_ds with shape (ny/factor, nx/factor).
    """
    if factor <= 1:
        return theta

    ny, nx = theta.shape
    fy = ny // factor
    fx = nx // factor
    if fy == 0 or fx == 0:
        return theta

    theta_ = theta[: fy * factor, : fx * factor]
    theta_blocks = theta_.reshape(fy, factor, fx, factor)

    u = xp.cos(theta_blocks)
    v = xp.sin(theta_blocks)
    u_mean = u.mean(axis=(1, 3))
    v_mean = v.mean(axis=(1, 3))

    return xp.arctan2(v_mean, u_mean)


def downsample_scalar(field, factor):
    """Block-average scalar fields (phase/compression) for render resolution."""
    arr = np.asarray(to_cpu(field))
    if factor <= 1:
        return arr

    ny, nx = arr.shape
    fy = ny // factor
    fx = nx // factor
    if fy == 0 or fx == 0:
        return arr

    arr = arr[: fy * factor, : fx * factor]
    arr = arr.reshape(fy, factor, fx, factor).mean(axis=(1, 3))
    return arr


def build_dash_segments_for_render(theta):
    """
    Build symmetric dashes from a (possibly downsampled) theta field.
    Returns numpy array with shape (n_dashes, 2, 2).
    """
    theta_ds = downsample_theta(theta, RENDER_SUBSAMPLE)
    ny, nx = theta_ds.shape

    ys, xs = xp.mgrid[0:ny, 0:nx]
    scale = float(RENDER_SUBSAMPLE)

    # Place each coarse dash at the center of its source block.
    xs = xs * scale + 0.5 * (scale - 1.0)
    ys = ys * scale + 0.5 * (scale - 1.0)

    u = xp.cos(theta_ds)
    v = xp.sin(theta_ds)

    half = DASH_LEN * 0.5 * scale
    x0 = xs - half * u
    y0 = ys - half * v
    x1 = xs + half * u
    y1 = ys + half * v

    segs = xp.stack(
        [xp.stack([x0, y0], axis=-1), xp.stack([x1, y1], axis=-1)],
        axis=-2,
    )
    return to_cpu(segs.reshape(-1, 2, 2))


def hsv_to_rgb(h, s, v):
    """Vectorized HSV->RGB for numpy arrays in [0,1]."""
    h6 = (h * 6.0) % 6.0
    i = np.floor(h6).astype(np.int32)
    f = h6 - i

    p = v * (1.0 - s)
    q = v * (1.0 - f * s)
    t = v * (1.0 - (1.0 - f) * s)

    r = np.empty_like(h, dtype=np.float32)
    g = np.empty_like(h, dtype=np.float32)
    b = np.empty_like(h, dtype=np.float32)

    m0 = i == 0
    m1 = i == 1
    m2 = i == 2
    m3 = i == 3
    m4 = i == 4
    m5 = i == 5

    r[m0], g[m0], b[m0] = v[m0], t[m0], p[m0]
    r[m1], g[m1], b[m1] = q[m1], v[m1], p[m1]
    r[m2], g[m2], b[m2] = p[m2], v[m2], t[m2]
    r[m3], g[m3], b[m3] = p[m3], q[m3], v[m3]
    r[m4], g[m4], b[m4] = t[m4], p[m4], v[m4]
    r[m5], g[m5], b[m5] = v[m5], p[m5], q[m5]

    return np.stack([r, g, b], axis=-1)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Genesis Dash Grid - VisPy (v3)")
        self.resize(1000, 850)

        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)

        self.slider_panel = QWidget()
        self.slider_layout = QVBoxLayout(self.slider_panel)
        self.slider_layout.setSpacing(6)
        self.slider_panel.setMinimumWidth(240)

        slider_specs = [
            ("Align alpha", "alpha", 0.0, 1.2),
            ("Tension gamma", "gamma", 0.0, 0.2),
            ("Geometry kappa", "kappa", 0.0, 0.12),
            ("Phase", "phase", 0.0, 2.0),
            ("Dipoles", "dipole", 0.0, 2.0),
            ("Triads", "triads", 0.0, 2.5),
            ("Curvature", "curv", 0.0, 2.0),
            ("Lock", "lock_strength", 0.0, 1.0),
        ]

        self.slider_defs = []
        self.slider_labels = {}

        for title, attr, vmin, vmax in slider_specs:
            value = float(getattr(params, attr))
            label = QLabel(f"{title}: {value:.3f}")
            slider = QSlider(Qt.Horizontal)
            slider.setMinimum(0)
            slider.setMaximum(1000)

            frac = 0.0 if vmax == vmin else (value - vmin) / (vmax - vmin)
            frac = min(1.0, max(0.0, frac))
            slider.setValue(int(frac * 1000.0))

            slider.valueChanged.connect(self.make_slider_callback(attr, title, vmin, vmax))
            self.slider_layout.addWidget(label)
            self.slider_layout.addWidget(slider)

            self.slider_defs.append((attr, title, vmin, vmax, slider))
            self.slider_labels[attr] = label

        self.contour_persist_label = QLabel("Contour persistence: 20")
        self.contour_persist_slider = QSlider(Qt.Horizontal)
        self.contour_persist_slider.setMinimum(1)
        self.contour_persist_slider.setMaximum(200)
        self.contour_persist_slider.setValue(20)
        self.contour_persist_slider.valueChanged.connect(self.on_contour_persist_change)
        self.slider_layout.addWidget(self.contour_persist_label)
        self.slider_layout.addWidget(self.contour_persist_slider)

        self.help_label = QLabel("Keys: D toggle dashes, C toggle contours")
        self.slider_layout.addWidget(self.help_label)

        main_layout.addWidget(self.slider_panel)

        self.canvas = scene.SceneCanvas(keys="interactive", bgcolor="white", parent=central, size=(850, 850))
        main_layout.addWidget(self.canvas.native)
        main_layout.setStretch(0, 0)
        main_layout.setStretch(1, 1)

        self.view = self.canvas.central_widget.add_view()
        self.view.camera = scene.PanZoomCamera(aspect=1)
        self.view.camera.set_range(x=(0, N), y=(0, N))

        self.dashes = scene.visuals.Line(
            pos=np.zeros((0, 2), dtype=np.float32),
            connect="segments",
            color=(0.2, 0.2, 0.2, 1.0),
            width=1.0,
            parent=self.view.scene,
            method="gl",
            antialias=True,
        )
        self.dashes.visible = True

        self.contours = scene.visuals.Line(
            pos=np.zeros((0, 2), dtype=np.float32),
            connect=None,
            color=(0.05, 0.05, 0.05, 1.0),
            width=1.0,
            parent=self.view.scene,
            method="gl",
            antialias=True,
        )
        self.contours.visible = True

        self.show_dashes = True
        self.init_contour_buffer(length=20)

        self.canvas.events.key_press.connect(self.on_key_press)

        self.update(None)
        self.timer = app.Timer(interval=0.03, connect=self.update, start=True)

    def make_slider_callback(self, attr, title, vmin, vmax):
        def cb(raw_value):
            value = vmin + (vmax - vmin) * (raw_value / 1000.0)
            setattr(params, attr, value)
            self.slider_labels[attr].setText(f"{title}: {value:.3f}")

        return cb

    def init_contour_buffer(self, length=20):
        self.contour_buffer = []
        self.contour_buffer_length = int(length)

    def on_contour_persist_change(self, value):
        self.contour_buffer_length = int(value)
        self.contour_persist_label.setText(f"Contour persistence: {value}")

    def on_key_press(self, event):
        if event.key == "D":
            self.show_dashes = not self.show_dashes
            self.dashes.visible = self.show_dashes
        elif event.key == "C":
            self.contours.visible = not self.contours.visible

    def compute_dash_colors(self, angular_field):
        field_ds = downsample_scalar(angular_field, RENDER_SUBSAMPLE)
        hue = np.mod(field_ds, 2.0 * np.pi) / (2.0 * np.pi)
        sat = np.full_like(hue, 0.85, dtype=np.float32)
        val = np.full_like(hue, 0.95, dtype=np.float32)

        rgb = hsv_to_rgb(hue.astype(np.float32), sat, val).reshape(-1, 3)
        alpha = np.ones((rgb.shape[0], 1), dtype=np.float32)
        return np.concatenate([rgb, alpha], axis=1)

    def update_contours(self):
        C = to_cpu(state.C)

        C_smooth = (
            0.05 * C
            + 0.15 * (
                np.roll(C, 1, 0)
                + np.roll(C, -1, 0)
                + np.roll(C, 1, 1)
                + np.roll(C, -1, 1)
            )
            + 0.10 * (
                np.roll(np.roll(C, 1, 0), 1, 1)
                + np.roll(np.roll(C, 1, 0), -1, 1)
                + np.roll(np.roll(C, -1, 0), 1, 1)
                + np.roll(np.roll(C, -1, 0), -1, 1)
            )
        )
        C_smooth = gaussian_filter(C_smooth, sigma=1.2)

        c_min = float(C_smooth.min())
        c_max = float(C_smooth.max())
        if c_max - c_min < 1e-8:
            return

        lo = c_min + 0.30 * (c_max - c_min)
        hi = c_min + 0.90 * (c_max - c_min)
        levels = np.linspace(lo, hi, 6)

        frame_pos = []
        frame_conn = []
        offset = 0

        for lvl in levels:
            contour_list = measure.find_contours(C_smooth, lvl)
            for contour in contour_list:
                mapped = np.column_stack([contour[:, 1], contour[:, 0]])
                n = mapped.shape[0]
                if n < 2:
                    continue
                frame_pos.append(mapped)
                frame_conn.append(
                    np.column_stack(
                        [
                            np.arange(offset, offset + n - 1),
                            np.arange(offset + 1, offset + n),
                        ]
                    )
                )
                offset += n

        if frame_pos:
            frame_pos = np.vstack(frame_pos)
            frame_conn = np.vstack(frame_conn)
            self.contour_buffer.append((frame_pos, frame_conn))
            if len(self.contour_buffer) > self.contour_buffer_length:
                self.contour_buffer.pop(0)

        if not self.contour_buffer:
            self.contours.set_data(pos=np.zeros((0, 2), dtype=np.float32), connect=None)
            return

        all_pos = []
        all_conn = []
        offset = 0
        for pos, conn in self.contour_buffer:
            all_pos.append(pos)
            all_conn.append(conn + offset)
            offset += pos.shape[0]

        self.contours.set_data(
            pos=np.vstack(all_pos),
            connect=np.vstack(all_conn),
            color=(0.05, 0.05, 0.05, 1.0),
            width=1.0,
        )

    def update(self, event):
        step(state, params, rules)

        segs = build_dash_segments_for_render(state.theta)

        if hasattr(state, "phase"):
            phase_field = to_cpu(state.phase)
            if np.allclose(phase_field, phase_field.flat[0]):
                phase_field = to_cpu(state.theta)
        else:
            phase_field = to_cpu(state.theta)

        dash_colors = self.compute_dash_colors(phase_field)
        dash_colors_expanded = np.repeat(dash_colors, 2, axis=0)

        self.dashes.set_data(
            pos=segs.reshape(-1, 2),
            connect="segments",
            color=dash_colors_expanded,
        )

        if self.contours.visible:
            self.update_contours()


if __name__ == "__main__":
    import sys

    app_qt = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    app_qt.exec_()
