import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from matplotlib.widgets import Slider

# =========================

# Parameters

# =========================

N = 40          # grid size
dt = 0.05       # time step

alpha0 = 0.3    # neighbor alignment strength (primary field)
gamma0 = 0.8    # tension gain (how strongly gradients feed tension)
kappa0 = 0.03   # geometry coupling (how much tension moves the grid)
lambda0 = 0.6   # emergence strength: how strongly tension spawns secondary field

decay_tau = 0.02   # tension decay per step
decay_phi = 0.05   # secondary field relaxation
click_radius = 2   # radius of disturbance on click

# =========================

# State fields

# =========================

theta = np.random.rand(N, N) * 2 * np.pi   # primary orientation field
phi   = np.zeros((N, N))                   # secondary/emergent orientation field
tau   = np.zeros((N, N))                   # tension / distinction field
ux    = np.zeros((N, N))                   # x-displacement of grid
uy    = np.zeros((N, N))                   # y-displacement of grid

#Base grid (unity)

x = np.arange(N)
y = np.arange(N)
X, Y = np.meshgrid(x, y)

# =========================

# Helpers

# =========================

def angle_diff(a, b):
    """
    Smallest signed difference between two angles (a - b) wrapped to [-pi, pi].
    """
    d = a - b
    return (d + np.pi) % (2 * np.pi) - np.pi

# =========================

# Genesis + Emergent Second Field update

# =========================

def update_genesis(theta, phi, tau, ux, uy, alpha, gamma, kappa, lam):
    """
    One update step:
    - theta: primary orientation
    - phi:   secondary/emergent orientation
    - tau:   tension/distinction
    - ux,uy: geometry displacement
    """
    # ---------- Primary field neighbor coupling ----------
    up    = np.roll(theta, -1, axis=0)
    down  = np.roll(theta,  1, axis=0)
    left  = np.roll(theta, -1, axis=1)
    right = np.roll(theta,  1, axis=1)

    dtheta = (
        np.sin(up - theta) +
        np.sin(down - theta) +
        np.sin(left - theta) +
        np.sin(right - theta)
    )

    # ---------- Tension from primary gradients ----------
    grad = np.abs(dtheta)
    tau = (1.0 - decay_tau) * tau + gamma * grad

    # ---------- Geometry displacement from tension + primary ----------
    ux = ux + kappa * tau * np.cos(theta)
    uy = uy + kappa * tau * np.sin(theta)

    # ---------- Secondary field dynamics ----------
    # Neighbor coupling for phi (local smoothness)
    up_p    = np.roll(phi, -1, axis=0)
    down_p  = np.roll(phi,  1, axis=0)
    left_p  = np.roll(phi, -1, axis=1)
    right_p = np.roll(phi,  1, axis=1)

    dphi_neighbors = (
        np.sin(up_p - phi) +
        np.sin(down_p - phi) +
        np.sin(left_p - phi) +
        np.sin(right_p - phi)
    )

    # Emergent "target" orientation: roughly orthogonal to theta where tension is high
    phi_target = theta + 0.5 * np.pi  # 90 degrees ahead
    diff_to_target = angle_diff(phi_target, phi)

    # Secondary field update:
    #  - smooth via its own neighbors
    #  - pushed toward orthogonal-to-theta where tau is large
    #  - gently pulled back toward theta baseline in low-tau areas
    phi = phi + dt * (
        0.3 * dphi_neighbors +             # local coherence
        lam * tau * diff_to_target -       # emergence from tension
        decay_phi * angle_diff(phi, theta) # relax toward primary when quiet
    )
    phi = np.mod(phi, 2 * np.pi)

    # ---------- Primary field update (feels tau, but not phi directly) ----------
    theta = theta + dt * (alpha * dtheta + 0.1 * tau)
    theta = np.mod(theta, 2 * np.pi)

    return theta, phi, tau, ux, uy

# =========================

# Matplotlib setup

# =========================

fig, ax = plt.subplots()
plt.subplots_adjust(bottom=0.3)

# Initial arrow directions

U1 = np.cos(theta)
V1 = np.sin(theta)

U2 = np.cos(phi)
V2 = np.sin(phi)

positions = np.c_[X.ravel(), Y.ravel()]

# Primary field quiver (larger, default color)

quiv1 = ax.quiver(positions[:, 0], positions[:, 1],
U1.ravel(), V1.ravel(),
pivot='mid', scale=40, width=0.003)

# Secondary field quiver (smaller, red)

quiv2 = ax.quiver(positions[:, 0], positions[:, 1],
U2.ravel(), V2.ravel(),
pivot='mid', scale=60, width=0.0015, color='tab:red')

ax.set_aspect('equal')
ax.set_xlim(-2, N + 2)
ax.set_ylim(-2, N + 2)
ax.set_xticks([])
ax.set_yticks([])
ax.set_title(
"Genesis Dash Grid v2 — Emergent Second Field\n"
"Blue: primary θ, Red: emergent φ | Click to disturb"
)

# Sliders

ax_alpha  = fig.add_axes([0.15, 0.20, 0.7, 0.03])
ax_gamma  = fig.add_axes([0.15, 0.15, 0.7, 0.03])
ax_kappa  = fig.add_axes([0.15, 0.10, 0.7, 0.03])
ax_lambda = fig.add_axes([0.15, 0.05, 0.7, 0.03])

slider_alpha  = Slider(ax_alpha,  "α Align",     0.0, 1.0,  valinit=alpha0)
slider_gamma  = Slider(ax_gamma,  "γ Tension",   0.0, 1.5,  valinit=gamma0)
slider_kappa  = Slider(ax_kappa,  "κ Geometry",  0.0, 0.1,  valinit=kappa0)
slider_lambda = Slider(ax_lambda, "λ Emergence", 0.0, 1.5,  valinit=lambda0)

# =========================

# Mouse interaction

# =========================

def on_click(event):
    global theta, phi
    if event.inaxes != ax:
        return
    if event.xdata is None or event.ydata is None:
        return

    i = int(round(event.ydata))
    j = int(round(event.xdata))

    if 0 <= i < N and 0 <= j < N:
        # perturb primary field (and lightly seed secondary) in a local patch
        for a in range(-click_radius, click_radius + 1):
            for b in range(-click_radius, click_radius + 1):
                ii = i + a
                jj = j + b
                if 0 <= ii < N and 0 <= jj < N:
                    theta[ii, jj] += np.pi * (np.random.rand() - 0.5)
                    phi[ii, jj]   += 0.5 * np.pi * (np.random.rand() - 0.5)

fig.canvas.mpl_connect("button_press_event", on_click)

# =========================

# Animation loop

# =========================

def animate(frame):
    global theta, phi, tau, ux, uy

    alpha  = slider_alpha.val
    gamma  = slider_gamma.val
    kappa  = slider_kappa.val
    lam    = slider_lambda.val

    theta, phi, tau, ux, uy = update_genesis(theta, phi, tau, ux, uy,
                                             alpha, gamma, kappa, lam)

    # Update directions
    U1 = np.cos(theta).ravel()
    V1 = np.sin(theta).ravel()
    quiv1.set_UVC(U1, V1)

    U2 = np.cos(phi).ravel()
    V2 = np.sin(phi).ravel()
    quiv2.set_UVC(U2, V2)

    # Update positions using displaced grid
    new_positions = np.c_[(X + ux).ravel(), (Y + uy).ravel()]
    quiv1.set_offsets(new_positions)
    quiv2.set_offsets(new_positions)

    return quiv1, quiv2

anim = FuncAnimation(fig, animate, interval=30, blit=False)

if __name__ == "__main__":
    plt.show()