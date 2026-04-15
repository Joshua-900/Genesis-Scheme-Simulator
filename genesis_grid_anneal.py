# genesis_grid_anneal.py
#
# Annealing experiment: same physics as genesis_grid_large.py but with a
# temperature parameter that decays over time. High temperature unlocks
# compressed regions and adds noise, allowing the system to explore
# lower-energy configurations before freezing.
#
# The anneal cycle:
#   1. Hot start — lock_strength ≈ 0, noise injected, system is fluid
#   2. Slow cooling — lock_strength ramps toward target, noise decays
#   3. Frozen — system locks into whatever structure it found
#   4. (Optional) click "Reheat" to restart the cycle
#
# Also adds compression decay — C relaxes toward zero so locked regions
# can re-compete during the hot phase.

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from matplotlib.widgets import Slider, Button
from matplotlib import cm
from matplotlib.collections import LineCollection
from scipy.ndimage import gaussian_filter

from src.genesis_grid import (
    GenesisState, GenesisParams, step,
    rules_alignment, rules_compression,
    rules_phase, rules_dipoles, rules_triads, rules_curvature,
    rules_locking,
)
from src.genesis_grid.backend import xp, to_cpu

# =====================================================
# Setup
# =====================================================

N = 150
SUBSAMPLE = 3
CONTOUR_INTERVAL = 5

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

params.lock_strength   = 0.0   # starts unlocked (hot)
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
# Annealing state
# =====================================================

class AnnealState:
    def __init__(self):
        self.temperature = 1.0       # 1.0 = hot, 0.0 = frozen
        self.cooling_rate = 0.002    # per frame
        self.target_lock = 0.75      # lock_strength when fully cooled
        self.noise_scale = 0.15      # theta noise amplitude at T=1
        self.comp_decay = 0.05       # how fast C relaxes during hot phase
        self.frame = 0

    def reset(self):
        self.temperature = 1.0
        self.frame = 0
        # Reset compression and geometry so locked regions unlock
        state.C[:] = 0.0
        state.ux[:] = 0.0
        state.uy[:] = 0.0
        state.tau[:] = 0.0

    def step(self):
        self.frame += 1

        # Cool down
        self.temperature = max(0.0, self.temperature - self.cooling_rate)

        # Lock strength ramps up as temperature drops
        params.lock_strength = self.target_lock * (1.0 - self.temperature)

        # Inject noise proportional to temperature
        if self.temperature > 0.01:
            noise = self.noise_scale * self.temperature * xp.random.randn(N, N)
            state.theta = (state.theta + noise) % (2 * xp.pi)

            # Decay compression during hot phase (let locked regions unlock)
            state.C *= (1.0 - self.comp_decay * self.temperature)


anneal = AnnealState()

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
plt.subplots_adjust(bottom=0.30)

