# genesis_grid_large.py
#
# Large-scale emergence visualization. N=200 grid with subsampled dash
# rendering — only every Kth cell draws a dash, so matplotlib doesn't
# choke on 40,000 line segments. Contours update every 5th frame.
# Physics runs at full resolution.

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

N = 200
SUBSAMPLE = 3          # render every 3rd cell (200/3 ≈ 67x67 dashes instead of 200x200)
CONTOUR_INTERVAL = 5   # redraw contours every 5th frame

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

click_radius = 5

# =====================================================
# Subsample grid for dash rendering
# =====================================================

X_full = to_cpu(state.X)
Y_full = to_cpu(state.Y)

# Indices of cells we actually draw
sub_i = np.arange(0, N, SUBSAMPLE)
sub_j = np.arange(0, N, SUBSAMPLE)
sub_ii, sub_jj = np.meshgrid(sub_i, sub_j)
sub_mask_i = sub_ii.ravel()
sub_mask_j = sub_jj.ravel()
n_dashes = len(sub_mask_i)

dash_len = 0.45 * SUBSAMPLE  # scale dash length to subsample spacing

# =====================================================
# Main figure
# =====================================================

fig, ax = plt.subplots(figsize=(9, 9))
plt.subplots_adjust(bottom=0.28)

# Background: phase-well heatmap (rendered as imshow at full resolution — fast)
bg_phase = ax.imshow(
    np.zeros((N, N)),
    origin="lower",
    extent=(0, N, 0, N),
    cmap="tab10",
    alpha=0.15,
    vmin=0, vmax=4,
    interpolation="nearest",
)

# Background: compression heatmap
bg_comp = ax.imshow(
    np.zeros((N, N)),
    origin="lower",
    extent=(0, N, 0, N),
    cmap="Greys",
    alpha=0.3,
    vmin=0.0, vmax=1.0,
    interpolation="bilinear",
)

# Subsampled dashes
theta_cpu = to_cpu(state.theta)
sub_x = X_full[sub_mask_i, sub_mask_j]
sub_y = Y_full[sub_mask_i, sub_mask_j]
sub_th = theta_cpu[sub_mask_i, sub_mask_j]

positions = np.c_[sub_x, sub_y]
vecs0 = np.c_[np.cos(sub_th), np.sin(sub_th)]
vecs0 /= np.linalg.norm(vecs0, axis=1, keepdims=True) + 1e-8

p0 = positions - 0.5 * dash_len * vecs0
p1 = positions + 0.5 * dash_len * vecs0
segments0 = np.stack([p0, p1], axis=1)

dashes = LineCollection(segments0, linewidths=0.6)
ax.add_collection(dashes)

