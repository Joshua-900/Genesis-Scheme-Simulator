import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from matplotlib.widgets import Slider

#-----------------------------
# Parameters
#-----------------------------

N = 30              # grid size (NxN)
alpha_init = 0.2    # initial coupling strength
dt = 1.0            # time step for updates
perturb_strength = np.pi / 2  # how strong a mouse click perturbation is

#-----------------------------
# State: orientation field θ[i,j]
#-----------------------------

theta = np.random.rand(N, N) * 2 * np.pi

#Grid coordinates for plotting

x = np.arange(N)
y = np.arange(N)
X, Y = np.meshgrid(x, y)

#-----------------------------
# Update rule
#-----------------------------

def update_theta(theta, alpha):
    """
    Simple neighbor-alignment dynamics:
    θ_t+1 = θ_t + α * sum_neighbors sin(θ_neighbor - θ_here)
    Periodic boundary conditions via np.roll.
    """
    # Neighbors via periodic boundary conditions
    up    = np.roll(theta, -1, axis=0)
    down  = np.roll(theta,  1, axis=0)
    left  = np.roll(theta, -1, axis=1)
    right = np.roll(theta,  1, axis=1)

    # "Tug" from neighbors
    dtheta = (
        np.sin(up    - theta) +
        np.sin(down  - theta) +
        np.sin(left  - theta) +
        np.sin(right - theta)
    )

    # Update and wrap back into [0, 2π)
    theta_new = theta + alpha * dt * dtheta
    theta_new = (theta_new + 2 * np.pi) % (2 * np.pi)
    return theta_new

#-----------------------------
# Matplotlib setup
#-----------------------------

plt.style.use("default")

fig, ax = plt.subplots()
plt.subplots_adjust(bottom=0.15)  # leave room for slider

#Initial direction vectors for quiver

U = np.cos(theta)
V = np.sin(theta)

quiver = ax.quiver(X, Y, U, V, pivot='middle', scale=40)

ax.set_aspect('equal')
ax.set_xlim(-1, N)
ax.set_ylim(-1, N)
ax.set_xticks([])
ax.set_yticks([])
ax.set_title("Interactive Dash Grid (click to disturb, 'r' to randomize)")

#Slider for alpha (coupling strength)

slider_ax = fig.add_axes([0.2, 0.05, 0.6, 0.03])
alpha_slider = Slider(slider_ax, 'Coupling α', 0.0, 1.0, valinit=alpha_init)

#-----------------------------
# Interaction: mouse + keyboard
#-----------------------------

def on_click(event):
    global theta
    if event.inaxes != ax:
        return
    # Find nearest grid point
    i = int(round(event.ydata))
    j = int(round(event.xdata))
    if 0 <= i < N and 0 <= j < N:
        # Add a local perturbation
        theta[i, j] += perturb_strength * (2 * np.random.rand() - 1)
        theta[i, j] = (theta[i, j] + 2 * np.pi) % (2 * np.pi)

def on_key(event):
    global theta
    if event.key == 'r':
        # Randomize the whole field
        theta = np.random.rand(N, N) * 2 * np.pi

fig.canvas.mpl_connect('button_press_event', on_click)
fig.canvas.mpl_connect('key_press_event', on_key)

#-----------------------------
# Animation loop
#-----------------------------

def animate(frame):
    global theta
    alpha = alpha_slider.val  # current coupling from slider
    theta = update_theta(theta, alpha)

    U = np.cos(theta)
    V = np.sin(theta)

    quiver.set_UVC(U, V)
    return quiver,

anim = FuncAnimation(fig, animate, interval=30, blit=False)

plt.show()