# genesis_grid_minimal.py
#
# Minimal emergence experiment: ONLY the non-arbitrary forces.
#
#   Alignment  — the only possible local coupling (derived from symmetry)
#   Geometry   — the core hypothesis (orientation drives displacement)
#   Curvature  — closes the feedback loop (geometry drives orientation)
#   Locking    — emerges from geometry (compression at folds)
#
# NO phase wells. NO dipoles. NO triads.
#
# Usage: python genesis_grid_minimal.py [N]
#        e.g. python genesis_grid_minimal.py 200

import sys
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from matplotlib.widgets import Slider, Button, TextBox
from matplotlib import cm
from matplotlib.collections import LineCollection
from scipy.ndimage import gaussian_filter

from src.genesis_grid import (
    GenesisState, GenesisParams, step,
    rules_alignment, rules_compression, rules_curvature,
    rules_locking, diagnostics,
)
from src.genesis_grid.backend import to_cpu

# =====================================================
# Simulation state (rebuilt on resize)
# =====================================================

class Sim:
    """Mutable container for everything that depends on N."""
    pass

S = Sim()

# Shared params (survive resize)
params = GenesisParams()
params.alpha   = 0.3
params.gamma   = 0.015
params.kappa   = 0.015
params.curv    = 0.4
params.phase   = 0.0
params.dipole  = 0.0
params.triads  = 0.0
params.lock_strength   = 0.75
params.phase_lock_gain = 0.0
params.tri_lock_gain   = 0.0
params.shell_geom_gain = 0.08

RULES = [
    rules_alignment.alignment_rule,
    rules_compression.compression_rule,
    rules_curvature.curvature_rule,
]

# Measurement constants
HIST_BINS = 36
HIST_RANGE = (0, 2 * np.pi)
LOG_INTERVAL = 100
CSV_INTERVAL = 1000
MEASURE_START = 500
CONTOUR_INTERVAL = 4
PHASE_TRAIL_LEN = 2000
MAX_HISTORY = 600

_bin_centers = np.linspace(0, 2 * np.pi, HIST_BINS, endpoint=False) + np.pi / HIST_BINS

