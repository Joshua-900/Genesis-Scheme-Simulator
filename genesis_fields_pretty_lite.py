import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from matplotlib.widgets import Slider
from matplotlib import cm
from matplotlib.collections import LineCollection

# =====================================================

# Parameters

# =====================================================

N = 60          # grid size
dt = 0.05       # time step

alpha0    = 0.3   # neighbor alignment strength
gamma0    = 0.9   # tension gain
kappa0    = 0.10  # geometry coupling (max of your slider)
well0     = 1.4   # phase / localization strength (4-well)
dipole0   = 0.2   # head–tail dipole interaction strength
tri0      = 0.8   # triangular cohesion strength
curv0     = 0.4   # curvature feedback strength

decay_tau  = 0.02   # tension decay
geom_decay = 0.05   # geometry decay (restoring force)
click_radius = 2

tri_sigma  = 0.8
tri_sigma2 = tri_sigma ** 2

# Compression / fold mechanics

sigma_c        = 0.25
sigma_c2       = sigma_c ** 2
lock_strength  = 0.75
tri_lock_gain  = 3.0
phase_lock_gain = 2.5
shell_geom_gain = 0.08

# =====================================================

# State fields

# =====================================================

theta = np.random.rand(N, N) * 2 * np.pi   # orientation field
tau   = np.zeros((N, N))                   # tension field
ux    = np.zeros((N, N))                   # x-displacement
uy    = np.zeros((N, N))                   # y-displacement

compression_field = np.zeros((N, N))

x = np.arange(N)
y = np.arange(N)
X, Y = np.meshgrid(x, y)

# =====================================================

# Helpers

# =====================================================

def angle_diff(a, b):
    d = a - b
    return (d + np.pi) % (2 * np.pi) - np.pi

# =====================================================

# Dynamics

# =====================================================

