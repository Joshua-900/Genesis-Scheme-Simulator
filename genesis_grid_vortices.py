# genesis_grid_vortices.py
#
# Vortex visualization — same engine and physics, with topological defect
# detection overlaid. Vortices are the "knotted forces" — points where
# theta winds by 2pi and cannot be smoothed away by local rules.
#
# Red dots = +1 vortices (counterclockwise winding)
# Blue dots = -1 vortices (clockwise winding)
# The vortex count over time is tracked in the diagnostics panel.

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
    rules_locking, diagnostics,
)
from src.genesis_grid.backend import to_cpu

# =====================================================
# Setup
# =====================================================

N = 100
SUBSAMPLE = 2
CONTOUR_INTERVAL = 4

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

click_radius = 4

# Vortex tracking history
vortex_history = []
MAX_HISTORY = 500

# =====================================================
# Subsample grid
# =====================================================

X_full = to_cpu(state.X)
Y_full = to_cpu(state.Y)

sub_i = np.arange(0, N, SUBSAMPLE)
sub_j = np.arange(0, N, SUBSAMPLE)
sub_ii, sub_jj = np.meshgrid(sub_i, sub_j)
sub_mask_i = sub_ii.ravel()
sub_mask_j = sub_jj.ravel()

dash_len = 0.45 * SUBSAMPLE

# =====================================================
# Main figure
# =====================================================

fig, ax = plt.subplots(figsize=(9, 9))
plt.subplots_adjust(bottom=0.28)

# Compression background
bg_comp = ax.imshow(
    np.zeros((N, N)),
    origin="lower", extent=(0, N, 0, N),
    cmap="Greys", alpha=0.2, vmin=0.0, vmax=1.0,
    interpolation="bilinear",
)

# Subsampled dashes
theta_cpu = to_cpu(state.theta)
sub_th = theta_cpu[sub_mask_i, sub_mask_j]
positions = np.c_[X_full[sub_mask_i, sub_mask_j], Y_full[sub_mask_i, sub_mask_j]]
vecs0 = np.c_[np.cos(sub_th), np.sin(sub_th)]
vecs0 /= np.linalg.norm(vecs0, axis=1, keepdims=True) + 1e-8

