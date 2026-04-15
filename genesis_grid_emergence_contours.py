# genesis_grid_emergence_contours.py
#
# Same engine and physics as genesis_grid_emergence.py, but with lightweight
# contour overlay for the "pretty" look. Contours are drawn on the compression
# field (smooth, few levels) instead of theta (noisy, dense).
# Updated every 3rd frame to keep rendering fast.

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from matplotlib.widgets import Slider
from matplotlib import cm
from matplotlib.collections import LineCollection
from scipy.ndimage import gaussian_filter

from src.genesis_grid import (
    GenesisState, GenesisParams, step,
    rules_alignment, rules_compression,
    rules_phase, rules_dipoles, rules_triads, rules_curvature,
    rules_locking,
)
from src.genesis_grid.backend import to_cpu

# =====================================================
# Setup
# =====================================================

N = 60
state = GenesisState(N, dt=0.05)
params = GenesisParams()

params.alpha   = 0.3
params.gamma   = 0.015
params.kappa   = 0.015
params.phase   = 0.6
params.dipole  = 0.3
params.triads  = 0.8
params.curv    = 0.4

params.decay_tau  = 0.02
params.geom_decay = 0.05
params.sigma_c2   = 0.25 ** 2
params.tri_sigma2 = 0.8 ** 2

params.lock_strength   = 0.75
params.phase_lock_gain = 2.5
params.tri_lock_gain   = 3.0
params.shell_geom_gain = 0.08

RULES = [
    rules_alignment.alignment_rule,
    rules_compression.compression_rule,
    rules_phase.phase_rule,
    rules_dipoles.dipole_rule,
    rules_triads.triad_rule,
    rules_curvature.curvature_rule,
]

click_radius = 3

# =====================================================
# Main figure
# =====================================================

fig, ax = plt.subplots()
plt.subplots_adjust(bottom=0.35)

X_grid = to_cpu(state.X)
Y_grid = to_cpu(state.Y)
theta_cpu = to_cpu(state.theta)

# Background: compression heatmap
bg_comp = ax.imshow(
    np.zeros((N, N)),
    origin="lower",
    extent=(-1, N + 1, -1, N + 1),
    cmap="Greys",
    alpha=0.2,
    vmin=0.0, vmax=1.0,
    interpolation="gaussian",
)

# Symmetric dashes
positions = np.c_[X_grid.ravel(), Y_grid.ravel()]
U0 = np.cos(theta_cpu).ravel()
V0 = np.sin(theta_cpu).ravel()
vecs0 = np.c_[U0, V0]
vecs0 /= np.linalg.norm(vecs0, axis=1, keepdims=True) + 1e-8
dash_len = 0.55

p0 = positions - 0.5 * dash_len * vecs0
p1 = positions + 0.5 * dash_len * vecs0
segments0 = np.stack([p0, p1], axis=1)

dashes = LineCollection(segments0, linewidths=0.7)
ax.add_collection(dashes)

