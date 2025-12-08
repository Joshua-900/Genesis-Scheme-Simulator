# ui_matplotlib.py



# Matplotlib front-end for the modular Genesis Dash Grid.

# - Symmetric dashes (angle only DOF)

# - Compression heat background

# - Sliders for main parameters

# - Mouse click to disturb

# - Press 'd' to toggle dashes


from backend import xp
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from matplotlib.widgets import Slider
from matplotlib.collections import LineCollection

from core import GenesisState, GenesisParams, step
import rules_alignment
import rules_phase
import rules_dipoles
import rules_triads
import rules_curvature
import rules_compression
import relax

# =========================

# Config

# =========================

N  = 80      # grid size
DT = 0.05    # time step

DASH_LEN = 0.45       # dash length in grid units
CLICK_RADIUS = 2       # mouse disturbance radius (cells)

# =========================

# Init state, params, rules

# =========================

state  = GenesisState(N, DT)
params = GenesisParams()

rules = [
rules_alignment.alignment_rule,
rules_phase.phase_rule,
rules_dipoles.dipole_rule,
rules_triads.triad_rule,
rules_curvature.curvature_rule,
rules_compression.compression_rule,
relax.relaxation_rule,
]

# whether to show dashes (can toggle with 'd')

show_dashes = False

# =========================

# Dash geometry helper

# =========================

def build_dash_segments(theta):
    """
    Build symmetric dash segments from theta field.
    Returns (N^2, 2, 2) array for LineCollection: [[(x0,y0),(x1,y1)], ...]
    """
    ny, nx = theta.shape
    ys, xs = xp.mgrid[0:ny, 0:nx]

    u = xp.cos(theta)
    v = xp.sin(theta)

    half = DASH_LEN * 0.5
    x0 = xs - half * u
    y0 = ys - half * v
    x1 = xs + half * u
    y1 = ys + half * v

    segs = xp.stack(
        [xp.stack([x0, y0], axis=-1), xp.stack([x1, y1], axis=-1)],
        axis=-2,
    )
    return segs.reshape(-1, 2, 2)

# =========================

# Matplotlib setup

# =========================

fig, ax = plt.subplots(figsize=(7, 7))
plt.subplots_adjust(bottom=0.30)

ax.set_aspect("equal")
ax.set_xlim(-1, N)
ax.set_ylim(-1, N)
ax.invert_yaxis()
ax.set_xticks([])
ax.set_yticks([])

title = ax.set_title(
"Genesis Dash Grid — Phase + Dipoles + Triads + Curvature + Compression\n"
"Symmetric dashes, compression heat; click to disturb (press 'd' to toggle dashes)",
fontsize=10,
)

# Background: compression field (start all zeros)

comp_img = ax.imshow(
state.C,
cmap="Greys_r",      # high compression = dark
origin="upper",
interpolation="bilinear",
extent=(-0.5, N - 0.5, -0.5, N - 0.5),
vmin=0.0,
vmax=1.0,
alpha=0.85,
)

# Initial dash segments

init_segs = build_dash_segments(state.theta)
dashes = LineCollection(
init_segs,
colors="black",
linewidths=0.5,
alpha=0.85,
)
ax.add_collection(dashes)

# =========================

# Sliders

# =========================

slider_defs = [
("alpha",  0.0, 1.0,  params.alpha,  "Align α"),
("gamma",  0.0, 0.2,  params.gamma,  "Tension γ"),
("kappa",  0.0, 0.05, params.kappa,  "Geometry κ"),
("phase",  0.0, 2.0,  params.phase,  "Phase"),
("dipole", 0.0, 1.5,  params.dipole, "Dipoles"),
("triads", 0.0, 2.0,  params.triads, "Triads"),
("curv",   0.0, 2.0,  params.curv,   "Curvature"),
]

slider_objs = {}
bottom = 0.28
height = 0.022
spacing = 0.028

for idx, (name, vmin, vmax, v0, label) in enumerate(slider_defs):
    ax_slider = fig.add_axes([0.15, bottom - idx * spacing, 0.7, height])
    slider = Slider(ax_slider, label, vmin, vmax, valinit=v0)
    slider_objs[name] = slider

def on_slider_change(val):
    params.alpha  = slider_objs["alpha"].val
    params.gamma  = slider_objs["gamma"].val
    params.kappa  = slider_objs["kappa"].val
    params.phase  = slider_objs["phase"].val
    params.dipole = slider_objs["dipole"].val
    params.triads = slider_objs["triads"].val
    params.curv   = slider_objs["curv"].val

for s in slider_objs.values():
    s.on_changed(on_slider_change)

# =========================

# Mouse + keyboard

# =========================

def on_click(event):
    if event.inaxes is not ax:
        return
    if event.xdata is None or event.ydata is None:
        return

    j = int(round(event.xdata))
    i = int(round(event.ydata))

    if not (0 <= i < N and 0 <= j < N):
        return

    for di in range(-CLICK_RADIUS, CLICK_RADIUS + 1):
        for dj in range(-CLICK_RADIUS, CLICK_RADIUS + 1):
            ii = i + di
            jj = j + dj
            if 0 <= ii < N and 0 <= jj < N:
                # random angular kick
                state.theta[ii, jj] += xp.pi * (xp.random.rand() - 0.5)

def on_key(event):
    global show_dashes
    if event.key == "d":
        show_dashes = not show_dashes
        dashes.set_visible(show_dashes)
        fig.canvas.draw_idle()

    fig.canvas.mpl_connect("button_press_event", on_click)
    fig.canvas.mpl_connect("key_press_event", on_key)

# =========================

# Animation

# =========================

def animate(frame):
    # advance the Genesis engine
    step(state, params, rules)

    # light smoothing of compression for nicer blobs
    C = state.C
    C_smooth = 0.25 * (
        xp.roll(C, 1, 0) + xp.roll(C, -1, 0) +
        xp.roll(C, 1, 1) + xp.roll(C, -1, 1)
    )
    state.C = xp.clip(C_smooth, 0.0, 1.0)

    comp_img.set_data(state.C)

    # update dash geometry if visible
    segs = build_dash_segments(state.theta)
    dashes.set_segments(segs)

    return (comp_img, dashes)

if __name__ == "__main__":
    anim = FuncAnimation(fig, animate, interval=30, blit=False, cache_frame_data=False)
    plt.show()