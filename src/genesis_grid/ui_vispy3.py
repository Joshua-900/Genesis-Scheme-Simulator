# ui_vispy.py



# VisPy + PyQt5 front-end for the modular Genesis Dash Grid.

# - GPU state via backend.xp

# - Symmetric dashes

# - Compression-driven contour shells

# - Coarse-grained dash rendering to avoid aliasing: each dash represents

# a block of cells (RENDER_SUBSAMPLE x RENDER_SUBSAMPLE).

from backend import xp, to_cpu
from core import GenesisState, GenesisParams, step
import rules_alignment
import rules_phase
import rules_dipoles
import rules_triads
import rules_curvature
import rules_compression
import relax

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

N = 256          # grid size (works fine with 64 too)
DT = 0.05        # time step
DASH_LEN = 0.45  # dash length in cell units
CLICK_RADIUS = 2  # (unused for now – easy to add later)

# Coarse-graining factor for rendering:

# 1 = one dash per cell (max detail, aliasing when zoomed out)

# 2 = dash per 2x2 block

# 4 = dash per 4x4 block (good mesoscale)

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

# =========================

# Dash geometry helpers

# =========================

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
        return theta  # fallback

    # trim to multiple of factor
    theta_ = theta[: fy * factor, : fx * factor]

    # reshape into blocks (fy, factor, fx, factor)
    theta_blocks = theta_.reshape(fy, factor, fx, factor)

    # average unit vectors inside each block
    u = xp.cos(theta_blocks)
    v = xp.sin(theta_blocks)
    u_mean = u.mean(axis=(1, 3))
    v_mean = v.mean(axis=(1, 3))

    theta_ds = xp.arctan2(v_mean, u_mean)
    return theta_ds

                        np.arange(offset, offset + n - 1),
                        np.arange(offset + 1, offset + n),
                    ])
                    frame_conn.append(seg_idx)
                    offset += n
            if frame_pos:
                frame_pos = np.vstack(frame_pos)
                frame_conn = np.vstack(frame_conn)
                self.contour_buffer.append((frame_pos, frame_conn))
                if (
                    self.contour_buffer_length is not None
                    and len(self.contour_buffer) > self.contour_buffer_length
                ):
                    self.contour_buffer.pop(0)
            if self.contour_buffer:
                all_pos = []
                all_conn = []
                offset = 0
                def update(self, event):
                    print("update called")  # Debug print to confirm animation loop
                    # Print min/max of phase and theta to confirm state is changing
                    phase_arr = to_cpu(state.phase) if hasattr(state, 'phase') else None
                    theta_arr = to_cpu(state.theta)
                    if phase_arr is not None:
                        print(f"phase min/max: {phase_arr.min():.4f} / {phase_arr.max():.4f}")
                    print(f"theta min/max: {theta_arr.min():.4f} / {theta_arr.max():.4f}")
                    step(state, params, rules)
                    segs = build_dash_segments_for_render(state.theta)
                    # Color code dashes by phase
                    if hasattr(state, 'phase'):
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
                        C = to_cpu(state.C)
                        C_smooth = (
                            0.05 * C
                            + 0.15
                            * (
                                np.roll(C, 1, 0)
                                + np.roll(C, -1, 0)
                                + np.roll(C, 1, 1)
                                + np.roll(C, -1, 1)
                            )
                            + 0.10
                            * (
                                np.roll(np.roll(C, 1, 0), 1, 1)
                                + np.roll(np.roll(C, 1, 0), -1, 1)
                                + np.roll(np.roll(C, -1, 0), 1, 1)
                                + np.roll(np.roll(C, -1, 0), -1, 1)
                            )
                        )
                        C_smooth = gaussian_filter(C_smooth, sigma=1.2)
                        c_min = float(C_smooth.min())
                        c_max = float(C_smooth.max())
                        if c_max - c_min < 1e-6:
                            return
                        lo = c_min + 0.30 * (c_max - c_min)
                        hi = c_min + 0.90 * (c_max - c_min)
                        levels = np.linspace(lo, hi, 6)
                        frame_pos = []
                        frame_conn = []
                        offset = 0
                        for lvl in levels:
                            cs_list = measure.find_contours(C_smooth, lvl)
                            for c in cs_list:
                                mapped = np.column_stack([c[:, 1], c[:, 0]])
                                n = mapped.shape[0]
                                if n < 2:
                                    continue
                                frame_pos.append(mapped)
                                seg_idx = np.column_stack([
                                    np.arange(offset, offset + n - 1),
                                    np.arange(offset + 1, offset + n),
                                ])
                                frame_conn.append(seg_idx)
                                offset += n
                        if frame_pos:
                            frame_pos = np.vstack(frame_pos)
                            frame_conn = np.vstack(frame_conn)
                            self.contour_buffer.append((frame_pos, frame_conn))
                            if (
                                self.contour_buffer_length is not None
                                and len(self.contour_buffer) > self.contour_buffer_length
                            ):
                                self.contour_buffer.pop(0)
                        if self.contour_buffer:
                            all_pos = []
                            all_conn = []
                            offset = 0
                            for pos, conn in self.contour_buffer:
                                all_pos.append(pos)
                                all_conn.append(conn + offset)
                                offset += pos.shape[0]
                            pos = np.vstack(all_pos)
                            conn = np.vstack(all_conn)
                            self.contours.set_data(
                                pos=pos,
                                connect=conn,
                                color=(0.05, 0.05, 0.05, 1.0),
                                width=1.0,
                            )
                        else:
                            self.contours.set_data(
                                pos=np.zeros((0, 2)), connect=None
                            )
        # Dashes (line segments)
        init_segs = build_dash_segments_for_render(state.theta)
        self.dashes = scene.visuals.Line(
            pos=init_segs.reshape(-1, 2),
            connect="segments",
            color=(0.25, 0.25, 0.25, 1.0),
            width=1.0,
            parent=view.scene,
            method="gl",
            antialias=True,
        )
        self.dashes.visible = True
        self.show_dashes = True

        # Contours (pos + connect arrays)
        self.contours = scene.visuals.Line(
            pos=np.zeros((0, 2)),
            color=(0.05, 0.05, 0.05, 1.0),
            width=1.0,
            parent=view.scene,
            method="gl",
            antialias=True,
        )
        self.contours.visible = True

        # Keyboard events
        self.canvas.events.key_press.connect(self.on_key_press)

        # Contour buffer for persistence
        self.init_contour_buffer(length=15)  # default

        # Animation timer
        self.timer = app.Timer(interval=0.03, connect=self.update, start=True)

# =========================
# Contour buffer handling
# =========================
                connect=conn,
                color=(0.05, 0.05, 0.05, 1.0),
                width=1.0,
            )
        else:
            # nothing to draw
            self.contours.set_data(
                pos=np.zeros((0, 2)), connect=None
            )

# =========================

# Main entry

# =========================

if __name__ == "__main__":
    import sys

    appQt = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    appQt.exec_()