import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from matplotlib.widgets import Slider
from matplotlib import cm

# =========================

# Parameters

# =========================

N = 40          # grid size
dt = 0.05       # time step

alpha0 = 0.3    # neighbor alignment strength
gamma0 = 0.8    # tension gain
kappa0 = 0.03   # geometry coupling
well0  = 0.6    # phase / localization strength (multi-well potential)
dipole0 = 0.4   # strength of head–tail dipole interactions

decay_tau   = 0.02   # tension decay
geom_decay  = 0.05   # geometry decay (restoring force toward original grid)
click_radius = 2

# =========================

# State fields (ONLY true DOF is theta)

# =========================

theta = np.random.rand(N, N) * 2 * np.pi   # orientation field
tau   = np.zeros((N, N))                   # tension field (driven by theta)
ux    = np.zeros((N, N))                   # x-displacement
uy    = np.zeros((N, N))                   # y-displacement

# Base grid (unity)

x = np.arange(N)
y = np.arange(N)
X, Y = np.meshgrid(x, y)

# =========================

# Update step

# =========================

def update_genesis(theta, tau, ux, uy,
    alpha, gamma, kappa,
    well_strength, dipole_strength):
    """
    One update step:
    theta: orientation field
    tau:   tension (from theta gradients)
    ux,uy: geometry displacement
    alpha: neighbor alignment strength
    gamma: tension gain
    kappa: geometry coupling
    well_strength: strength of 4-well phase potential
    dipole_strength: strength of head–tail interactions
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
    # points are pulled by tension along their orientation
    ux = (1.0 - geom_decay) * ux + kappa * tau * np.cos(theta)
    uy = (1.0 - geom_decay) * uy + kappa * tau * np.sin(theta)

    # ---------- 4-well phase potential (symmetry breaking) ----------
    # V(theta) = -cos(4 theta)
    # force toward minima = -dV/dtheta = -4 sin(4 theta)
    phase_force = -well_strength * np.sin(4.0 * theta)

    # ---------- Dipole head–tail interactions ----------
    # Each dash has a head (direction theta) and a tail (theta + pi).
    # We favor configurations where a cell's head points toward a neighbor's tail.
    dipole_torque = np.zeros_like(theta)

    # current deformed positions
    X_def = X + ux
    Y_def = Y + uy

    # 4-neighbor interactions
    neighbor_offsets = [(1, 0), (-1, 0), (0, 1), (0, -1)]

    for i in range(N):
        for j in range(N):
            for di, dj in neighbor_offsets:
                ni = i + di
                nj = j + dj
                if 0 <= ni < N and 0 <= nj < N:
                    # direction from (i,j) to neighbor (ni,nj)
                    dx = X_def[ni, nj] - X_def[i, j]
                    dy = Y_def[ni, nj] - Y_def[i, j]
                    phi = np.arctan2(dy, dx)

                    # Head of A (i,j) toward B:
                    QA = np.cos(theta[i, j]   - phi)
                    # Head of B away from A (tail pointing to A):
                    QB = np.cos(theta[ni, nj] - (phi + np.pi))
                    Q  = QA * QB  # high if head(A) -> tail(B)

                    # Torque tending to rotate A so its head aims along +phi
                    dipole_torque[i, j]   += Q * np.sin(phi        - theta[i, j])
                    # Torque tending to rotate B so its head aims along +phi+pi
                    dipole_torque[ni, nj] += Q * np.sin(phi + np.pi - theta[ni, nj])

    dipole_torque *= dipole_strength

    # ---------- Total theta update ----------
    dtheta_total = alpha * dtheta_align + 0.1 * tau + phase_force + dipole_torque
    theta = theta + dt * dtheta_total
    theta = np.mod(theta, 2.0 * np.pi)

    return theta, tau, ux, uy

# =========================

# Matplotlib setup

# =========================

fig, ax = plt.subplots()
plt.subplots_adjust(bottom=0.30)

U = np.cos(theta)
V = np.sin(theta)

positions = np.c_[X.ravel(), Y.ravel()]

quiv = ax.quiver(
positions[:, 0], positions[:, 1],
U.ravel(), V.ravel(),
pivot='mid', scale=40, width=0.003
)

ax.set_aspect('equal')
ax.set_xlim(-2, N + 2)
ax.set_ylim(-2, N + 2)
ax.set_xticks([])
ax.set_yticks([])
ax.set_title(
"Genesis Dash Grid — 4-Phase + Dipole Interactions\n"
"Color = phase well, click to disturb"
)

# =========================

# Sliders

# =========================

ax_alpha  = fig.add_axes([0.15, 0.22, 0.7, 0.03])
ax_gamma  = fig.add_axes([0.15, 0.17, 0.7, 0.03])
ax_kappa  = fig.add_axes([0.15, 0.12, 0.7, 0.03])
ax_well   = fig.add_axes([0.15, 0.07, 0.7, 0.03])
ax_dipole = fig.add_axes([0.15, 0.02, 0.7, 0.03])

slider_alpha  = Slider(ax_alpha,  "α Align",        0.0, 1.0,  valinit=alpha0)
slider_gamma  = Slider(ax_gamma,  "γ Tension",      0.0, 1.5,  valinit=gamma0)
slider_kappa  = Slider(ax_kappa,  "κ Geometry",     0.0, 0.1,  valinit=kappa0)
slider_well   = Slider(ax_well,   "Phase Strength", 0.0, 2.0,  valinit=well0)
slider_dipole = Slider(ax_dipole, "Dipole Strength",0.0, 2.0,  valinit=dipole0)

# =========================

# Mouse interaction

# =========================

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

# =========================

# Animation loop

# =========================

def animate(frame):
    global theta, tau, ux, uy

    alpha         = slider_alpha.val
    gamma         = slider_gamma.val
    kappa         = slider_kappa.val
    well_strength = slider_well.val
    dipole_strength = slider_dipole.val

    theta, tau, ux, uy = update_genesis(
        theta, tau, ux, uy,
        alpha, gamma, kappa,
        well_strength, dipole_strength
    )

    # Directions
    U = np.cos(theta).ravel()
    V = np.sin(theta).ravel()
    quiv.set_UVC(U, V)

    # Positions (deformed grid)
    new_positions = np.c_[(X + ux).ravel(), (Y + uy).ravel()]
    quiv.set_offsets(new_positions)

    # Color by which of 4 phase wells theta is nearest to
    # wells at 0, pi/2, pi, 3pi/2
    indices = ((theta + 0.25 * np.pi) // (0.5 * np.pi)).astype(int) % 4
    colors = cm.tab10((indices.ravel() / 4.0))
    quiv.set_color(colors)

    return quiv,
anim = FuncAnimation(fig, animate, interval=30, blit=False)

if __name__ == "__main__":
    plt.show()