indices0 = ((sub_th + 0.25 * np.pi) // (0.5 * np.pi)).astype(int) % 4
dashes.set_color(cm.tab10(indices0 / 4.0))

contours = None

ax.set_aspect("equal")
ax.set_xlim(0, N)
ax.set_ylim(0, N)
ax.set_xticks([])
ax.set_yticks([])
ax.set_title(f"Genesis Grid — N={N} (large scale)\nDashes subsampled {SUBSAMPLE}x, contours on smoothed theta")

# =====================================================
# Second figure — diagnostics at full resolution
# =====================================================

fig2, (ax_u, ax_c) = plt.subplots(1, 2, figsize=(8, 3.5))
fig2.suptitle(f"Genesis Diagnostic Fields (N={N})")

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

ax_calpha = fig.add_axes([0.15, 0.21, 0.7, 0.02])
ax_alpha  = fig.add_axes([0.15, 0.17, 0.7, 0.02])
ax_gamma  = fig.add_axes([0.15, 0.13, 0.7, 0.02])
ax_kappa  = fig.add_axes([0.15, 0.09, 0.7, 0.02])
ax_well   = fig.add_axes([0.15, 0.05, 0.7, 0.02])
ax_lock   = fig.add_axes([0.15, 0.01, 0.7, 0.02])

slider_calpha = Slider(ax_calpha, "Contour",   0.0, 1.0,  valinit=0.7)
slider_alpha  = Slider(ax_alpha,  "Align",     0.0, 1.0,  valinit=params.alpha)
slider_gamma  = Slider(ax_gamma,  "Tension",   0.0, 1.5,  valinit=params.gamma)
slider_kappa  = Slider(ax_kappa,  "Geometry",  0.0, 0.1,  valinit=params.kappa)
slider_well   = Slider(ax_well,   "Phase",     0.0, 2.0,  valinit=params.phase)
slider_lock   = Slider(ax_lock,   "Lock",      0.0, 1.0,  valinit=params.lock_strength)

# =====================================================
# Mouse interaction
# =====================================================

def on_click(event):
    if event.inaxes != ax:
        return
    if event.xdata is None or event.ydata is None:
        return

    ci = int(round(event.ydata))
    cj = int(round(event.xdata))

    if 0 <= ci < N and 0 <= cj < N:
        for a in range(-click_radius, click_radius + 1):
            for b in range(-click_radius, click_radius + 1):
                ii, jj = ci + a, cj + b
                if 0 <= ii < N and 0 <= jj < N:
                    state.theta[ii, jj] += np.pi * (np.random.rand() - 0.5)

fig.canvas.mpl_connect("button_press_event", on_click)

# =====================================================
# Animation
# =====================================================

_frame_count = 0

def animate(frame):
    global contours, _frame_count
    _frame_count += 1

    # Sliders
    params.alpha = slider_alpha.val
    params.gamma = slider_gamma.val
    params.kappa = slider_kappa.val
    params.phase = slider_well.val
    params.lock_strength = slider_lock.val

    # Engine step
    step(state, params, RULES, post=rules_locking.locking_postprocess)

    # Pull to CPU
    theta_cpu = to_cpu(state.theta)
    ux_cpu = to_cpu(state.ux)
    uy_cpu = to_cpu(state.uy)
    C_cpu = to_cpu(state.C)

    # Phase-well background (full res, but imshow is fast)
    phase_idx = ((theta_cpu + 0.25 * np.pi) // (0.5 * np.pi)).astype(int) % 4
    bg_phase.set_data(phase_idx)

    # Compression background
    bg_comp.set_data(C_cpu)

    # Subsampled dashes
    sub_th = theta_cpu[sub_mask_i, sub_mask_j]
    sub_ux = ux_cpu[sub_mask_i, sub_mask_j]
    sub_uy = uy_cpu[sub_mask_i, sub_mask_j]

    sx = X_full[sub_mask_i, sub_mask_j] + sub_ux
    sy = Y_full[sub_mask_i, sub_mask_j] + sub_uy

    vecs = np.c_[np.cos(sub_th), np.sin(sub_th)]
    vecs /= np.linalg.norm(vecs, axis=1, keepdims=True) + 1e-8

    pos = np.c_[sx, sy]
    p0 = pos - 0.5 * dash_len * vecs
    p1 = pos + 0.5 * dash_len * vecs
    dashes.set_segments(np.stack([p0, p1], axis=1))

    sub_idx = ((sub_th + 0.25 * np.pi) // (0.5 * np.pi)).astype(int) % 4
    dashes.set_color(cm.tab10(sub_idx / 4.0))

    # Contours every Nth frame
    if _frame_count % CONTOUR_INTERVAL == 0:
        if contours is not None:
            contours.remove()
            contours = None

        calpha = slider_calpha.val
        if calpha > 0.01:
            theta_smooth = gaussian_filter(theta_cpu, sigma=2.0)
            contours = ax.contour(
                X_full + ux_cpu, Y_full + uy_cpu, theta_smooth,
                levels=6,
                linewidths=0.5,
                colors='black', alpha=calpha)

    # Diagnostics
    ex = np.cos(theta_cpu)
    ey = np.sin(theta_cpu)
    ex_avg = (ex + np.roll(ex, 1, 0) + np.roll(ex, -1, 0)
              + np.roll(ex, 1, 1) + np.roll(ex, -1, 1)) / 5.0
    ey_avg = (ey + np.roll(ey, 1, 0) + np.roll(ey, -1, 0)
              + np.roll(ey, 1, 1) + np.roll(ey, -1, 1)) / 5.0
    unity = np.sqrt(ex_avg ** 2 + ey_avg ** 2)

    im_unity.set_data(unity)
    im_comp.set_data(C_cpu)

    return dashes, bg_comp, bg_phase, im_unity, im_comp


anim = FuncAnimation(fig, animate, interval=50, blit=False, cache_frame_data=False)

if __name__ == "__main__":
    plt.show()