# Phase-well background
bg_phase = ax.imshow(
    np.zeros((N, N)),
    origin="lower", extent=(0, N, 0, N),
    cmap="tab10", alpha=0.15, vmin=0, vmax=4,
    interpolation="nearest",
)

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
dashes = LineCollection(np.stack([p0, p1], axis=1), linewidths=0.6)
ax.add_collection(dashes)
dashes.set_color(cm.tab10(((sub_th + 0.25*np.pi) // (0.5*np.pi)).astype(int) % 4 / 4.0))

contours = None

# Temperature bar (visual indicator)
temp_bar = ax.barh(N * 0.98, anneal.temperature * N, height=N * 0.015,
                    left=0, color='orangered', alpha=0.8)
temp_text = ax.text(N * 0.5, N * 1.01, "T = 1.000  (HOT)", ha='center',
                     fontsize=9, fontweight='bold', color='orangered')

ax.set_aspect("equal")
ax.set_xlim(0, N)
ax.set_ylim(0, N * 1.04)
ax.set_xticks([])
ax.set_yticks([])
ax.set_title(f"Genesis Grid Annealing — N={N}")

# =====================================================
# Diagnostics
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
# Sliders and buttons
# =====================================================

ax_cooling = fig.add_axes([0.15, 0.20, 0.55, 0.02])
ax_alpha   = fig.add_axes([0.15, 0.16, 0.55, 0.02])
ax_gamma   = fig.add_axes([0.15, 0.12, 0.55, 0.02])
ax_well    = fig.add_axes([0.15, 0.08, 0.55, 0.02])
ax_calpha  = fig.add_axes([0.15, 0.04, 0.55, 0.02])
ax_lock    = fig.add_axes([0.15, 0.00, 0.55, 0.02])

slider_cooling = Slider(ax_cooling, "Cool rate", 0.0005, 0.01, valinit=anneal.cooling_rate, valfmt='%.4f')
slider_alpha   = Slider(ax_alpha,   "Align",     0.0, 1.0, valinit=params.alpha)
slider_gamma   = Slider(ax_gamma,   "Tension",   0.0, 1.5, valinit=params.gamma)
slider_well    = Slider(ax_well,    "Phase",     0.0, 2.0, valinit=params.phase)
slider_calpha  = Slider(ax_calpha,  "Contour",   0.0, 1.0, valinit=0.6)
slider_lock    = Slider(ax_lock,    "Max Lock",  0.0, 1.0, valinit=anneal.target_lock)

# Reheat button
ax_reheat = fig.add_axes([0.78, 0.12, 0.15, 0.06])
btn_reheat = Button(ax_reheat, 'Reheat', color='#ff6b35', hovercolor='#ff4500')

def on_reheat(event):
    anneal.reset()

btn_reheat.on_clicked(on_reheat)

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

    # Read sliders
    anneal.cooling_rate = slider_cooling.val
    anneal.target_lock = slider_lock.val
    params.alpha = slider_alpha.val
    params.gamma = slider_gamma.val
    params.phase = slider_well.val

    # Anneal step (adjusts lock_strength, injects noise, decays C)
    anneal.step()

    # Engine step
    step(state, params, RULES, post=rules_locking.locking_postprocess)

    # Pull to CPU
    theta_cpu = to_cpu(state.theta)
    ux_cpu = to_cpu(state.ux)
    uy_cpu = to_cpu(state.uy)
    C_cpu = to_cpu(state.C)

    # Phase background
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

    # Temperature bar
    T = anneal.temperature
    temp_bar[0].set_width(T * N)
    if T > 0.5:
        temp_bar[0].set_color('orangered')
        label = f"T = {T:.3f}  (HOT)"
        temp_text.set_color('orangered')
    elif T > 0.1:
        temp_bar[0].set_color('goldenrod')
        label = f"T = {T:.3f}  (cooling)"
        temp_text.set_color('goldenrod')
    elif T > 0.01:
        temp_bar[0].set_color('steelblue')
        label = f"T = {T:.3f}  (cold)"
        temp_text.set_color('steelblue')
    else:
        temp_bar[0].set_color('navy')
        label = f"T = {T:.3f}  (FROZEN)"
        temp_text.set_color('navy')
    temp_text.set_text(label)

    # Contours
    if _frame_count % CONTOUR_INTERVAL == 0:
        if contours is not None:
            contours.remove()
            contours = None

        calpha = slider_calpha.val
        if calpha > 0.01 and T < 0.5:
            theta_smooth = gaussian_filter(theta_cpu, sigma=2.0)
            contours = ax.contour(
                X_full + ux_cpu, Y_full + uy_cpu, theta_smooth,
                levels=6, linewidths=0.5,
                colors='black', alpha=calpha)

    # Diagnostics
    ex = np.cos(theta_cpu); ey = np.sin(theta_cpu)
    ex_avg = (ex + np.roll(ex,1,0) + np.roll(ex,-1,0) + np.roll(ex,1,1) + np.roll(ex,-1,1)) / 5.0
    ey_avg = (ey + np.roll(ey,1,0) + np.roll(ey,-1,0) + np.roll(ey,1,1) + np.roll(ey,-1,1)) / 5.0
    unity = np.sqrt(ex_avg**2 + ey_avg**2)

    im_unity.set_data(unity)
    im_comp.set_data(C_cpu)

    return dashes, bg_comp, bg_phase, im_unity, im_comp


anim = FuncAnimation(fig, animate, interval=50, blit=False, cache_frame_data=False)

if __name__ == "__main__":
    plt.show()
