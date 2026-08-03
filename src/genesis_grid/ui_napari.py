"""
Genesis grid viewer — napari edition.

Same simulation, rendered the napari way:
  * compression field C  -> Image layer
  * orientation theta    -> Image layer with cyclic HSV colormap
  * orientation dashes   -> Vectors layer
  * raw state capture    -> theta and C saved to NPZ on demand

Run from the `src` directory:
    python -m genesis_grid.ui_napari
"""

from datetime import datetime
from pathlib import Path

import numpy as np
import napari
from magicgui.widgets import Container, FloatSlider, PushButton
from qtpy.QtCore import QTimer

from .backend import to_cpu
from .core import GenesisState, GenesisParams, step
from .collector import RawStateCollector
from . import rules_alignment
from . import rules_phase
from . import rules_dipoles
from . import rules_triads
from . import rules_curvature
from . import rules_compression
from . import relax


# =========================
# Config
# =========================
N = 256
DT = 0.05
DASH_LEN = 0.45
RENDER_SUBSAMPLE = 4
INTERVAL_MS = 100

CAPTURE_EVERY = 1
CAPTURE_MAX_FRAMES = 5000
CAPTURE_FIELDS = ("theta", "C")


# =========================
# Init state, params, rules
# =========================
state = GenesisState(N, DT)
params = GenesisParams()

collector = RawStateCollector(
    every=CAPTURE_EVERY,
    max_frames=CAPTURE_MAX_FRAMES,
    fields=CAPTURE_FIELDS,
)

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
    Build a napari Vectors array from a block-averaged theta field.

    napari Vectors use shape (M, 2, 2):
      [:, 0] = origin (row, col)
      [:, 1] = projection (drow, dcol)
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

    cy = ys * scale + 0.5 * (scale - 1.0)
    cx = xs * scale + 0.5 * (scale - 1.0)

    length = DASH_LEN * scale
    drow = np.sin(ang) * length
    dcol = np.cos(ang) * length

    starts = np.stack(
        [
            (cy - 0.5 * drow).ravel(),
            (cx - 0.5 * dcol).ravel(),
        ],
        axis=1,
    )
    dirs = np.stack(
        [
            drow.ravel(),
            dcol.ravel(),
        ],
        axis=1,
    )

    return np.stack([starts, dirs], axis=1).astype(np.float32)


# =========================
# Topological structure
# =========================
def _wrap(x):
    """Wrap angle differences into (-pi, pi]."""
    return (x + np.pi) % (2.0 * np.pi) - np.pi


def defect_charges(theta):
    """
    Compute winding number on every elementary plaquette.

    Returns an (N, N) integer array:
      +1 = vortex
      -1 = antivortex
       0 = no defect
    """
    th = to_cpu(theta)

    a = th
    b = np.roll(th, -1, axis=1)
    c = np.roll(np.roll(th, -1, axis=0), -1, axis=1)
    d = np.roll(th, -1, axis=0)

    loop = (
        _wrap(b - a)
        + _wrap(c - b)
        + _wrap(d - c)
        + _wrap(a - d)
    )

    return np.rint(loop / (2.0 * np.pi)).astype(np.int32)


def defect_points(theta):
    """
    Return positive and negative defect coordinates for napari.

    Returns:
      pos_coords, neg_coords, defect_count, net_charge
    """
    charge = defect_charges(theta)
    ii, jj = np.nonzero(charge)
    q = charge[ii, jj]

    coords = np.stack(
        [
            ii + 0.5,
            jj + 0.5,
        ],
        axis=1,
    ).astype(np.float32)

    pos = q > 0
    pos_coords = coords[pos]
    neg_coords = coords[~pos]

    return (
        pos_coords,
        neg_coords,
        int(q.shape[0]),
        int(q.sum()),
    )


