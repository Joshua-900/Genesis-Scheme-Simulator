import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from matplotlib.widgets import Slider
from matplotlib import cm
from matplotlib.collections import LineCollection

# =====================================================

# Parameters

# =====================================================

N = 40          # grid size
dt = 0.05       # time step

alpha0    = 0.3   # neighbor alignment strength
gamma0    = 0.015   # tension gain
kappa0    = 0.015  # geometry coupling (max of your slider)
well0     = 0.6   # phase / localization strength (4-well)
dipole0   = 0.3   # head–tail dipole interaction strength
tri0      = 0.8   # triangular cohesion strength
curv0     = 0.4   # curvature feedback strength

decay_tau  = 0.02   # tension decay
geom_decay = 0.05   # geometry decay (restoring force)
click_radius = 2

tri_sigma  = 0.8
tri_sigma2 = tri_sigma ** 2

# Compression / fold mechanics (a bit more aggressive)

sigma_c        = 0.25
sigma_c2       = sigma_c ** 2
lock_strength  = 0.75
tri_lock_gain  = 3.0
phase_lock_gain = 2.5
shell_geom_gain = 0.08

# =====================================================

# State fields (ONLY true DOF is theta)

# =====================================================

theta = np.random.rand(N, N) * 2 * np.pi   # orientation field
tau   = np.zeros((N, N))                   # tension field (driven by theta)
ux    = np.zeros((N, N))                   # x-displacement
uy    = np.zeros((N, N))                   # y-displacement

# Genesis diagnostic fields (computed, not independent)

unity_field      = np.zeros((N, N))  # U: local coherence
difference_field = np.zeros((N, N))  # D: normalized tension
distinct_field   = np.zeros((N, N))  # S: triad coherence
compression_field = np.zeros((N, N)) # C: compression / fold intensity

# Base grid (unity)

x = np.arange(N)
y = np.arange(N)
X, Y = np.meshgrid(x, y)

# =====================================================

# Helpers

# =====================================================

def angle_diff(a, b):
    """Smallest signed difference a-b in [-pi, pi]."""
    d = a - b
    return (d + np.pi) % (2 * np.pi) - np.pi

# =====================================================

# Update step

# =====================================================