indices0 = ((theta_cpu + 0.25 * np.pi) // (0.5 * np.pi)).astype(int) % 4
dashes.set_color(cm.tab10(indices0.ravel() / 4.0))

# Initial contours (on smoothed compression — will be replaced each update)
contours = None

ax.set_aspect("equal")
ax.set_xlim(-1, N + 1)
ax.set_ylim(-1, N + 1)
ax.set_xticks([])
ax.set_yticks([])
ax.set_title(
    "Genesis Grid Engine — Contour Variant\n"
    "Dashes = orientation, contours = smoothed compression, color = phase well"
)

# =====================================================
# Second figure — diagnostics
# =====================================================

fig2, (ax_u, ax_c) = plt.subplots(1, 2, figsize=(7, 3))
fig2.suptitle("Genesis Diagnostic Fields")

im_unity = ax_u.imshow(np.zeros((N, N)), vmin=0.0, vmax=1.0,
                        cmap="viridis", origin="lower")
ax_u.set_title("Unity U(i,j)")
ax_u.set_xticks([]); ax_u.set_yticks([])

im_comp = ax_c.imshow(np.zeros((N, N)), vmin=0.0, vmax=1.0,
                       cmap="inferno", origin="lower")
ax_c.set_title("Compression C(i,j)")
ax_c.set_xticks([]); ax_c.set_yticks([])

fig2.colorbar(im_unity, ax=ax_u, fraction=0.046, pad=0.04)
fig2.colorbar(im_comp, ax=ax_c, fraction=0.046, pad=0.04)

# =====================================================
# Sliders
# =====================================================

ax_calpha = fig.add_axes([0.15, 0.27, 0.7, 0.03])
ax_alpha  = fig.add_axes([0.15, 0.22, 0.7, 0.03])
ax_gamma  = fig.add_axes([0.15, 0.17, 0.7, 0.03])
ax_kappa  = fig.add_axes([0.15, 0.12, 0.7, 0.03])
ax_well   = fig.add_axes([0.15, 0.07, 0.7, 0.03])
ax_dipole = fig.add_axes([0.15, 0.02, 0.7, 0.03])
ax_lock   = fig.add_axes([0.15, -0.03, 0.7, 0.03])

slider_calpha = Slider(ax_calpha, "Contour \u03b1",  0.0, 1.0,  valinit=0.8)
slider_alpha  = Slider(ax_alpha,  "\u03b1 Align",    0.0, 1.0,  valinit=params.alpha)
slider_gamma  = Slider(ax_gamma,  "\u03b3 Tension",  0.0, 1.5,  valinit=params.gamma)
slider_kappa  = Slider(ax_kappa,  "\u03ba Geometry", 0.0, 0.1,  valinit=params.kappa)
slider_well   = Slider(ax_well,   "Phase",           0.0, 2.0,  valinit=params.phase)
slider_dipole = Slider(ax_dipole, "Dipole",          0.0, 2.0,  valinit=params.dipole)
slider_lock   = Slider(ax_lock,   "Lock",            0.0, 1.0,  valinit=params.lock_strength)

# =====================================================
# Mouse interaction
# =====================================================

def on_click(event):
    if event.inaxes != ax:
        return
    if event.xdata is None or event.ydata is None:
        return

    i = int(round(event.ydata))
    j = int(round(event.xdata))

    if 0 <= i < N and 0 <= j < N:
        for a in range(-click_radius, click_radius + 1):
            for b in range(-click_radius, click_radius + 1):
                ii, jj = i + a, j + b
                if 0 <= ii < N and 0 <= jj < N:
                    state.theta[ii, jj] += np.pi * (np.random.rand() - 0.5)

fig.canvas.mpl_connect("button_press_event", on_click)

# =====================================================
# Animation loop
# =====================================================

_frame_count = 0
_CONTOUR_INTERVAL = 3  # redraw contours every Nth frame

def animate(frame):
    global contours, _frame_count
    _frame_count += 1

    # Read sliders
    params.alpha  = slider_alpha.val
    params.gamma  = slider_gamma.val
    params.kappa  = slider_kappa.val
    params.phase  = slider_well.val
    params.dipole = slider_dipole.val
    params.lock_strength = slider_lock.val

    # Engine step
    step(state, params, RULES, post=rules_locking.locking_postprocess)

    # Pull to CPU
    theta_cpu = to_cpu(state.theta)
    ux_cpu = to_cpu(state.ux)
    uy_cpu = to_cpu(state.uy)
    C_cpu = to_cpu(state.C)

    # Update compression background
    bg_comp.set_data(C_cpu)

    # Update dashes
    Udir = np.cos(theta_cpu).ravel()
    Vdir = np.sin(theta_cpu).ravel()
    vecs = np.c_[Udir, Vdir]
    vecs /= np.linalg.norm(vecs, axis=1, keepdims=True) + 1e-8

    new_pos = np.c_[(X_grid + ux_cpu).ravel(), (Y_grid + uy_cpu).ravel()]
    p0 = new_pos - 0.5 * dash_len * vecs
    p1 = new_pos + 0.5 * dash_len * vecs
    dashes.set_segments(np.stack([p0, p1], axis=1))

    indices = ((theta_cpu + 0.25 * np.pi) // (0.5 * np.pi)).astype(int) % 4
    dashes.set_color(cm.tab10(indices.ravel() / 4.0))

    # Update contours every Nth frame (lightweight: smoothed C, few levels)
    if _frame_count % _CONTOUR_INTERVAL == 0:
        # Remove old contours
        if contours is not None:
            contours.remove()

        # Smooth the compression field to get large-scale shell boundaries
        # Contour on smoothed C for large-scale shells
        C_smooth = gaussian_filter(C_cpu, sigma=1.5)

        # Also contour theta on the deformed grid for domain boundaries
        theta_smooth = gaussian_filter(theta_cpu, sigma=0.8)

        calpha = slider_calpha.val
        if calpha > 0.01:
            contours = ax.contour(
                X_grid + ux_cpu, Y_grid + uy_cpu, theta_smooth,
                levels=6,
                linewidths=0.8,
                colors='black', alpha=calpha)
        else:
            contours = None

    # Update diagnostics
    ex = np.cos(theta_cpu)
    ey = np.sin(theta_cpu)
    ex_avg = (ex + np.roll(ex, 1, 0) + np.roll(ex, -1, 0)
              + np.roll(ex, 1, 1) + np.roll(ex, -1, 1)) / 5.0
    ey_avg = (ey + np.roll(ey, 1, 0) + np.roll(ey, -1, 0)
              + np.roll(ey, 1, 1) + np.roll(ey, -1, 1)) / 5.0
    unity = np.sqrt(ex_avg ** 2 + ey_avg ** 2)

    im_unity.set_data(unity)
    im_comp.set_data(C_cpu)

    return dashes, bg_comp, im_unity, im_comp


anim = FuncAnimation(fig, animate, interval=40, blit=False, cache_frame_data=False)

if __name__ == "__main__":
    plt.show()