def update_genesis(theta, tau, ux, uy,
    alpha, gamma, kappa,
    well_strength, dipole_strength,
    tri_strength, curv_strength):
    """
    One update step: alignment, tension+geometry, 4-well phase,
    dipoles, triads, curvature, compression locking.
    Returns updated (theta, tau, ux, uy, compression_field).
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

    # ---------- Tension ----------
    grad = np.abs(dtheta_align)
    tau = (1.0 - decay_tau) * tau + gamma * grad

    # ---------- Geometry ----------
    ux = (1.0 - geom_decay) * ux + kappa * tau * np.cos(theta)
    uy = (1.0 - geom_decay) * uy + kappa * tau * np.sin(theta)

    X_def = X + ux
    Y_def = Y + uy

    # ---------- 4-well phase ----------
    phase_force = -well_strength * np.sin(4.0 * theta)

    # ---------- Dipoles ----------
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

    # ---------- Triads ----------
    tri_torque = np.zeros_like(theta)
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
                S = np.exp(-sq_err / tri_sigma2)
                if S < 1e-3:
                    continue

                tri_torque[i0, j0] += tri_strength * S * np.sin(a0 - th0)
                tri_torque[i1, j1] += tri_strength * S * np.sin(a1 - th1)
                tri_torque[i2, j2] += tri_strength * S * np.sin(a2 - th2)

    # ---------- Curvature ----------
    ux_lap = (np.roll(ux, -1, 0) + np.roll(ux, 1, 0) +
            np.roll(ux, -1, 1) + np.roll(ux, 1, 1) - 4.0 * ux)
    uy_lap = (np.roll(uy, -1, 0) + np.roll(uy, 1, 0) +
            np.roll(uy, -1, 1) + np.roll(uy, 1, 1) - 4.0 * uy)

    curv_mag = np.sqrt(ux_lap*ux_lap + uy_lap*uy_lap) + 1e-6
    phi_curv = np.arctan2(uy_lap, ux_lap)

    curvature_torque = curv_strength * curv_mag * np.sin(phi_curv - theta)

    # ---------- Compression ----------
    ux_x = np.roll(ux, -1, axis=1) - ux
    ux_y = np.roll(ux, -1, axis=0) - ux
    uy_x = np.roll(uy, -1, axis=1) - uy
    uy_y = np.roll(uy, -1, axis=0) - uy

    detF = (1.0 + ux_x) * (1.0 + uy_y) - ux_y * uy_x
    C = np.exp(-(detF * detF) / (sigma_c2 + 1e-8))

    Cx = 0.5 * (np.roll(C, -1, axis=1) - np.roll(C, 1, axis=1))
    Cy = 0.5 * (np.roll(C, -1, axis=0) - np.roll(C, 1, axis=0))

    ux = ux + shell_geom_gain * Cx
    uy = uy + shell_geom_gain * Cy

    tri_torque   = tri_torque * (1.0 + tri_lock_gain   * C)
    phase_force  = phase_force * (1.0 + phase_lock_gain * C)

    # ---------- Total update ----------
    dtheta_total = (
        alpha * dtheta_align +
        0.1 * tau +
        phase_force +
        dipole_torque +
        tri_torque +
        curvature_torque
    )

    dtheta_total = dtheta_total * (1.0 - lock_strength * C)

    theta = theta + dt * dtheta_total
    theta = np.mod(theta, 2.0 * np.pi)

    return theta, tau, ux, uy, C
# =====================================================

# Visualization setup (single pretty figure)

# =====================================================

fig, ax = plt.subplots()
plt.subplots_adjust(bottom=0.30)

# Background = compression field

bg_comp = ax.imshow(compression_field,
origin="lower",
extent=(-2, N + 2, -2, N + 2),
cmap="Greys",
alpha=0.25,
vmin=0.0, vmax=1.0)

# Symmetric dashes

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

# =====================================================

# Sliders

# =====================================================

ax_alpha  = fig.add_axes([0.15, 0.22, 0.7, 0.03])
ax_gamma  = fig.add_axes([0.15, 0.17, 0.7, 0.03])
ax_kappa  = fig.add_axes([0.15, 0.12, 0.7, 0.03])
ax_well   = fig.add_axes([0.15, 0.07, 0.7, 0.03])
ax_dipole = fig.add_axes([0.15, 0.02, 0.7, 0.03])

slider_alpha  = Slider(ax_alpha,  "α Align",        0.0, 1.0,  valinit=alpha0)
slider_gamma  = Slider(ax_gamma,  "γ Tension",      0.0, 1.5,  valinit=gamma0)
slider_kappa  = Slider(ax_kappa,  "κ Geometry",     0.0, 0.1,  valinit=kappa0)
slider_well   = Slider(ax_well,   "Phase Strength", 0.0, 2.0,  valinit=well0)
slider_dipole = Slider(ax_dipole, "Dipole / Triad / Curv", 0.0, 2.0,  valinit=1.0)

# We'll scale tri_strength and curv_strength from this one slider for now:

def tri_strength_from(x):  return tri0 * x
def curv_strength_from(x): return curv0 * x

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

# Animation

# =====================================================

def animate(frame):
    global theta, tau, ux, uy, compression_field

    alpha         = slider_alpha.val
    gamma         = slider_gamma.val
    kappa         = slider_kappa.val
    well_strength = slider_well.val
    dipole_strength = slider_dipole.val
    tri_strength    = tri_strength_from(slider_dipole.val)
    curv_strength   = curv_strength_from(slider_dipole.val)

    theta, tau, ux, uy, C = update_genesis(
        theta, tau, ux, uy,
        alpha, gamma, kappa,
        well_strength, dipole_strength,
        tri_strength, curv_strength
    )

    compression_field = C

    # Background
    bg_comp.set_data(compression_field)

    # Dashes
    Udir = np.cos(theta).ravel()
    Vdir = np.sin(theta).ravel()
    vecs = np.c_[Udir, Vdir]
    vecs /= np.linalg.norm(vecs, axis=1, keepdims=True) + 1e-8

    new_positions = np.c_[(X + ux).ravel(), (Y + uy).ravel()]
    p0 = new_positions - 0.5 * dash_len * vecs
    p1 = new_positions + 0.5 * dash_len * vecs
    segments = np.stack([p0, p1], axis=1)
    dashes.set_segments(segments)

    indices = ((theta + 0.25 * np.pi) // (0.5 * np.pi)).astype(int) % 4
    colors = cm.tab10((indices.ravel() / 4.0))
    dashes.set_color(colors)

    return dashes, bg_comp
anim = FuncAnimation(fig, animate, interval=40, blit=False)

if __name__ == "__main__":
    plt.show()