def update_genesis(theta, tau, ux, uy,
    alpha, gamma, kappa,
    well_strength, dipole_strength,
    tri_strength, curv_strength):
    """
    One update step with:
    - neighbor alignment
    - tension + geometry
    - 4-well phase potential
    - dipole head–tail interactions
    - triangular cohesion (3-body)
    - curvature feedback
    - compression-based interlock & boundary shaping

    Also computes Genesis diagnostic fields:
      U(i,j): local unity / coherence
      D(i,j): difference (normalized tension)
      S(i,j): distinction (triad coherence)
      C(i,j): compression / fold measure
    """
    # ---------- Neighbor alignment ----------
    up    = np.roll(theta, -1, axis=0)
    down  = np.roll(theta,  1, axis=0)
    left  = np.roll(theta, -1, axis=1)
    right = np.roll(theta,  1, axis=1)

    dtheta_align = (
        np.sin(up - theta) +
        np.sin(down - theta) +
        np.sin(left - theta) +
        np.sin(right - theta)
    )

    # ---------- Tension from gradients ----------
    grad = np.abs(dtheta_align)
    tau = (1.0 - decay_tau) * tau + gamma * grad

    # ---------- Geometry displacement (with damping) ----------
    ux = (1.0 - geom_decay) * ux + kappa * tau * np.cos(theta)
    uy = (1.0 - geom_decay) * uy + kappa * tau * np.sin(theta)

    # precompute deformed positions
    X_def = X + ux
    Y_def = Y + uy

    # ---------- 4-well phase potential (symmetry breaking) ----------
    # V(theta) = -cos(4 theta), dV/dtheta = 4 sin(4 theta)
    phase_force = -well_strength * np.sin(4.0 * theta)

    # ---------- Dipole head–tail interactions ----------
    dipole_torque = np.zeros_like(theta)
    neighbor_offsets = [(1, 0), (-1, 0), (0, 1), (0, -1)]
    for i in range(N):
        for j in range(N):
            for di, dj in neighbor_offsets:
                ni = i + di
                nj = j + dj
                if 0 <= ni < N and 0 <= nj < N:
                    dx = X_def[ni, nj] - X_def[i, j]
                    dy = Y_def[ni, nj] - Y_def[i, j]
                    phi = np.arctan2(dy, dx)

                    QA = np.cos(theta[i, j]   - phi)
                    QB = np.cos(theta[ni, nj] - (phi + np.pi))
                    Q  = QA * QB

                    dipole_torque[i, j]   += Q * np.sin(phi        - theta[i, j])
                    dipole_torque[ni, nj] += Q * np.sin(phi + np.pi - theta[ni, nj])

    dipole_torque *= dipole_strength

    # ---------- Triangular cohesion (3-body, proto-tiles) ----------
    tri_torque = np.zeros_like(theta)
    tri_score  = np.zeros_like(theta)   # S(i,j): distinction measure

    # Triads: right-angle L-shapes around each cell
    triads = [
        ((0, 0), (1, 0), (0, 1),  (0.25*np.pi, 0.0,        0.5*np.pi)),   # NE
        ((0, 0), (-1, 0), (0, 1), (0.75*np.pi, np.pi,      0.5*np.pi)),   # NW
        ((0, 0), (1, 0), (0, -1),( -0.25*np.pi, 0.0,     -0.5*np.pi)),    # SE
        ((0, 0), (-1,0), (0, -1),( -0.75*np.pi, np.pi,   -0.5*np.pi)),    # SW
    ]

    for i in range(N):
        for j in range(N):
            for (o0, o1, o2, angs) in triads:
                i0, j0 = i + o0[0], j + o0[1]
                i1, j1 = i + o1[0], j + o1[1]
                i2, j2 = i + o2[0], j + o2[1]
                if not (0 <= i0 < N and 0 <= j0 < N and
                        0 <= i1 < N and 0 <= j1 < N and
                        0 <= i2 < N and 0 <= j2 < N):
                    continue

                th0 = theta[i0, j0]
                th1 = theta[i1, j1]
                th2 = theta[i2, j2]

                a0, a1, a2 = angs

                d0 = angle_diff(th0, a0)
                d1 = angle_diff(th1, a1)
                d2 = angle_diff(th2, a2)

                sq_err = d0*d0 + d1*d1 + d2*d2
                S = np.exp(-sq_err / tri_sigma2)  # 0..1 triadic coherence

                if S < 1e-3:
                    continue

                tri_torque[i0, j0] += tri_strength * S * np.sin(a0 - th0)
                tri_torque[i1, j1] += tri_strength * S * np.sin(a1 - th1)
                tri_torque[i2, j2] += tri_strength * S * np.sin(a2 - th2)

                # record maximum S for each participating cell
                tri_score[i0, j0] = max(tri_score[i0, j0], S)
                tri_score[i1, j1] = max(tri_score[i1, j1], S)
                tri_score[i2, j2] = max(tri_score[i2, j2], S)

    # ---------- Curvature feedback (geometry -> orientation) ----------
    ux_lap = (np.roll(ux, -1, 0) + np.roll(ux, 1, 0) +
            np.roll(ux, -1, 1) + np.roll(ux, 1, 1) - 4.0 * ux)
    uy_lap = (np.roll(uy, -1, 0) + np.roll(uy, 1, 0) +
            np.roll(uy, -1, 1) + np.roll(uy, 1, 1) - 4.0 * uy)

    curv_mag = np.sqrt(ux_lap*ux_lap + uy_lap*uy_lap) + 1e-6
    phi_curv = np.arctan2(uy_lap, ux_lap)

    curvature_torque = curv_strength * curv_mag * np.sin(phi_curv - theta)

    # ---------- Compression / fold detection from deformation ----------
    ux_x = np.roll(ux, -1, axis=1) - ux   # ∂ux/∂x
    ux_y = np.roll(ux, -1, axis=0) - ux   # ∂ux/∂y
    uy_x = np.roll(uy, -1, axis=1) - uy   # ∂uy/∂x
    uy_y = np.roll(uy, -1, axis=0) - uy   # ∂uy/∂y

    detF = (1.0 + ux_x) * (1.0 + uy_y) - ux_y * uy_x

    # C ~ 1 when detF ~ 0 (high compression / potential fold)
    C = np.exp(-(detF * detF) / (sigma_c2 + 1e-8))

    # Compression gradient for "shell" effect around compressed cores
    Cx = 0.5 * (np.roll(C, -1, axis=1) - np.roll(C, 1, axis=1))
    Cy = 0.5 * (np.roll(C, -1, axis=0) - np.roll(C, 1, axis=0))

    # Geometry push along compression gradients (sharpen boundaries / repel shell)
    ux = ux + shell_geom_gain * Cx
    uy = uy + shell_geom_gain * Cy

    # Amplify triad & phase locking in compressed cores (interlock / solidify)
    tri_torque   = tri_torque * (1.0 + tri_lock_gain   * C)
    phase_force  = phase_force * (1.0 + phase_lock_gain * C)

    # ---------- Total theta update ----------
    dtheta_total = (
        alpha * dtheta_align +
        0.1 * tau +
        phase_force +
        dipole_torque +
        tri_torque +
        curvature_torque
    )

    # Slow dynamics in high-compression regions (lock them into "solid" structures)
    dtheta_total = dtheta_total * (1.0 - lock_strength * C)

    theta = theta + dt * dtheta_total
    theta = np.mod(theta, 2.0 * np.pi)

    # ---------- Genesis diagnostic fields ----------

    # UNITY: local coherence of orientation (magnitude of neighborhood order parameter)
    ex = np.cos(theta)
    ey = np.sin(theta)
    ex_avg = (ex + np.roll(ex, 1, 0) + np.roll(ex, -1, 0)
                + np.roll(ex, 1, 1) + np.roll(ex, -1, 1)) / 5.0
    ey_avg = (ey + np.roll(ey, 1, 0) + np.roll(ey, -1, 0)
                + np.roll(ey, 1, 1) + np.roll(ey, -1, 1)) / 5.0
    unity = np.sqrt(ex_avg*ex_avg + ey_avg*ey_avg)   # 0..1

    # DIFFERENCE: normalized tension (how far from unity)
    tau_norm = tau / (np.max(tau) + 1e-6)           # 0..1

    # DISTINCTION: triadic coherence score already computed (0..1)
    distinction = tri_score

    return theta, tau, ux, uy, unity, tau_norm, distinction, C