def init_sim(N):
    """Initialize or reinitialize the simulation at grid size N."""
    S.N = N
    S.SUBSAMPLE = max(1, N // 50)  # auto-scale: ~50x50 dashes regardless of N
    S.state = GenesisState(N, dt=0.05)
    S.click_radius = max(2, N // 25)

    S.X_full = to_cpu(S.state.X)
    S.Y_full = to_cpu(S.state.Y)

    sub_i = np.arange(0, N, S.SUBSAMPLE)
    sub_j = np.arange(0, N, S.SUBSAMPLE)
    sub_ii, sub_jj = np.meshgrid(sub_i, sub_j)
    S.sub_mask_i = sub_ii.ravel()
    S.sub_mask_j = sub_jj.ravel()
    S.dash_len = 0.45 * S.SUBSAMPLE

    # Reset measurement
    S.vortex_history = []
    S.hist_accumulator = np.zeros(HIST_BINS, dtype=np.float64)
    S.hist_sample_count = 0
    S.frame_count = 0
    S.contours = None
    S.phase_trail_x = []
    S.phase_trail_y = []

    # CSV log
    S.hist_log_file = f"minimal_theta_histogram_N{N}_log.csv"
    with open(S.hist_log_file, "w") as f:
        header = "frame,vortices,samples," + ",".join(f"bin_{c:.3f}" for c in _bin_centers)
        f.write(header + "\n")

    print(f"Initialized N={N}, subsample={S.SUBSAMPLE}, dashes={len(S.sub_mask_i)}")


# Initial N from command line or default
N_init = int(sys.argv[1]) if len(sys.argv) > 1 else 100
init_sim(N_init)

# =====================================================
# Figures — created once, contents rebuilt on resize
# =====================================================

# --- Main figure ---
fig, ax = plt.subplots(figsize=(9, 9))
plt.subplots_adjust(bottom=0.32)

bg_comp = ax.imshow(np.zeros((S.N, S.N)), origin="lower", extent=(0, S.N, 0, S.N),
                     cmap="Greys", alpha=0.3, vmin=0.0, vmax=1.0, interpolation="bilinear")

theta_cpu = to_cpu(S.state.theta)
sub_th = theta_cpu[S.sub_mask_i, S.sub_mask_j]
pos = np.c_[S.X_full[S.sub_mask_i, S.sub_mask_j], S.Y_full[S.sub_mask_i, S.sub_mask_j]]
vecs0 = np.c_[np.cos(sub_th), np.sin(sub_th)]
vecs0 /= np.linalg.norm(vecs0, axis=1, keepdims=True) + 1e-8
p0 = pos - 0.5 * S.dash_len * vecs0
p1 = pos + 0.5 * S.dash_len * vecs0
dashes = LineCollection(np.stack([p0, p1], axis=1), linewidths=0.5, alpha=0.7)
ax.add_collection(dashes)
dashes.set_color(cm.hsv(sub_th / (2 * np.pi)))

scatter_plus = ax.scatter([], [], c='red', s=25, marker='o', zorder=5, label='+1')
scatter_minus = ax.scatter([], [], c='blue', s=25, marker='o', zorder=5, label='-1')

ax.set_aspect("equal")
ax.set_xlim(0, S.N); ax.set_ylim(0, S.N)
ax.set_xticks([]); ax.set_yticks([])
ax.legend(loc='upper right', fontsize=8, framealpha=0.8)

# --- Diagnostics ---
fig2, ((ax_count, ax_unity), (ax_theta, ax_comp)) = plt.subplots(2, 2, figsize=(9, 7))
fig2.suptitle("Minimal System Diagnostics")

line_total, = ax_count.plot([], [], 'k-', linewidth=1.5)
ax_count.set_xlim(0, MAX_HISTORY); ax_count.set_ylim(0, 200)
ax_count.set_xlabel("Frame"); ax_count.set_ylabel("Vortex count")
ax_count.set_title("Topological Defects Over Time")

im_unity = ax_unity.imshow(np.zeros((S.N, S.N)), vmin=0, vmax=1, cmap="viridis", origin="lower")
ax_unity.set_title("Unity (local coherence)"); ax_unity.set_xticks([]); ax_unity.set_yticks([])

im_theta = ax_theta.imshow(np.zeros((S.N, S.N)), vmin=0, vmax=2*np.pi, cmap="hsv", origin="lower")
ax_theta.set_title("Theta field"); ax_theta.set_xticks([]); ax_theta.set_yticks([])

im_comp = ax_comp.imshow(np.zeros((S.N, S.N)), vmin=0, vmax=1, cmap="inferno", origin="lower")
ax_comp.set_title("Compression C(i,j)"); ax_comp.set_xticks([]); ax_comp.set_yticks([])
fig2.tight_layout()

# --- Histograms ---
fig3, (ax_hist, ax_hist_avg) = plt.subplots(2, 1, figsize=(7, 5))
ax_hist.set_xlim(0, 2*np.pi); ax_hist.set_xlabel("Theta"); ax_hist.set_ylabel("Count")
hist_bars = ax_hist.bar(_bin_centers, np.zeros(HIST_BINS), width=2*np.pi/HIST_BINS,
                         color='steelblue', alpha=0.8)

ax_hist_avg.set_xlim(0, 2*np.pi); ax_hist_avg.set_xlabel("Theta"); ax_hist_avg.set_ylabel("Avg Count")
hist_bars_avg = ax_hist_avg.bar(_bin_centers, np.zeros(HIST_BINS), width=2*np.pi/HIST_BINS,
                                 color='darkorange', alpha=0.8)
uniform_line = ax_hist_avg.axhline(0, color='black', linewidth=1, linestyle='--', alpha=0.5, label='uniform')
ax_hist_avg.legend(fontsize=8)
fig3.tight_layout()

# --- Phase portrait ---
fig4, ax_phase = plt.subplots(figsize=(5, 5))
circle_t = np.linspace(0, 2*np.pi, 100)
ax_phase.plot(np.cos(circle_t), np.sin(circle_t), 'k-', linewidth=0.5, alpha=0.3)
ax_phase.axhline(0, color='k', linewidth=0.3, alpha=0.2)
ax_phase.axvline(0, color='k', linewidth=0.3, alpha=0.2)
phase_trail_line, = ax_phase.plot([], [], '-', color='steelblue', linewidth=0.4, alpha=0.3)
phase_dot, = ax_phase.plot([], [], 'o', color='red', markersize=8, zorder=5)
ax_phase.set_xlim(-1.1, 1.1); ax_phase.set_ylim(-1.1, 1.1)
ax_phase.set_aspect('equal')
ax_phase.set_xlabel("⟨cos θ⟩"); ax_phase.set_ylabel("⟨sin θ⟩")
fig4.tight_layout()

# --- Geometry visualization ---
fig5, (ax_mesh, ax_disp, ax_strain) = plt.subplots(1, 3, figsize=(14, 4.5))
fig5.suptitle("Protospace Geometry")

# Deformed grid mesh — draw every Kth grid line
MESH_STEP = max(2, S.N // 40)  # ~40 lines in each direction

mesh_lines_h = []  # horizontal grid lines on deformed mesh
mesh_lines_v = []  # vertical grid lines on deformed mesh
from matplotlib.collections import LineCollection as LC

mesh_h_coll = LC([], linewidths=0.4, colors='black', alpha=0.6)
mesh_v_coll = LC([], linewidths=0.4, colors='black', alpha=0.6)
ax_mesh.add_collection(mesh_h_coll)
ax_mesh.add_collection(mesh_v_coll)
ax_mesh.set_aspect("equal")
ax_mesh.set_xlim(0, S.N); ax_mesh.set_ylim(0, S.N)
ax_mesh.set_xticks([]); ax_mesh.set_yticks([])
ax_mesh.set_title("Deformed Grid Mesh")

# Displacement magnitude
im_disp = ax_disp.imshow(np.zeros((S.N, S.N)), vmin=0, vmax=1,
                           cmap="magma", origin="lower")
ax_disp.set_title("Displacement |u|")
ax_disp.set_xticks([]); ax_disp.set_yticks([])
fig5.colorbar(im_disp, ax=ax_disp, fraction=0.046, pad=0.04)

# Strain field (detF)
im_strain = ax_strain.imshow(np.zeros((S.N, S.N)), vmin=0, vmax=2,
                              cmap="RdBu_r", origin="lower")
ax_strain.set_title("Strain det(F) — red=compressed, blue=stretched")
ax_strain.set_xticks([]); ax_strain.set_yticks([])
fig5.colorbar(im_strain, ax=ax_strain, fraction=0.046, pad=0.04)

fig5.tight_layout()

GEOM_UPDATE_INTERVAL = 5  # update geometry view every Nth frame

# =====================================================
# Rebuild visuals after resize
# =====================================================

def rebuild_visuals():
    """Update all figure elements after N changes."""
    global dashes, scatter_plus, scatter_minus

    N = S.N
    theta_cpu = to_cpu(S.state.theta)

    # Main figure
    ax.clear()
    bg_comp_new = ax.imshow(np.zeros((N, N)), origin="lower", extent=(0, N, 0, N),
                             cmap="Greys", alpha=0.3, vmin=0, vmax=1, interpolation="bilinear")

    sub_th = theta_cpu[S.sub_mask_i, S.sub_mask_j]
    pos = np.c_[S.X_full[S.sub_mask_i, S.sub_mask_j], S.Y_full[S.sub_mask_i, S.sub_mask_j]]
    vecs0 = np.c_[np.cos(sub_th), np.sin(sub_th)]
    vecs0 /= np.linalg.norm(vecs0, axis=1, keepdims=True) + 1e-8
    p0 = pos - 0.5 * S.dash_len * vecs0
    p1 = pos + 0.5 * S.dash_len * vecs0

    dashes_new = LineCollection(np.stack([p0, p1], axis=1), linewidths=0.5, alpha=0.7)
    ax.add_collection(dashes_new)
    dashes_new.set_color(cm.hsv(sub_th / (2 * np.pi)))

    sp = ax.scatter([], [], c='red', s=25, marker='o', zorder=5, label='+1')
    sm = ax.scatter([], [], c='blue', s=25, marker='o', zorder=5, label='-1')

    ax.set_aspect("equal")
    ax.set_xlim(0, N); ax.set_ylim(0, N)
    ax.set_xticks([]); ax.set_yticks([])
    ax.legend(loc='upper right', fontsize=8, framealpha=0.8)

    # Update globals
    globals()['bg_comp'] = bg_comp_new
    globals()['dashes'] = dashes_new
    globals()['scatter_plus'] = sp
    globals()['scatter_minus'] = sm
    S.contours = None

    # Diagnostics — update imshow extents
    for im in [im_unity, im_theta, im_comp]:
        im.set_data(np.zeros((N, N)))
        im.set_extent([0, N, 0, N])

    # Histogram uniform line
    uniform_line.set_ydata([N * N / HIST_BINS])

    # Phase portrait — clear trail
    S.phase_trail_x.clear()
    S.phase_trail_y.clear()
    phase_trail_line.set_data([], [])
    phase_dot.set_data([], [])

    print(f"Rebuilt visuals for N={N}")

# =====================================================
# Sliders and controls
# =====================================================

ax_alpha  = fig.add_axes([0.15, 0.22, 0.55, 0.02])
ax_gamma  = fig.add_axes([0.15, 0.18, 0.55, 0.02])
ax_kappa  = fig.add_axes([0.15, 0.14, 0.55, 0.02])
ax_curv   = fig.add_axes([0.15, 0.10, 0.55, 0.02])
ax_lock   = fig.add_axes([0.15, 0.06, 0.55, 0.02])
ax_calpha = fig.add_axes([0.15, 0.02, 0.55, 0.02])

slider_alpha  = Slider(ax_alpha,  "Align",     0.0, 1.0, valinit=params.alpha)
slider_gamma  = Slider(ax_gamma,  "Tension",   0.0, 0.5, valinit=params.gamma)
slider_kappa  = Slider(ax_kappa,  "Geometry",  0.0, 0.1, valinit=params.kappa)
slider_curv   = Slider(ax_curv,   "Curvature", 0.0, 2.0, valinit=params.curv)
slider_lock   = Slider(ax_lock,   "Lock",      0.0, 1.0, valinit=params.lock_strength)
slider_calpha = Slider(ax_calpha, "Contour",   0.0, 1.0, valinit=0.3)

# Grid size input + restart button
ax_nbox    = fig.add_axes([0.78, 0.18, 0.08, 0.03])
ax_restart = fig.add_axes([0.78, 0.12, 0.15, 0.04])
nbox = TextBox(ax_nbox, "N ", initial=str(S.N))
btn_restart = Button(ax_restart, "Restart", color='#ff6b35', hovercolor='#ff4500')

def on_restart(event):
    try:
        new_n = int(nbox.text)
        if new_n < 20 or new_n > 500:
            print(f"N={new_n} out of range (20-500)")
            return
    except ValueError:
        print("Invalid N")
        return

    init_sim(new_n)
    rebuild_visuals()
    print(f"Restarted at N={new_n}")

btn_restart.on_clicked(on_restart)

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
    N = S.N
    r = S.click_radius
    if 0 <= ci < N and 0 <= cj < N:
        for a in range(-r, r + 1):
            for b in range(-r, r + 1):
                ii, jj = ci + a, cj + b
                if 0 <= ii < N and 0 <= jj < N:
                    S.state.theta[ii, jj] += np.pi * (np.random.rand() - 0.5)

fig.canvas.mpl_connect("button_press_event", on_click)

# =====================================================
# Animation
# =====================================================

def animate(frame):
    S.frame_count += 1
    N = S.N
    state = S.state

    params.alpha = slider_alpha.val
    params.gamma = slider_gamma.val
    params.kappa = slider_kappa.val
    params.curv  = slider_curv.val
    params.lock_strength = slider_lock.val

    step(state, params, RULES, post=rules_locking.locking_postprocess)

    theta_cpu = to_cpu(state.theta)
    ux_cpu = to_cpu(state.ux)
    uy_cpu = to_cpu(state.uy)
    C_cpu = to_cpu(state.C)

    vp, vm, winding = diagnostics.detect_vortices(state)
    n_total = len(vp) + len(vm)
    S.vortex_history.append(n_total)
    if len(S.vortex_history) > MAX_HISTORY:
        S.vortex_history.pop(0)

    # Main figure
    bg_comp.set_data(C_cpu)

    sub_th = theta_cpu[S.sub_mask_i, S.sub_mask_j]
    sub_ux = ux_cpu[S.sub_mask_i, S.sub_mask_j]
    sub_uy = uy_cpu[S.sub_mask_i, S.sub_mask_j]
    sx = S.X_full[S.sub_mask_i, S.sub_mask_j] + sub_ux
    sy = S.Y_full[S.sub_mask_i, S.sub_mask_j] + sub_uy
    vecs = np.c_[np.cos(sub_th), np.sin(sub_th)]
    vecs /= np.linalg.norm(vecs, axis=1, keepdims=True) + 1e-8
    pos = np.c_[sx, sy]
    p0 = pos - 0.5 * S.dash_len * vecs
    p1 = pos + 0.5 * S.dash_len * vecs
    dashes.set_segments(np.stack([p0, p1], axis=1))
    dashes.set_color(cm.hsv(sub_th / (2 * np.pi)))

    vs = 25
    if vp:
        vp_arr = np.array(vp)
        vp_r = np.clip(vp_arr[:, 0].astype(int), 0, N-1)
        vp_c = np.clip(vp_arr[:, 1].astype(int), 0, N-1)
        scatter_plus.set_offsets(np.c_[vp_arr[:,1]+ux_cpu[vp_r,vp_c], vp_arr[:,0]+uy_cpu[vp_r,vp_c]])
    else:
        scatter_plus.set_offsets(np.empty((0, 2)))
    scatter_plus.set_sizes([vs])

    if vm:
        vm_arr = np.array(vm)
        vm_r = np.clip(vm_arr[:, 0].astype(int), 0, N-1)
        vm_c = np.clip(vm_arr[:, 1].astype(int), 0, N-1)
        scatter_minus.set_offsets(np.c_[vm_arr[:,1]+ux_cpu[vm_r,vm_c], vm_arr[:,0]+uy_cpu[vm_r,vm_c]])
    else:
        scatter_minus.set_offsets(np.empty((0, 2)))
    scatter_minus.set_sizes([vs])

    if S.frame_count % CONTOUR_INTERVAL == 0:
        if S.contours is not None:
            S.contours.remove()
            S.contours = None
        calpha = slider_calpha.val
        if calpha > 0.01:
            sigma = max(1.0, N / 60)
            theta_smooth = gaussian_filter(theta_cpu, sigma=sigma)
            S.contours = ax.contour(
                S.X_full + ux_cpu, S.Y_full + uy_cpu, theta_smooth,
                levels=8, linewidths=0.4, colors='black', alpha=calpha)

    ax.set_title(
        f"MINIMAL: Align + Geometry + Curvature + Locking (N={N})\n"
        f"Vortices: {n_total}  |  Frame: {S.frame_count}  |  No phase wells, no dipoles, no triads"
    )

    # Diagnostics
    line_total.set_data(np.arange(len(S.vortex_history)), S.vortex_history)
    ax_count.set_xlim(0, max(len(S.vortex_history), 50))
    ax_count.set_ylim(0, max(max(S.vortex_history) + 10, 50) if S.vortex_history else 50)

    unity = diagnostics.compute_unity(state)
    im_unity.set_data(unity)
    im_theta.set_data(theta_cpu)
    im_comp.set_data(C_cpu)

    # Histogram
    counts, _ = np.histogram(theta_cpu.ravel(), bins=HIST_BINS, range=HIST_RANGE)
    for bar, h in zip(hist_bars, counts):
        bar.set_height(h)
    ax_hist.set_ylim(0, max(counts.max() * 1.1, 1))
    ax_hist.set_title(f"Instant Theta Distribution (frame {S.frame_count})")

    if S.frame_count >= MEASURE_START and S.frame_count % LOG_INTERVAL == 0:
        S.hist_accumulator += counts.astype(np.float64)
        S.hist_sample_count += 1
        avg = S.hist_accumulator / S.hist_sample_count
        for bar, h in zip(hist_bars_avg, avg):
            bar.set_height(h)
        ax_hist_avg.set_ylim(0, max(avg.max() * 1.1, 1))
        ax_hist_avg.set_title(
            f"Time-Averaged Distribution ({S.hist_sample_count} samples, "
            f"frames {MEASURE_START}-{S.frame_count})")

    if S.frame_count >= MEASURE_START and S.frame_count % CSV_INTERVAL == 0 and S.hist_sample_count > 0:
        avg = S.hist_accumulator / S.hist_sample_count
        with open(S.hist_log_file, "a") as f:
            row = f"{S.frame_count},{n_total},{S.hist_sample_count}," + ",".join(f"{v:.2f}" for v in avg)
            f.write(row + "\n")
        print(f"[frame {S.frame_count}] N={N}, vortices={n_total}, "
              f"peak={avg.max():.1f}, trough={avg.min():.1f}, ratio={avg.max()/max(avg.min(),1):.2f}")

    # Phase portrait
    mean_cos = np.mean(np.cos(theta_cpu))
    mean_sin = np.mean(np.sin(theta_cpu))
    S.phase_trail_x.append(mean_cos)
    S.phase_trail_y.append(mean_sin)
    if len(S.phase_trail_x) > PHASE_TRAIL_LEN:
        S.phase_trail_x.pop(0)
        S.phase_trail_y.pop(0)
    phase_trail_line.set_data(S.phase_trail_x, S.phase_trail_y)
    phase_dot.set_data([mean_cos], [mean_sin])
    mag = np.sqrt(mean_cos**2 + mean_sin**2)
    ax_phase.set_title(f"Order Parameter |m| = {mag:.3f}\ncenter = disordered, edge = full SSB")

    # Geometry visualization (every Nth frame — mesh is expensive to draw)
    if S.frame_count % GEOM_UPDATE_INTERVAL == 0:
        ms = max(2, N // 40)  # mesh step

        # Deformed grid mesh
        X_def = S.X_full + ux_cpu
        Y_def = S.Y_full + uy_cpu

        # Horizontal lines (constant row, varying col)
        h_segs = []
        for i in range(0, N, ms):
            pts = np.c_[X_def[i, :], Y_def[i, :]].reshape(-1, 1, 2)
            if len(pts) > 1:
                segs = np.concatenate([pts[:-1], pts[1:]], axis=1)
                h_segs.extend(segs)

        # Vertical lines (constant col, varying row)
        v_segs = []
        for j in range(0, N, ms):
            pts = np.c_[X_def[:, j], Y_def[:, j]].reshape(-1, 1, 2)
            if len(pts) > 1:
                segs = np.concatenate([pts[:-1], pts[1:]], axis=1)
                v_segs.extend(segs)

        if h_segs:
            mesh_h_coll.set_segments(h_segs)
        if v_segs:
            mesh_v_coll.set_segments(v_segs)

        ax_mesh.set_xlim(-N*0.05, N*1.05)
        ax_mesh.set_ylim(-N*0.05, N*1.05)

        # Displacement magnitude
        disp_mag = np.sqrt(ux_cpu**2 + uy_cpu**2)
        im_disp.set_data(disp_mag)
        im_disp.set_clim(0, max(disp_mag.max(), 0.01))
        ax_disp.set_title(f"Displacement |u| (max={disp_mag.max():.2f})")

        # Strain field (detF)
        ux_x = np.roll(ux_cpu, -1, axis=1) - ux_cpu
        ux_y = np.roll(ux_cpu, -1, axis=0) - ux_cpu
        uy_x = np.roll(uy_cpu, -1, axis=1) - uy_cpu
        uy_y = np.roll(uy_cpu, -1, axis=0) - uy_cpu
        detF = (1.0 + ux_x) * (1.0 + uy_y) - ux_y * uy_x

        im_strain.set_data(detF)
        im_strain.set_clim(max(detF.min(), -0.5), min(detF.max(), 2.5))
        ax_strain.set_title(f"Strain det(F) [{detF.min():.2f}, {detF.max():.2f}]")

    return dashes, bg_comp, scatter_plus, scatter_minus


anim = FuncAnimation(fig, animate, interval=50, blit=False, cache_frame_data=False)

if __name__ == "__main__":
    plt.show()
