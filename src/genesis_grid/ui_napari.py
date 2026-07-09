"""
Genesis grid viewer — napari edition (for comparison with ui_vispy3.py).

Same simulation, rendered the napari way:
  * compression field C  -> Image layer (colormap texture, GPU) — replaces the
    hand-rolled marching-squares contours from the vispy version.
  * orientation theta    -> Image layer with a cyclic 'hsv' colormap (angle->hue).
  * orientation dashes   -> Vectors layer (subsampled director field).

Controls are a magicgui dock widget instead of manual QSlider plumbing.

Run from the `src` directory:
    python -m genesis_grid.ui_napari
"""

from .backend import xp, to_cpu
from .core import GenesisState, GenesisParams, step
from . import rules_alignment
from . import rules_phase
from . import rules_dipoles
from . import rules_triads
from . import rules_curvature
from . import rules_compression
from . import relax

import numpy as np
import napari
from magicgui.widgets import Container, FloatSlider, PushButton
from qtpy.QtCore import QTimer

# =========================
# Config
# =========================
N = 256
DT = 0.05
DASH_LEN = 0.45
RENDER_SUBSAMPLE = 4
INTERVAL_MS = 30

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
# Dash / vector geometry
# =========================
def build_dash_vectors(theta):
    """
    Build a napari Vectors array from a (block-averaged) theta field.

    napari Vectors want shape (M, 2, 2): [:, 0] = origin (row, col),
    [:, 1] = projection (drow, dcol). We center each dash on its block.
    """
    th = to_cpu(theta)
    ny, nx = th.shape
    f = RENDER_SUBSAMPLE
    fy, fx = ny // f, nx // f
    if fy == 0 or fx == 0:
        f, fy, fx = 1, ny, nx

    if f > 1:
        blocks = th[: fy * f, : fx * f].reshape(fy, f, fx, f)
        u = np.cos(blocks).mean(axis=(1, 3))
        v = np.sin(blocks).mean(axis=(1, 3))
        ang = np.arctan2(v, u)
    else:
        ang = th

    ys, xs = np.mgrid[0:fy, 0:fx]
    scale = float(f)
    cy = ys * scale + 0.5 * (scale - 1.0)  # row = y
    cx = xs * scale + 0.5 * (scale - 1.0)  # col = x

    length = DASH_LEN * scale
    drow = np.sin(ang) * length  # y-component -> row
    dcol = np.cos(ang) * length  # x-component -> col

    # center the dash: start half a vector back from the block center
    starts = np.stack([(cy - 0.5 * drow).ravel(), (cx - 0.5 * dcol).ravel()], axis=1)
    dirs = np.stack([drow.ravel(), dcol.ravel()], axis=1)
    return np.stack([starts, dirs], axis=1).astype(np.float32)


# =========================
# Topological structure: defect detection (winding number)
# =========================
def _wrap(x):
    """Wrap angle differences into (-pi, pi]."""
    return (x + np.pi) % (2.0 * np.pi) - np.pi


def defect_charges(theta):
    """
    Winding number on every elementary plaquette of the theta field.

    Walk the 4 corners of each unit square, sum the wrapped angle
    differences, divide by 2*pi. Result is an integer per plaquette:
      +1 = vortex, -1 = antivortex, 0 = smooth (no defect).
    Returns an (N, N) integer array; entry (i, j) is the charge of the
    plaquette whose top-left corner is cell (i, j).
    """
    th = to_cpu(theta)
    a = th                                    # (i,   j)
    b = np.roll(th, -1, axis=1)               # (i,   j+1)
    c = np.roll(np.roll(th, -1, 0), -1, 1)    # (i+1, j+1)
    d = np.roll(th, -1, axis=0)               # (i+1, j)

    loop = _wrap(b - a) + _wrap(c - b) + _wrap(d - c) + _wrap(a - d)
    return np.rint(loop / (2.0 * np.pi)).astype(np.int32)


def defect_points(theta):
    """
    Split defects by sign so each can live in its own constant-color layer.

    Returns (pos_coords, neg_coords, count, net_charge), where coords are
    (M, 2) plaquette-center positions in (row, col) for napari.
    """
    charge = defect_charges(theta)
    ii, jj = np.nonzero(charge)
    q = charge[ii, jj]

    # plaquette center sits half a cell down-right of its top-left corner
    coords = np.stack([ii + 0.5, jj + 0.5], axis=1).astype(np.float32)
    pos = q > 0
    pos_coords = coords[pos]
    neg_coords = coords[~pos]

    return pos_coords, neg_coords, int(q.shape[0]), int(q.sum())