p0 = positions - 0.5 * dash_len * vecs0
p1 = positions + 0.5 * dash_len * vecs0
dashes = LineCollection(np.stack([p0, p1], axis=1), linewidths=0.5, alpha=0.6)
ax.add_collection(dashes)
dashes.set_color(cm.tab10(((sub_th + 0.25*np.pi) // (0.5*np.pi)).astype(int) % 4 / 4.0))

# Vortex scatter plots (will be updated each frame)
scatter_plus = ax.scatter([], [], c='red', s=30, marker='o', zorder=5, label='+1 vortex')
scatter_minus = ax.scatter([], [], c='blue', s=30, marker='o', zorder=5, label='-1 vortex')

contours = None

ax.set_aspect("equal")
ax.set_xlim(0, N)
ax.set_ylim(0, N)
ax.set_xticks([])
ax.set_yticks([])
ax.legend(loc='upper right', fontsize=8, framealpha=0.8)
ax.set_title(f"Genesis Grid — Topological Defects (N={N})\nRed = +1 vortex, Blue = -1 vortex")

# =====================================================
# Second figure — vortex count over time + diagnostics
# =====================================================

fig2, ((ax_count, ax_unity), (ax_winding, ax_comp)) = plt.subplots(2, 2, figsize=(9, 6))
fig2.suptitle("Vortex Diagnostics")

# Vortex count time series
line_plus, = ax_count.plot([], [], 'r-', linewidth=1.5, label='+1')
line_minus, = ax_count.plot([], [], 'b-', linewidth=1.5, label='-1')
line_total, = ax_count.plot([], [], 'k--', linewidth=1, label='total')
ax_count.set_xlim(0, MAX_HISTORY)
ax_count.set_ylim(0, 200)
ax_count.set_xlabel("Frame")
ax_count.set_ylabel("Count")
ax_count.set_title("Vortex Count Over Time")
ax_count.legend(fontsize=8)

# Unity field
im_unity = ax_unity.imshow(np.zeros((N, N)), vmin=0.0, vmax=1.0,
                            cmap="viridis", origin="lower")
ax_unity.set_title("Unity (local coherence)")
ax_unity.set_xticks([]); ax_unity.set_yticks([])

# Winding number field
im_winding = ax_winding.imshow(np.zeros((N, N)), vmin=-1, vmax=1,
                                cmap="RdBu_r", origin="lower")
ax_winding.set_title("Winding Number Field")
ax_winding.set_xticks([]); ax_winding.set_yticks([])

# Compression field
im_comp = ax_comp.imshow(np.zeros((N, N)), vmin=0.0, vmax=1.0,
                          cmap="inferno", origin="lower")
ax_comp.set_title("Compression C(i,j)")
ax_comp.set_xticks([]); ax_comp.set_yticks([])

fig2.tight_layout()

# =====================================================
# Sliders
# =====================================================

ax_alpha  = fig.add_axes([0.15, 0.20, 0.7, 0.02])
ax_gamma  = fig.add_axes([0.15, 0.16, 0.7, 0.02])
ax_well   = fig.add_axes([0.15, 0.12, 0.7, 0.02])
ax_lock   = fig.add_axes([0.15, 0.08, 0.7, 0.02])
ax_calpha = fig.add_axes([0.15, 0.04, 0.7, 0.02])
ax_vsize  = fig.add_axes([0.15, 0.00, 0.7, 0.02])

slider_alpha  = Slider(ax_alpha,  "Align",    0.0, 1.0,  valinit=params.alpha)
slider_gamma  = Slider(ax_gamma,  "Tension",  0.0, 1.5,  valinit=params.gamma)
slider_well   = Slider(ax_well,   "Phase",    0.0, 2.0,  valinit=params.phase)
slider_lock   = Slider(ax_lock,   "Lock",     0.0, 1.0,  valinit=params.lock_strength)
slider_calpha = Slider(ax_calpha, "Contour",  0.0, 1.0,  valinit=0.4)
slider_vsize  = Slider(ax_vsize,  "Vortex sz", 5, 120, valinit=30, valstep=5)

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
    params.phase = slider_well.val
    params.lock_strength = slider_lock.val

    # Engine step
    step(state, params, RULES, post=rules_locking.locking_postprocess)

    # Pull to CPU
    theta_cpu = to_cpu(state.theta)
    ux_cpu = to_cpu(state.ux)
    uy_cpu = to_cpu(state.uy)
    C_cpu = to_cpu(state.C)

    # --- Detect vortices ---
    vp, vm, winding = diagnostics.detect_vortices(state)

    # Track counts
    vortex_history.append((len(vp), len(vm)))
    if len(vortex_history) > MAX_HISTORY:
        vortex_history.pop(0)

    # --- Update main figure ---
    bg_comp.set_data(C_cpu)

    # Dashes
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

    # Vortex markers (on deformed grid)
    vs = slider_vsize.val
    if vp:
        vp_arr = np.array(vp)
        vp_rows = np.clip(vp_arr[:, 0].astype(int), 0, N-1)
        vp_cols = np.clip(vp_arr[:, 1].astype(int), 0, N-1)
        vp_x = vp_arr[:, 1] + ux_cpu[vp_rows, vp_cols]
        vp_y = vp_arr[:, 0] + uy_cpu[vp_rows, vp_cols]
        scatter_plus.set_offsets(np.c_[vp_x, vp_y])
    else:
        scatter_plus.set_offsets(np.empty((0, 2)))
    scatter_plus.set_sizes([vs])

    if vm:
        vm_arr = np.array(vm)
        vm_rows = np.clip(vm_arr[:, 0].astype(int), 0, N-1)
        vm_cols = np.clip(vm_arr[:, 1].astype(int), 0, N-1)
        vm_x = vm_arr[:, 1] + ux_cpu[vm_rows, vm_cols]
        vm_y = vm_arr[:, 0] + uy_cpu[vm_rows, vm_cols]
        scatter_minus.set_offsets(np.c_[vm_x, vm_y])
    else:
        scatter_minus.set_offsets(np.empty((0, 2)))
    scatter_minus.set_sizes([vs])

    # Contours
    if _frame_count % CONTOUR_INTERVAL == 0:
        if contours is not None:
            contours.remove()
            contours = None

        calpha = slider_calpha.val
        if calpha > 0.01:
            theta_smooth = gaussian_filter(theta_cpu, sigma=1.5)
            contours = ax.contour(
                X_full + ux_cpu, Y_full + uy_cpu, theta_smooth,
                levels=6, linewidths=0.4,
                colors='black', alpha=calpha)

    ax.set_title(
        f"Genesis Grid — Topological Defects (N={N})\n"
        f"+1: {len(vp)}  |  -1: {len(vm)}  |  total: {len(vp)+len(vm)}  |  frame: {_frame_count}"
    )

    # --- Update diagnostics figure ---
    # Vortex count time series
    hist = np.array(vortex_history)
    x_hist = np.arange(len(hist))
    line_plus.set_data(x_hist, hist[:, 0])
    line_minus.set_data(x_hist, hist[:, 1])
    line_total.set_data(x_hist, hist[:, 0] + hist[:, 1])
    ax_count.set_xlim(0, max(len(hist), 50))
    ax_count.set_ylim(0, max(hist[:, 0].max() + 10, 50))

    # Unity
    unity = diagnostics.compute_unity(state)
    im_unity.set_data(unity)

    # Winding number
    im_winding.set_data(winding)

    # Compression
    im_comp.set_data(C_cpu)

    return dashes, bg_comp, scatter_plus, scatter_minus, im_unity, im_winding, im_comp


anim = FuncAnimation(fig, animate, interval=50, blit=False, cache_frame_data=False)

if __name__ == "__main__":
    plt.show()
