#run_visual_test.py

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..', 'src')))

import numpy as np
import matplotlib.pyplot as plt

from genesis_scheme.engine.genesis_base_engine import Field, tension, step

def make_unity_field(shape=(128, 128), u0=0.0):
    """
    Create a Unity Field with constant value u0.
    """
    F0 = np.full(shape, u0, dtype=float)
    return Field(F0, u0=u0)

def add_local_tension(field: Field, radius: int = 2, amplitude: float = 1.5):
    """
    Seed a circular bump in the center of the unity field.
    """
    H, W = field.shape
    cy, cx = H // 2, W // 2

    Y, X = np.ogrid[:H, :W]
    mask = (X - cx)**2 + (Y - cy)**2 <= radius**2

    F_new = field.F.copy()
    F_new[mask] += amplitude
    return Field(F_new, u0=field.u0)

def main():
    # --- Init Unity Field ---
    field = make_unity_field(shape=(128, 128), u0=0.0)

    # --- Apply Tension ---
    field = add_local_tension(field, radius=10, amplitude=0.7)

    # --- Genesis parameters ---
    alpha = 0.7   # contractive
    beta  = 0.05  # expansive
    gamma = 0.1   # nonlinear coupling
    dt    = 0.1   # timestep

    # tension tracker
    T_prev = tension(field)
    print(f"t = 0, T = {T_prev:.6f}")

    # --- plotting setup ---
    plt.ion()
    fig, ax = plt.subplots()
    im = ax.imshow(field.F, cmap="viridis", origin="lower")
    ax.set_title(f"t = 0, T = {T_prev:.6f}")
    plt.colorbar(im, ax=ax)

    num_steps = 10000

    for t in range(1, num_steps + 1):

        # evolve one time-step
        field = step(field, alpha=alpha, beta=beta, gamma=gamma, dt=dt)

        # compute tension + tension change
        T_curr = tension(field)
        dT = T_curr - T_prev

        # early + milestone logging
        if t <= 500 or t % 500 == 0:
            print(f"t = {t:5d}, T = {T_curr:12.6f}, dT = {dT:.6e}")

        # update previous tension
        T_prev = T_curr

        # update visualization every 2 frames
        if t % 2 == 0:
            im.set_data(field.F)
            ax.set_title(f"t = {t}, T = {T_curr:.6f}, dT = {dT:.2e}")
            plt.pause(0.0001)

        # optional verbose logging
        if t % 10 == 0:
            print(f"t = {t:4d}, T = {T_curr:.6f}, dT = {dT:.6e}")

    plt.ioff()
    plt.show()

if __name__ == "__main__":
    main()