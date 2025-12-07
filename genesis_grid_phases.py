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

decay_tau = 0.02
click_radius = 2

# =========================

# State fields

# =========================

theta = np.random.rand(N, N) * 2 * np.pi   # ONLY true DOF
tau   = np.zeros((N, N))                   # tension field (driven by theta)
ux    = np.zeros((N, N))                   # x-displacement
uy    = np.zeros((N, N))                   # y-displacement

x = np.arange(N)
y = np.arange(N)
X, Y = np.meshgrid(x, y)

# =========================

# Helpers

# =========================

def update_genesis(theta, tau, ux, uy, alpha, gamma, kappa, well_strength):
    """
    One update step:
    theta: orientation field
    tau:   tension (from theta gradients)
    ux,uy: geometry
    well_strength: strength of 4-well potential that favors 4 angles
    """
    # Neighbor coupling (alignment)
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

    # Tension from gradients
    grad = np.abs(dtheta_align)
    tau = (1.0 - decay_tau) * tau + gamma * grad

    # Geometry displacement: tension pushes along orientation
    ux = ux + kappa * tau * np.cos(theta)
    uy = uy + kappa * tau * np.sin(theta)

    # === NEW: multi-well "phase" potential ===
    # V(theta) = -cos(4 theta)
    # force toward minima = -dV/dtheta = -4 sin(4 theta)
    phase_force = -well_strength * np.sin(4.0 * theta)

    # Total orientation update
    dtheta_total = alpha * dtheta_align + 0.1 * tau + phase_force
    theta = theta + dt * dtheta_total
    theta = np.mod(theta, 2.0 * np.pi)

    return theta, tau, ux, uy


# =========================

# Matplotlib setup

# =========================

fig, ax = plt.subplots()
plt.subplots_adjust(bottom=0.25)

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
"Genesis Dash Grid — 4-Phase Localization from Forces Only\n"
"Color = phase (which energy well), click to disturb"
)

# Sliders

ax_alpha = fig.add_axes([0.15, 0.15, 0.7, 0.03])
ax_gamma = fig.add_axes([0.15, 0.10, 0.7, 0.03])
ax_kappa = fig.add_axes([0.15, 0.05, 0.7, 0.03])
ax_well  = fig.add_axes([0.15, 0.00, 0.7, 0.03])

slider_alpha = Slider(ax_alpha, "α Align",   0.0, 1.0,  valinit=alpha0)
slider_gamma = Slider(ax_gamma, "γ Tension", 0.0, 1.5,  valinit=gamma0)
slider_kappa = Slider(ax_kappa, "κ Geometry",0.0, 0.1,  valinit=kappa0)
slider_well  = Slider(ax_well,  "Phase Strength", 0.0, 2.0, valinit=well0)

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

    alpha = slider_alpha.val
    gamma = slider_gamma.val
    kappa = slider_kappa.val
    well_strength = slider_well.val

    theta, tau, ux, uy = update_genesis(theta, tau, ux, uy,
                                        alpha, gamma, kappa, well_strength)

    # Directions
    U = np.cos(theta).ravel()
    V = np.sin(theta).ravel()
    quiv.set_UVC(U, V)

    # Positions (deformed grid)
    new_positions = np.c_[(X + ux).ravel(), (Y + uy).ravel()]
    quiv.set_offsets(new_positions)

    # Color by which of 4 wells theta is nearest to
    # wells at 0, pi/2, pi, 3pi/2
    # shift by pi/4 then bucket in steps of pi/2
    indices = ((theta + 0.25 * np.pi) // (0.5 * np.pi)).astype(int) % 4
    colors = cm.tab10((indices.ravel() / 4.0))
    quiv.set_color(colors)

    return quiv,
anim = FuncAnimation(fig, animate, interval=30, blit=False)

if __name__ == "__main__":
    plt.show()