# =====================================================

# Matplotlib setup: main pretty figure

# =====================================================

fig, ax = plt.subplots()
plt.subplots_adjust(bottom=0.38)

# Background heatmap: compression (C)

comp_norm = compression_field  # initially zeros
bg_comp = ax.imshow(comp_norm,
origin="lower",
extent=(-2, N + 2, -2, N + 2),
cmap="Greys",
alpha=0.25,
vmin=0.0, vmax=1.0)

# Symmetric dash visualization (no arrow heads)

positions = np.c_[X.ravel(), Y.ravel()]
U0 = np.cos(theta).ravel()
V0 = np.sin(theta).ravel()
vecs0 = np.c_[U0, V0]
vecs0 /= np.linalg.norm(vecs0, axis=1, keepdims=True) + 1e-8
dash_len = 0.6

p0 = positions - 0.5 * dash_len * vecs0
p1 = positions + 0.5 * dash_len * vecs0
segments0 = np.stack([p0, p1], axis=1)

dashes = LineCollection(segments0, linewidths=0.7)
ax.add_collection(dashes)

# Initial color by phase wells

indices0 = ((theta + 0.25 * np.pi) // (0.5 * np.pi)).astype(int) % 4
colors0 = cm.tab10((indices0.ravel() / 4.0))
dashes.set_color(colors0)

ax.set_aspect('equal')
ax.set_xlim(-2, N + 2)
ax.set_ylim(-2, N + 2)
ax.set_xticks([])
ax.set_yticks([])
ax.set_title(
"Genesis Dash Grid — Phase + Dipoles + Triads + Curvature + Compression\n"
"Symmetric dashes, background = compression, color = phase, click to disturb"
)

# Initial contour overlay (quality landscape)

contours = ax.contour(X, Y, theta, levels=10,
linewidths=0.3, colors='k', alpha=0.15)

# =====================================================

# Sliders

# =====================================================

ax_alpha  = fig.add_axes([0.15, 0.30, 0.7, 0.03])
ax_gamma  = fig.add_axes([0.15, 0.25, 0.7, 0.03])
ax_kappa  = fig.add_axes([0.15, 0.20, 0.7, 0.03])
ax_well   = fig.add_axes([0.15, 0.15, 0.7, 0.03])
ax_dipole = fig.add_axes([0.15, 0.10, 0.7, 0.03])
ax_tri    = fig.add_axes([0.15, 0.05, 0.7, 0.03])
ax_curv   = fig.add_axes([0.15, 0.00, 0.7, 0.03])

slider_alpha  = Slider(ax_alpha,  "α Align",        0.0, 1.0,  valinit=alpha0)
slider_gamma  = Slider(ax_gamma,  "γ Tension",      0.0, 1.5,  valinit=gamma0)
slider_kappa  = Slider(ax_kappa,  "κ Geometry",     0.0, 0.1,  valinit=kappa0)
slider_well   = Slider(ax_well,   "Phase Strength", 0.0, 2.0,  valinit=well0)
slider_dipole = Slider(ax_dipole, "Dipole Strength",0.0, 2.0,  valinit=dipole0)
slider_tri    = Slider(ax_tri,    "Triad Strength", 0.0, 2.0,  valinit=tri0)
slider_curv   = Slider(ax_curv,   "Curv Strength",  0.0, 2.0,  valinit=curv0)

# =====================================================

# Second figure for Genesis fields (Unity, Distinction)

# =====================================================

fig2, (ax_u, ax_s) = plt.subplots(1, 2, figsize=(7, 3))
fig2.suptitle("Genesis Fields: Unity (U) and Distinction (S)")

im_unity = ax_u.imshow(unity_field, vmin=0.0, vmax=1.0,
cmap="viridis", origin="lower")
ax_u.set_title("Unity U(i,j)")
ax_u.set_xticks([])
ax_u.set_yticks([])

im_distinct = ax_s.imshow(distinct_field, vmin=0.0, vmax=1.0,
cmap="magma", origin="lower")
ax_s.set_title("Distinction S(i,j)")
ax_s.set_xticks([])
ax_s.set_yticks([])

fig2.colorbar(im_unity, ax=ax_u, fraction=0.046, pad=0.04)
fig2.colorbar(im_distinct, ax=ax_s, fraction=0.046, pad=0.04)

# =====================================================

# Mouse interaction

# =====================================================

def on_click(event):
    global theta
    if event.inaxes != ax:
        return
    if event.xdata is None or event.ydata is None:
        return

    i = int(round(event.ydata))
    j = int(round(event.xdata))

    if 0 <= i < N and 0 <= j < N:
        for a in range(-click_radius, click_radius + 1):
            for b in range(-click_radius, click_radius + 1):
                ii = i + a
                jj = j + b
                if 0 <= ii < N and 0 <= jj < N:
                    theta[ii, jj] += np.pi * (np.random.rand() - 0.5)

    fig.canvas.mpl_connect("button_press_event", on_click)

# =====================================================

# Animation loop

# =====================================================

def animate(frame):
    global theta, tau, ux, uy
    global unity_field, difference_field, distinct_field, compression_field
    global contours

    alpha         = slider_alpha.val
    gamma         = slider_gamma.val
    kappa         = slider_kappa.val
    well_strength = slider_well.val
    dipole_strength = slider_dipole.val
    tri_strength    = slider_tri.val
    curv_strength   = slider_curv.val

    theta, tau, ux, uy, U, D, S, C = update_genesis(
        theta, tau, ux, uy,
        alpha, gamma, kappa,
        well_strength, dipole_strength,
        tri_strength, curv_strength
    )

    unity_field      = U
    difference_field = D
    distinct_field   = S
    compression_field = C

    # ----- update background compression heatmap -----
    bg_comp.set_data(compression_field)

    # ----- update symmetric dash segments -----
    Udir = np.cos(theta).ravel()
    Vdir = np.sin(theta).ravel()
    vecs = np.c_[Udir, Vdir]
    vecs /= np.linalg.norm(vecs, axis=1, keepdims=True) + 1e-8

    new_positions = np.c_[(X + ux).ravel(), (Y + uy).ravel()]
    p0 = new_positions - 0.5 * dash_len * vecs
    p1 = new_positions + 0.5 * dash_len * vecs
    segments = np.stack([p0, p1], axis=1)
    dashes.set_segments(segments)

    # Color by phase well
    indices = ((theta + 0.25 * np.pi) // (0.5 * np.pi)).astype(int) % 4
    colors = cm.tab10((indices.ravel() / 4.0))
    dashes.set_color(colors)

    # ----- update contours (quality landscape) -----
    if contours is not None and hasattr(contours, 'collections'):
        for c in contours.collections:
            c.remove()
    contours = ax.contour(X + ux, Y + uy, theta, levels=10,
                          linewidths=0.3, colors='k', alpha=0.15)

    # ----- update Genesis field visualizations -----
    im_unity.set_data(unity_field)
    im_distinct.set_data(distinct_field)

    return dashes, bg_comp, im_unity, im_distinct
anim = FuncAnimation(fig, animate, interval=40, blit=False, cache_frame_data=False)

if __name__ == "__main__":
    plt.show()