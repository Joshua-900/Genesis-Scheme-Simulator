import numpy as np
import matplotlib.pyplot as plt

#-----------------------------
# Parameters
#-----------------------------

GRID_SIZE = 200       # size of the grid (GRID_SIZE x GRID_SIZE)
ALPHA = 1.2 #0.2           # strength of smoothing (form / unity-restoring)
BETA = 0.8            # strength of nonlinear push (force / tension-amplifying)
DT = 0.01 # 0.1             # time step factor (keep small for stability)
STEPS_PER_FRAME = 2   # how many updates per visual refresh

#Seed parameters

CENTER_RADIUS = 10    # radius of central perturbation
SEED_AMPLITUDE = 0.5  # how strong the central seed is
NOISE_SCALE = 0.02    # how much random noise to add initially

#-----------------------------
# Helper: Laplacian (periodic boundary)
#-----------------------------

def laplacian(u):
    """
    Discrete Laplacian with periodic boundary conditions.
    """
    return (
        np.roll(u, 1, axis=0)
        + np.roll(u, -1, axis=0)
        + np.roll(u, 1, axis=1)
        + np.roll(u, -1, axis=1)
        - 4 * u
    )

#-----------------------------
# Initialize field (Unity + Tension)
#-----------------------------

def init_field():
    # Start at unity: all zeros (uniform state)
    u = np.zeros((GRID_SIZE, GRID_SIZE), dtype=np.float32)

    # Add small random noise everywhere (soft tension)
    u += NOISE_SCALE * np.random.randn(GRID_SIZE, GRID_SIZE).astype(np.float32)

    # Add a central circular seed (stronger localized tension)
    cx, cy = GRID_SIZE // 2, GRID_SIZE // 2
    y, x = np.ogrid[:GRID_SIZE, :GRID_SIZE]
    mask = (x - cx) ** 2 + (y - cy) ** 2 <= CENTER_RADIUS ** 2
    u[mask] += SEED_AMPLITUDE

    # Optionally clip initial field to a safe range
    u = np.clip(u, -1.0, 1.0)

    return u

#-----------------------------
# Genesis-style update step
#-----------------------------

def step(u):
    """
    Single update step:
    u_{t+1} = u_t + alpha * Laplacian(u_t) + beta * (u_t - u_t^3)
    """
    Lu = laplacian(u)

    # Form / smoothing term
    form_term = ALPHA * Lu

    # Force / tension term (local nonlinear, saturating)
    force_term = BETA * (u - u**3)

    # Update
    u_next = u + DT * (form_term + force_term)

    # Prevent blow-up: clip to a reasonable range
    u_next = np.clip(u_next, -1.5, 1.5)

    return u_next

#-----------------------------
# Main: simple animation loop
#-----------------------------

def run():
    u = init_field()

    plt.ion()
    fig, ax = plt.subplots(figsize=(6, 6))
    im = ax.imshow(u, cmap="viridis", vmin=-1.0, vmax=1.0, interpolation="nearest")
    ax.set_title("Genesis-style Field (form vs force)")
    plt.tight_layout()

    try:
        while True:
            # Do several steps per frame to make it move visibly
            for _ in range(STEPS_PER_FRAME):
                u = step(u)

            im.set_data(u)
            # If dynamics drift, you can recompute vmin/vmax dynamically:
            # im.set_clim(u.min(), u.max())

            plt.draw()
            plt.pause(0.0001)  # control refresh rate (increase to slow down)

    except KeyboardInterrupt:
        print("Stopped by user.")

if __name__ == "__main__":
    run()