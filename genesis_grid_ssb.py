# genesis_grid_ssb.py
#
# Spontaneous symmetry breaking experiment.
#
# Uses the RELATIVE triad rule — depends only on angle differences between
# cells, never on absolute angles. The rules are fully rotationally invariant.
# If discrete domains still emerge, that is genuine spontaneous symmetry
# breaking: the rules don't prefer any orientation, but the state does.
#
#   Alignment         — local coupling (rotationally invariant)
#   Geometry          — orientation drives displacement
#   Curvature         — geometry drives orientation (closes loop)
#   Relative Triads   — distinction principle via RELATIONSHIPS only
#   Locking           — compression at folds
#
# NO phase wells. NO dipoles. NO absolute angle preferences anywhere.
# The question: does the system pick preferred orientations on its own?

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from matplotlib.widgets import Slider
from matplotlib import cm
from matplotlib.collections import LineCollection
from scipy.ndimage import gaussian_filter

from src.genesis_grid import (
    GenesisState, GenesisParams, step,
    rules_alignment, rules_compression, rules_curvature,
    rules_triads_relative,
    rules_locking, diagnostics,
)
from src.genesis_grid.backend import to_cpu

# =====================================================
# Setup — minimal forces only
# =====================================================

N = 100
SUBSAMPLE = 2
CONTOUR_INTERVAL = 4

state = GenesisState(N, dt=0.05)
params = GenesisParams()

# The three non-arbitrary forces
params.alpha   = 0.3      # alignment coupling
params.gamma   = 0.015    # tension gain (drives geometry)
params.kappa   = 0.015    # geometry coupling
params.curv    = 0.4      # curvature feedback

# Zeroed — still testing without these
params.phase   = 0.0      # NO phase wells
params.dipole  = 0.0      # NO dipoles

# The distinction principle — re-enabled
params.triads  = 0.8

# Housekeeping
params.decay_tau  = 0.02
params.geom_decay = 0.05
params.sigma_c2   = 0.25 ** 2
params.tri_sigma2 = 0.8 ** 2

# Locking (emerges from geometry)
params.lock_strength   = 0.75
params.phase_lock_gain = 0.0    # nothing to amplify — no phase wells
params.tri_lock_gain   = 3.0    # amplify triads in compressed cores
params.shell_geom_gain = 0.08

# Rotationally invariant rule pipeline — no absolute angle preferences
RULES = [
    rules_alignment.alignment_rule,
    rules_compression.compression_rule,
    rules_triads_relative.triad_relative_rule,
    rules_curvature.curvature_rule,
]

click_radius = 4

# Vortex tracking
vortex_history = []
MAX_HISTORY = 600

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
    cmap="Greys", alpha=0.3, vmin=0.0, vmax=1.0,
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
dashes = LineCollection(np.stack([p0, p1], axis=1), linewidths=0.5, alpha=0.7)
ax.add_collection(dashes)

# Color by continuous angle (HSV) — no phase-well coloring since there are no wells
dashes.set_color(cm.hsv(sub_th / (2 * np.pi)))

# Vortex markers
scatter_plus = ax.scatter([], [], c='red', s=25, marker='o', zorder=5, label='+1')
scatter_minus = ax.scatter([], [], c='blue', s=25, marker='o', zorder=5, label='-1')

contours = None

ax.set_aspect("equal")
ax.set_xlim(0, N)
ax.set_ylim(0, N)
ax.set_xticks([])
ax.set_yticks([])
ax.legend(loc='upper right', fontsize=8, framealpha=0.8)
ax.set_title(
    f"MINIMAL: Alignment + Geometry + Curvature + Locking (N={N})\n"
    f"Rotationally invariant — no absolute angle preferences anywhere — does discretization emerge?"
)

# =====================================================
# Diagnostics
# =====================================================

fig2, ((ax_count, ax_unity), (ax_theta, ax_comp)) = plt.subplots(2, 2, figsize=(9, 7))
fig2.suptitle("SSB Diagnostics — Rotationally Invariant Rules")

# Vortex count
line_total, = ax_count.plot([], [], 'k-', linewidth=1.5)
ax_count.set_xlim(0, MAX_HISTORY)
ax_count.set_ylim(0, 200)
ax_count.set_xlabel("Frame")
ax_count.set_ylabel("Vortex count")
ax_count.set_title("Topological Defects Over Time")

# Unity
im_unity = ax_unity.imshow(np.zeros((N, N)), vmin=0.0, vmax=1.0,
                            cmap="viridis", origin="lower")
ax_unity.set_title("Unity (local coherence)")
ax_unity.set_xticks([]); ax_unity.set_yticks([])

# Theta field (continuous — looking for spontaneous discretization)
im_theta = ax_theta.imshow(np.zeros((N, N)), vmin=0, vmax=2*np.pi,
                            cmap="hsv", origin="lower")
ax_theta.set_title("Theta field (looking for spontaneous wells)")
ax_theta.set_xticks([]); ax_theta.set_yticks([])

# Compression
im_comp = ax_comp.imshow(np.zeros((N, N)), vmin=0.0, vmax=1.0,
                          cmap="inferno", origin="lower")
ax_comp.set_title("Compression C(i,j)")
ax_comp.set_xticks([]); ax_comp.set_yticks([])

fig2.tight_layout()