# =========================
# Build viewer
# =========================
def main():
    viewer = napari.Viewer(title="Genesis Dash Grid — napari")

    theta0 = to_cpu(state.theta)
    C0 = to_cpu(state.C)

    theta_layer = viewer.add_image(
        theta0,
        name="orientation θ",
        colormap="hsv",
        contrast_limits=(0.0, 2.0 * np.pi),
        interpolation2d="linear",
        opacity=0.6,
    )

    c_layer = viewer.add_image(
        C0,
        name="compression C",
        colormap="inferno",
        contrast_limits=(0.0, 1.0),
        interpolation2d="linear",
        opacity=0.85,
        blending="additive",
    )

    accum = {
        "C": np.zeros((N, N), dtype=np.float64),
        "beta": 0.05,
    }

    c_avg_layer = viewer.add_image(
        accum["C"],
        name="C (time-avg)",
        colormap="viridis",
        contrast_limits=(0.0, 1.0),
        interpolation2d="linear",
        opacity=0.9,
        visible=True,
    )

    dash_layer = viewer.add_vectors(
        build_dash_vectors(state.theta),
        name="dashes",
        edge_width=0.4,
        edge_color="white",
        length=1.0,
        vector_style="line",
        opacity=0.9,
    )

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

    viewer.text_overlay.visible = True
    viewer.text_overlay.font_size = 12

    frame_counter = 0
    running = {"on": True}

    def set_readout(count, net):
        viewer.text_overlay.text = (
            f"frame: {frame_counter}   "
            f"captured: {len(collector.steps)}/{CAPTURE_MAX_FRAMES}   "
            f"defects: {count}   net charge: {net:+d}   "
            f"(red +1 vortex, cyan -1 antivortex)"
        )

    set_readout(d_count, d_net)

    # -------------------------
    # Controls
    # -------------------------
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
        init = min(hi, max(lo, float(getattr(params, attr))))
        widget = FloatSlider(
            name=attr,
            label=attr,
            min=lo,
            max=hi,
            value=init,
        )
        widget.changed.connect(
            lambda value, attr_name=attr: setattr(params, attr_name, value)
        )
        sliders.append(widget)

    play_btn = PushButton(text="Pause")

    def toggle():
        running["on"] = not running["on"]
        play_btn.text = "Play" if not running["on"] else "Pause"

    play_btn.changed.connect(toggle)

    avg_slider = FloatSlider(
        name="avg_beta",
        label="C avg memory (beta)",
        min=0.005,
        max=0.30,
        value=accum["beta"],
    )
    avg_slider.changed.connect(
        lambda value: accum.__setitem__("beta", value)
    )

    reset_avg_btn = PushButton(text="Reset C avg")
    reset_avg_btn.changed.connect(
        lambda: accum["C"].fill(0.0)
    )

    save_btn = PushButton(text="Save Raw Data")

    def save_capture():
        if not collector.steps:
            print("No captured frames to save.")
            return

        project_root = Path(__file__).resolve().parents[2]
        results_dir = project_root / "results"
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = results_dir / f"napari_capture_{timestamp}.npz"

        collector.save(
            output_path,
            metadata={
                "N": N,
                "dt": DT,
                "interval_ms": INTERVAL_MS,
                "capture_every": CAPTURE_EVERY,
                "capture_max_frames": CAPTURE_MAX_FRAMES,
                "capture_fields": CAPTURE_FIELDS,
                "frames_simulated": frame_counter,
                "frames_captured": len(collector.steps),
                "params": vars(params).copy(),
            },
        )

        print(f"Saved raw capture to: {output_path.resolve()}")

    save_btn.changed.connect(save_capture)

    controls = Container(
        widgets=[
            *sliders,
            avg_slider,
            play_btn,
            reset_avg_btn,
            save_btn,
        ],
        labels=True,
    )

    viewer.window.add_dock_widget(
        controls,
        area="right",
        name="Genesis params",
    )

    # -------------------------
    # Animation loop
    # -------------------------
    def tick():
        nonlocal frame_counter

        if not running["on"]:
            return

        step(state, params, rules)

        frame_counter += 1
        collector.capture(frame_counter, state)

        theta_now = to_cpu(state.theta)
        C_now = to_cpu(state.C)

        theta_layer.data = theta_now
        c_layer.data = C_now
        dash_layer.data = build_dash_vectors(state.theta)

        beta = accum["beta"]
        accum["C"] *= 1.0 - beta
        accum["C"] += beta * C_now
        c_avg_layer.data = accum["C"]

        hi = float(accum["C"].max())
        c_avg_layer.contrast_limits = (
            0.0,
            hi if hi > 1e-6 else 1e-6,
        )

        pos_coords, neg_coords, d_count, d_net = defect_points(state.theta)
        vortex_layer.data = pos_coords
        antivortex_layer.data = neg_coords
        set_readout(d_count, d_net)

    timer = QTimer()
    timer.setInterval(INTERVAL_MS)
    timer.timeout.connect(tick)
    timer.start()

    viewer._genesis_timer = timer

    napari.run()


if __name__ == "__main__":
    main()
