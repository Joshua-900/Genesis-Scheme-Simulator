# ui_matplotlib.py



# Matplotlib front-end for the modular Genesis Dash Grid.

# - Symmetric dashes (orientation-only DOF)

# - Compression heat background

# - Optional contour overlay from compression

# - Sliders for main parameters

# - Mouse click to disturb

# - Keys:

# 'd' = toggle dashes

# 'v' = cycle view modes


from .backend import xp
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from matplotlib.widgets import Slider
from matplotlib.collections import LineCollection

from .core import GenesisState, GenesisParams, step
from . import rules_alignment
from . import rules_phase
from . import rules_dipoles
from . import rules_triads
from . import rules_curvature
from . import rules_compression
from . import relax

# =========================

# Config

# =========================

N  = 80      # grid size
DT = 0.05    # time step

DASH_LEN     = 0.45   # dash length in grid units
CLICK_RADIUS = 2      # mouse disturbance radius (cells)

# start with dashes visible?

show_dashes = False

# view / render mode:

# 0 = compression only

# 1 = compression + dashes

# 2 = compression + dashes + compression contours

render_mode = 2

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

ax.set_title(
"Genesis Dash Grid — Phase + Dipoles + Triads + Curvature + Compression\n"
"Symmetric dashes, compression heat; click to disturb ('d' dashes, 'v' view)",
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

# respect initial flags

dashes.set_visible(show_dashes and render_mode in (1, 2))

# contour artists (for mode 2)

contour_artists = []

def set_render_mode(new_mode: int):
    """Update global render mode and adjust alphas/visibility."""
    global render_mode
    render_mode = new_mode % 3  # just in case

    # adjust background emphasis by mode
    if render_mode == 0:
        comp_img.set_alpha(0.95)
    elif render_mode == 1:
        comp_img.set_alpha(0.85)
    else:  # mode 2
        comp_img.set_alpha(0.70)

    # dashes only meaningful in modes 1 and 2
    dashes.set_visible(show_dashes and render_mode in (1, 2))

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
                state.theta[ii, jj] += xp.pi * (xp.random.rand() - 0.5)

def on_key(event):
    global show_dashes
    if event.key == "d":
        # toggle dashes, but only show them in modes 1 and 2
        show_dashes = not show_dashes
        dashes.set_visible(show_dashes and render_mode in (1, 2))
        fig.canvas.draw_idle()
    elif event.key == "v":
        # cycle view modes
        set_render_mode(render_mode + 1)
        fig.canvas.draw_idle()

fig.canvas.mpl_connect("button_press_event", on_click)
fig.canvas.mpl_connect("key_press_event", on_key)

# =========================

# Animation

# =========================

def animate(frame):
    global contour_artists

    # advance the Genesis engine
    step(state, params, rules)

    # update compression background
    comp_img.set_data(state.C)

    # update dash geometry
    segs = build_dash_segments(state.theta)
    dashes.set_segments(segs)

    # handle contours for mode 2
    if render_mode == 2:
        # remove old contours
        for coll in contour_artists:
            coll.remove()
        # draw new ones from compression field
        cs = ax.contour(
            state.X,
            state.Y,
            state.C,
            levels=10,
            colors="black",
            linewidths=0.4,
            alpha=0.9,
        )
        contour_artists = getattr(cs, 'artists', getattr(cs, 'collections', []))
    else:
        # if leaving contour mode, clear any existing contours
        if contour_artists:
            for coll in contour_artists:
                coll.remove()
            contour_artists = []

    artists = [comp_img, dashes] + contour_artists
    return artists

# initialize render mode visuals

set_render_mode(render_mode)

if __name__ == "__main__":
    anim = FuncAnimation(fig, animate, interval=30, blit=False, cache_frame_data=False)
    plt.show()