# Theta histogram — this is the key diagnostic.
# If discretization emerges, the histogram will show peaks.
# If not, it'll be smooth/uniform.
fig3, ax_hist = plt.subplots(figsize=(6, 3))
ax_hist.set_xlim(0, 2 * np.pi)
ax_hist.set_ylim(0, N * N * 0.05)
ax_hist.set_xlabel("Theta")
ax_hist.set_ylabel("Count")
ax_hist.set_title("Theta Distribution — Peaks = Spontaneous Discretization")
hist_bars = ax_hist.bar(np.linspace(0, 2*np.pi, 36), np.zeros(36),
                         width=2*np.pi/36, color='steelblue', alpha=0.8)
fig3.tight_layout()

# =====================================================
# Sliders
# =====================================================

ax_alpha = fig.add_axes([0.15, 0.20, 0.7, 0.02])
ax_gamma = fig.add_axes([0.15, 0.16, 0.7, 0.02])
ax_kappa = fig.add_axes([0.15, 0.12, 0.7, 0.02])
ax_curv  = fig.add_axes([0.15, 0.08, 0.7, 0.02])
ax_lock  = fig.add_axes([0.15, 0.04, 0.7, 0.02])
ax_calpha = fig.add_axes([0.15, 0.00, 0.7, 0.02])

slider_alpha = Slider(ax_alpha, "Align",    0.0, 1.0, valinit=params.alpha)
slider_gamma = Slider(ax_gamma, "Tension",  0.0, 0.5, valinit=params.gamma)
slider_kappa = Slider(ax_kappa, "Geometry", 0.0, 0.1, valinit=params.kappa)
slider_curv  = Slider(ax_curv,  "Curvature", 0.0, 2.0, valinit=params.curv)
slider_lock  = Slider(ax_lock,  "Lock",     0.0, 1.0, valinit=params.lock_strength)
slider_calpha = Slider(ax_calpha, "Contour", 0.0, 1.0, valinit=0.3)

# =====================================================
# Mouse
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

    params.alpha = slider_alpha.val
    params.gamma = slider_gamma.val
    params.kappa = slider_kappa.val
    params.curv  = slider_curv.val
    params.lock_strength = slider_lock.val

    # Engine step
    step(state, params, RULES, post=rules_locking.locking_postprocess)

    # Pull to CPU
    theta_cpu = to_cpu(state.theta)
    ux_cpu = to_cpu(state.ux)
    uy_cpu = to_cpu(state.uy)
    C_cpu = to_cpu(state.C)

    # Vortices
    vp, vm, winding = diagnostics.detect_vortices(state)
    n_total = len(vp) + len(vm)
    vortex_history.append(n_total)
    if len(vortex_history) > MAX_HISTORY:
        vortex_history.pop(0)

    # Main figure
    bg_comp.set_data(C_cpu)

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

    # HSV coloring — continuous angle, no imposed wells
    dashes.set_color(cm.hsv(sub_th / (2 * np.pi)))

    # Vortex markers
    vs = 25
    if vp:
        vp_arr = np.array(vp)
        vp_r = np.clip(vp_arr[:, 0].astype(int), 0, N-1)
        vp_c = np.clip(vp_arr[:, 1].astype(int), 0, N-1)
        scatter_plus.set_offsets(np.c_[vp_arr[:,1]+ux_cpu[vp_r,vp_c], vp_arr[:,0]+uy_cpu[vp_r,vp_c]])
    else:
        scatter_plus.set_offsets(np.empty((0,2)))
    scatter_plus.set_sizes([vs])

    if vm:
        vm_arr = np.array(vm)
        vm_r = np.clip(vm_arr[:, 0].astype(int), 0, N-1)
        vm_c = np.clip(vm_arr[:, 1].astype(int), 0, N-1)
        scatter_minus.set_offsets(np.c_[vm_arr[:,1]+ux_cpu[vm_r,vm_c], vm_arr[:,0]+uy_cpu[vm_r,vm_c]])
    else:
        scatter_minus.set_offsets(np.empty((0,2)))
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
                levels=8, linewidths=0.4, colors='black', alpha=calpha)

    ax.set_title(
        f"SSB TEST: Align + Geometry + Curvature + Relative Triads + Locking (N={N})\n"
        f"Vortices: {n_total}  |  Frame: {_frame_count}  |  Rotationally invariant — no absolute angle preferences anywhere"
    )

    # Diagnostics
    line_total.set_data(np.arange(len(vortex_history)), vortex_history)
    ax_count.set_xlim(0, max(len(vortex_history), 50))
    ax_count.set_ylim(0, max(max(vortex_history) + 10, 50) if vortex_history else 50)

    unity = diagnostics.compute_unity(state)
    im_unity.set_data(unity)
    im_theta.set_data(theta_cpu)
    im_comp.set_data(C_cpu)

    # Theta histogram — the key question
    counts, _ = np.histogram(theta_cpu.ravel(), bins=36, range=(0, 2*np.pi))
    for bar, h in zip(hist_bars, counts):
        bar.set_height(h)
    ax_hist.set_ylim(0, max(counts.max() * 1.1, 1))

    return dashes, bg_comp, scatter_plus, scatter_minus


anim = FuncAnimation(fig, animate, interval=50, blit=False, cache_frame_data=False)

if __name__ == "__main__":
    plt.show()
