import numpy as np
import matplotlib.pyplot as plt

from field2 import Field2
from ops import step, tension_norm

def make_unity_field2(shape=(192, 192), u0=0.0, v0=0.0):
    """
    2-channel unity field:
    U = u0 everywhere
    V = v0 everywhere
    """
    H, W = shape
    U = np.full((H, W), u0, dtype=float)
    V = np.full((H, W), v0, dtype=float)
    return Field2(U, V, u0=u0, v0=v0)

def add_local_tension2(field: Field2, radius=10, amp_u=0.5, amp_v=0.0):
    """
    Seed a circular bump in the center of the field.
    """
    U, V = field.U.copy(), field.V.copy()
    H, W = U.shape

    cy, cx = H // 2, W // 2
    Y, X = np.ogrid[:H, :W]
    mask = (X - cx)**2 + (Y - cy)**2 <= radius**2

    U[mask] += amp_u
    V[mask] += amp_v

    return Field2(U, V, u0=field.u0, v0=field.v0)

def main():

    print(">>> RUNNING CLEAN TWO-FIELD TEST <<<")

    # -----------------------------
    # Init unity + tension
    # -----------------------------
    field = make_unity_field2(shape=(192, 192), u0=0.0, v0=0.0)
    field = add_local_tension2(field, radius=16, amp_u=0.80, amp_v=0.00)

    # params
    dt    = 0.20
    Du    = 0.16      # diffusion for U
    Dv    = 0.08      # diffusion for V
    alpha = 1.00      # reaction multiplier U
    beta  = 1.00      # reaction multiplier V
    gamma = 0.00      # nonlinear cross-term (disabled for now)

    # -----------------------------
    # Tension probe
    # -----------------------------
    T_prev = tension_norm(field)
    print(f"t = 0, T = {T_prev:.6f}")

    # -----------------------------
    # Time-series probe
    # -----------------------------
    H, W = field.U.shape
    i0, j0 = H // 2, W // 2     # probe the center cell

    probe_series = []
    probe_times = []

    probe_series.append(field.U[i0, j0])
    probe_times.append(0)

    # -----------------------------
    # plotting setup
    # -----------------------------
    plt.ion()
    fig, ax = plt.subplots()
    im = ax.imshow(field.U, cmap='magma', origin='lower', vmin=0, vmax=1)
    ax.set_title(f"t = 0, T = {T_prev:.6f}")
    plt.colorbar(im, ax=ax)

    # -----------------------------
    # main loop
    # -----------------------------
    num_steps = 50000

    for t in range(1, num_steps + 1):

        # step update
        field = step_twofield(field,
                            dt=dt, Du=Du, Dv=Dv,
                            alpha=alpha, beta=beta, gamma=gamma)

        # tension measurement
        T_curr = tension_norm(field)
        dT = T_curr - T_prev
        T_prev = T_curr

        # record probe
        probe_series.append(field.U[i0, j0])
        probe_times.append(t)

        # log
        if t <= 200 or t % 200 == 0:
            print(f"t = {t:5d}, T = {T_curr:.6f}, dT = {dT:.6e}")

        # plot update
        if t % 20 == 0:
            im.set_data(field.U)
            ax.set_title(f"t = {t}, T = {T_curr:.6f}, dT = {dT:.2e}")
            plt.pause(0.001)

    plt.ioff()
    plt.show()

    # -----------------------------
    # probe plot
    # -----------------------------
    plt.figure(figsize=(10, 4))
    plt.plot(probe_times, probe_series, '-', linewidth=0.8)
    plt.title("Probe time series at center cell")
    plt.xlabel("t")
    plt.ylabel("U(i0,j0)")
    plt.grid(True)
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    main()