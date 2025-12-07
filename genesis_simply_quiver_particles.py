import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from matplotlib.widgets import Slider

# =========================

# Parameters

# =========================

N = 40          # grid size
dt = 0.05       # time step

alpha0 = 0.3    # neighbor alignment strength
gamma0 = 0.8    # tension gain (how strongly gradients feed tension)
kappa0 = 0.03   # geometry coupling (how much tension moves the grid)

decay_tau = 0.02   # tension decay per step
click_radius = 2   # radius of disturbance on click

# =========================

# State fields

# =========================

theta = np.random.rand(N, N) * 2 * np.pi   # orientation field
tau   = np.zeros((N, N))                   # tension / distinction field
ux    = np.zeros((N, N))                   # x-displacement of grid
uy    = np.zeros((N, N))                   # y-displacement of grid

# Base grid (unity)

x = np.arange(N)
y = np.arange(N)
X, Y = np.meshgrid(x, y)

# =========================

# Genesis update step

# =========================

def update_genesis(theta, tau, ux, uy, alpha, gamma, kappa):
    """
    One update step:
    - theta: orientation
    - tau:   tension/distinction
    - ux,uy: geometry displacement
    """
    # Neighbors (periodic boundaries)
    up    = np.roll(theta, -1, axis=0)
    down  = np.roll(theta,  1, axis=0)
    left  = np.roll(theta, -1, axis=1)
    right = np.roll(theta,  1, axis=1)

    # Orientation change from neighbor alignment
    dtheta = (
        np.sin(up - theta) +
        np.sin(down - theta) +
        np.sin(left - theta) +
        np.sin(right - theta)
    )

    # Distinction / tension grows where gradients are large
    grad = np.abs(dtheta)
    tau = (1.0 - decay_tau) * tau + gamma * grad

    # Geometry displacement: tension pushes grid along orientation direction
    ux = ux + kappa * tau * np.cos(theta)
    uy = uy + kappa * tau * np.sin(theta)

    # Update orientation, with a small direct influence from tau
    theta = theta + dt * (alpha * dtheta + 0.1 * tau)
    theta = np.mod(theta, 2 * np.pi)

    return theta, tau, ux, uy


# =========================

# Matplotlib setup

# =========================

fig, ax = plt.subplots()
plt.subplots_adjust(bottom=0.25)

# Initial arrow directions

U = np.cos(theta)
V = np.sin(theta)

# Initial positions: base grid

positions = np.c_[X.ravel(), Y.ravel()]

quiv = ax.quiver(positions[:, 0], positions[:, 1],
U.ravel(), V.ravel(),
pivot='mid', scale=40)

ax.set_aspect('equal')
ax.set_xlim(-2, N + 2)
ax.set_ylim(-2, N + 2)
ax.set_xticks([])
ax.set_yticks([])
ax.set_title("Genesis Dash Grid\nClick to disturb | α=align, γ=tension, κ=geometry")

# Sliders

ax_alpha = fig.add_axes([0.15, 0.12, 0.7, 0.03])
ax_gamma = fig.add_axes([0.15, 0.07, 0.7, 0.03])
ax_kappa = fig.add_axes([0.15, 0.02, 0.7, 0.03])

slider_alpha = Slider(ax_alpha, "α Align",   0.0, 1.0,  valinit=alpha0)
slider_gamma = Slider(ax_gamma, "γ Tension", 0.0, 1.5,  valinit=gamma0)
slider_kappa = Slider(ax_kappa, "κ Geometry",0.0, 0.1,  valinit=kappa0)

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
        # perturb a small neighborhood
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

    alpha = slider_alpha.val
    gamma = slider_gamma.val
    kappa = slider_kappa.val

    theta, tau, ux, uy = update_genesis(theta, tau, ux, uy,
                                        alpha, gamma, kappa)

    # Update arrow directions
    U = np.cos(theta).ravel()
    V = np.sin(theta).ravel()
    quiv.set_UVC(U, V)

    # Update positions using displaced grid
    new_positions = np.c_[(X + ux).ravel(), (Y + uy).ravel()]
    quiv.set_offsets(new_positions)

    return quiv,

anim = FuncAnimation(fig, animate, interval=30, blit=False)

if __name__ == "__main__":
    plt.show()