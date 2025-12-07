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
gamma0 = 0.8    # tension gain (how strongly gradients feed tension)
kappa0 = 0.03   # geometry coupling (how much tension moves the grid)
shape0 = 0.6    # shape strength: how strongly "square-likeness" pulls angles

decay_tau = 0.02   # tension decay per step
click_radius = 2   # radius of disturbance on click

# Square motif parameters

shape_sigma = 0.7      # radians: tolerance for matching the motif
shape_sigma2 = shape_sigma ** 2

# =========================

# State fields

# =========================

theta = np.random.rand(N, N) * 2 * np.pi   # orientation field (only true DOF)
tau   = np.zeros((N, N))                   # tension / distinction field
ux    = np.zeros((N, N))                   # x-displacement of grid
uy    = np.zeros((N, N))                   # y-displacement of grid

# Base grid (unity)

x = np.arange(N)
y = np.arange(N)
X, Y = np.meshgrid(x, y)

# Square template (2x2) in absolute angle space:

#0, 90, 180, 270 degrees

square_template = np.array([
[0.0,            0.5 * np.pi],
[1.0 * np.pi,    1.5 * np.pi]
])

# =========================

# Helpers

# =========================

def angle_diff(a, b):
    """
    Smallest signed difference between angles (a - b) wrapped to [-pi, pi].
    """
    d = a - b
    return (d + np.pi) % (2 * np.pi) - np.pi

# =========================

# Genesis + Square-Attractor Update

# =========================

def update_genesis(theta, tau, ux, uy, alpha, gamma, kappa, shape_strength):
    """
    One update step:
    - theta: orientation (only dynamical DOF)
    - tau:   tension/distinction
    - ux,uy: geometry displacement
    - shape_strength: how strongly square motifs attract when already close
    Returns: theta, tau, ux, uy, square_score
    """
    # ---------- Primary neighbor coupling (alignment) ----------
    up    = np.roll(theta, -1, axis=0)
    down  = np.roll(theta,  1, axis=0)
    left  = np.roll(theta, -1, axis=1)
    right = np.roll(theta,  1, axis=1)

    dtheta_neighbors = (
        np.sin(up - theta) +
        np.sin(down - theta) +
        np.sin(left - theta) +
        np.sin(right - theta)
    )

    # ---------- Tension from primary gradients ----------
    grad = np.abs(dtheta_neighbors)
    tau = (1.0 - decay_tau) * tau + gamma * grad

    # ---------- Geometry displacement from tension + orientation ----------
    ux = ux + kappa * tau * np.cos(theta)
    uy = uy + kappa * tau * np.sin(theta)

    # ---------- Square motif forces (continuous, no locking) ----------
    extra_torque = np.zeros_like(theta)
    square_score = np.zeros_like(theta)

    # Loop over 2x2 patches
    for i in range(N - 1):
        for j in range(N - 1):
            patch = theta[i:i+2, j:j+2]

            # Difference to square template (elementwise angle diff)
            diffs = angle_diff(patch, square_template)
            sq_err = np.sum(diffs ** 2)

            # "Square-likeness" functional S in (0,1]
            S = np.exp(-sq_err / shape_sigma2)

            if S < 1e-3:
                continue  # negligible contribution

            # Apply extra torque toward the template, scaled by S
            # and accumulate square_score for visualization
            for a in range(2):
                for b in range(2):
                    ii = i + a
                    jj = j + b
                    delta = angle_diff(square_template[a, b], theta[ii, jj])
                    extra_torque[ii, jj] += shape_strength * S * delta

                    # Visual "square strength" at cell = max over any patch that covers it
                    if S > square_score[ii, jj]:
                        square_score[ii, jj] = S

    # ---------- Total orientation update ----------
    dtheta_total = dtheta_neighbors + extra_torque

    theta = theta + dt * (alpha * dtheta_total + 0.1 * tau)
    theta = np.mod(theta, 2 * np.pi)

    # Clamp square_score to [0,1]
    square_score = np.clip(square_score, 0.0, 1.0)

    return theta, tau, ux, uy, square_score

# =========================

# Matplotlib setup

# =========================

fig, ax = plt.subplots()
plt.subplots_adjust(bottom=0.25)

# Initial arrow directions

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
"Genesis Dash Grid — Square Motifs from Forces Only\n"
"Brightness ≈ square-likeness (2x2), click to disturb"
)

# Sliders

ax_alpha = fig.add_axes([0.15, 0.15, 0.7, 0.03])
ax_gamma = fig.add_axes([0.15, 0.10, 0.7, 0.03])
ax_kappa = fig.add_axes([0.15, 0.05, 0.7, 0.03])
ax_shape = fig.add_axes([0.15, 0.00, 0.7, 0.03])

slider_alpha = Slider(ax_alpha, "α Align",   0.0, 1.0,  valinit=alpha0)
slider_gamma = Slider(ax_gamma, "γ Tension", 0.0, 1.5,  valinit=gamma0)
slider_kappa = Slider(ax_kappa, "κ Geometry",0.0, 0.1,  valinit=kappa0)
slider_shape = Slider(ax_shape, "Shape Strength", 0.0, 1.5, valinit=shape0)

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

cmap = cm.plasma  # colormap for square-likeness intensity

def animate(frame):
    global theta, tau, ux, uy

    alpha = slider_alpha.val
    gamma = slider_gamma.val
    kappa = slider_kappa.val
    shape_strength = slider_shape.val

    theta, tau, ux, uy, square_score = update_genesis(
        theta, tau, ux, uy,
        alpha, gamma, kappa, shape_strength
    )

    # Update arrow directions
    U = np.cos(theta).ravel()
    V = np.sin(theta).ravel()
    quiv.set_UVC(U, V)

    # Update positions using displaced grid
    new_positions = np.c_[(X + ux).ravel(), (Y + uy).ravel()]
    quiv.set_offsets(new_positions)

    # Color intensity from square_score (0..1)
    colors = cmap(square_score.ravel())
    quiv.set_color(colors)

    return quiv,
anim = FuncAnimation(fig, animate, interval=30, blit=False)

if __name__ == "__main__":
    plt.show()