# =========================
# Build the viewer
# =========================
def main():
    viewer = napari.Viewer(title="Genesis Dash Grid — napari")

    theta0 = to_cpu(state.theta)
    C0 = to_cpu(state.C)

    # Orientation field as a cyclic hue image (angle -> hue).
    theta_layer = viewer.add_image(
        theta0,
        name="orientation θ",
        colormap="hsv",
        contrast_limits=(0.0, 2.0 * np.pi),
        interpolation2d="linear",
        opacity=0.6,
    )

    # Compression field C as a colormap texture — the napari replacement
    # for the vispy contour extraction.
    c_layer = viewer.add_image(
        C0,
        name="compression C",
        colormap="inferno",
        contrast_limits=(0.0, 1.0),
        interpolation2d="linear",
        opacity=0.85,
        blending="additive",
    )

    # Time-averaged compression (EMA) — reveals where the fast, flickering
    # C activity actually concentrates. `beta` sets how fast it forgets.
    accum = {"C": np.zeros((N, N), dtype=np.float64), "beta": 0.05}
    c_avg_layer = viewer.add_image(
        accum["C"],
        name="C (time-avg)",
        colormap="viridis",
        contrast_limits=(0.0, 1.0),
        interpolation2d="linear",
        opacity=0.9,
        visible=True,
    )

    # Orientation dashes as a Vectors layer.
    dash_layer = viewer.add_vectors(
        build_dash_vectors(state.theta),
        name="dashes",
        edge_width=0.4,
        edge_color="white",
        length=1.0,
        vector_style="line",
        opacity=0.9,
    )

    # Topological defects (the actual "structure"): winding-number points.
    # Two constant-color layers so per-frame updates only touch .data.
    pos_coords, neg_coords, d_count, d_net = defect_points(state.theta)
    vortex_layer = viewer.add_points(
        pos_coords,
        name="+1 vortex",
        face_color="red",
        border_color="black",
        border_width=0.12,
        size=6,
        symbol="disc",
    )
    antivortex_layer = viewer.add_points(
        neg_coords,
        name="-1 antivortex",
        face_color="cyan",
        border_color="black",
        border_width=0.12,
        size=6,
        symbol="disc",
    )

    # Live readout of the structure count.
    viewer.text_overlay.visible = True
    viewer.text_overlay.font_size = 12

    def set_readout(count, net):
        viewer.text_overlay.text = (
            f"defects: {count}   net charge: {net:+d}   "
            f"(red +1 vortex, cyan -1 antivortex)"
        )

    set_readout(d_count, d_net)

    # ---- controls (magicgui) ----
    slider_specs = [
        ("alpha", 0.0, 11.2),
        ("gamma", 0.0, 11.2),
        ("kappa", 0.0, 11.2),
        ("phase", 0.0, 21.0),
        ("dipole", 0.0, 21.0),
        ("triads", 0.0, 21.5),
        ("curv", 0.0, 21.0),
        ("lock_strength", 0.0, 11.0),
    ]

    sliders = []
    for attr, lo, hi in slider_specs:
        init = min(hi, max(lo, float(getattr(params, attr))))  # clamp to slider range
        w = FloatSlider(name=attr, label=attr, min=lo, max=hi, value=init)
        w.changed.connect(lambda v, a=attr: setattr(params, a, v))
        sliders.append(w)

    running = {"on": True}
    play_btn = PushButton(text="Pause")

    def toggle():
        running["on"] = not running["on"]
        play_btn.text = "Play" if not running["on"] else "Pause"

    play_btn.changed.connect(toggle)

    # time-avg memory: higher beta = shorter memory (forgets faster)
    avg_slider = FloatSlider(name="avg_beta", label="C avg memory (beta)",
                             min=0.005, max=0.30, value=accum["beta"])
    avg_slider.changed.connect(lambda v: accum.__setitem__("beta", v))

    reset_btn = PushButton(text="Reset C avg")
    reset_btn.changed.connect(lambda: accum["C"].fill(0.0))

    controls = Container(
        widgets=[*sliders, avg_slider, play_btn, reset_btn], labels=True
    )
    viewer.window.add_dock_widget(controls, area="right", name="Genesis params")

    # ---- animation loop ----
    def tick():
        if not running["on"]:
            return
        step(state, params, rules)
        C_now = to_cpu(state.C)
        theta_layer.data = to_cpu(state.theta)
        c_layer.data = C_now
        dash_layer.data = build_dash_vectors(state.theta)

        # exponential moving average of C, autoscaled for visibility
        b = accum["beta"]
        accum["C"] *= (1.0 - b)
        accum["C"] += b * C_now
        c_avg_layer.data = accum["C"]
        hi = float(accum["C"].max())
        c_avg_layer.contrast_limits = (0.0, hi if hi > 1e-6 else 1e-6)

        pos_coords, neg_coords, d_count, d_net = defect_points(state.theta)
        vortex_layer.data = pos_coords
        antivortex_layer.data = neg_coords
        set_readout(d_count, d_net)

    timer = QTimer()
    timer.setInterval(INTERVAL_MS)
    timer.timeout.connect(tick)
    timer.start()
    # keep a reference so the timer isn't garbage-collected
    viewer._genesis_timer = timer

    napari.run()


if __name__ == "__main__":
    main()
