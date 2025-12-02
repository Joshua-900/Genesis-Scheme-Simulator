#run.py
import numpy as np
import matplotlib.pyplot as plt

from field2 import Field2
from tension import tension_norm
from ops import step

def make_unity(shape=(200, 200)) -> Field2:
    # Baseline: U = 1, V = 0
    U = np.ones(shape, float)
    V = np.zeros(shape, float)
    return Field2(U, V)

def add_central_patch(field: Field2,
r: int = 10,
U_val: float = 0.50,
V_val: float = 0.25) -> Field2:
    """Seed: central square patch."""
    U = field.U.copy()
    V = field.V.copy()

    H, W = field.shape
    cy, cx = H // 2, W // 2

    U[cy - r: cy + r, cx - r: cx + r] = U_val
    V[cy - r: cy + r, cx - r: cx + r] = V_val

    return Field2(U, V)

def main():
    print(">>> RUNNING DUALITY PATTERN TEST <<<")

    field = make_unity()
    field = add_central_patch(field)

    print("initial U range:", field.U.min(), field.U.max())
    print("initial V range:", field.V.min(), field.V.max())

    # Duality parameters (known ‘worms’ regime)
    Du, Dv = 0.16, 0.08
    F, k   = 0.022, 0.051
    dt     = 1.0
    steps  = 50000

    T_prev = tension_norm(field)
    print(f"t = 0, T = {T_prev:.6f}")

    plt.ion()
    fig, ax = plt.subplots()

    # Visualize V, which tends to show clearer patterns
    im = ax.imshow(
        field.V,
        cmap="inferno",
        origin="lower",
        vmin=0.0,
        vmax=1.0,
    )
    plt.colorbar(im, ax=ax)

    for t in range(1, steps + 1):
        field = step(field, Du=Du, Dv=Dv, F=F, k=k, dt=dt)

        if t % 50 == 0:
            T_curr = tension_norm(field)
            dT = T_curr - T_prev
            T_prev = T_curr
            print(
                f"t = {t:5d}, "
                f"T = {T_curr:.6f}, dT = {dT:.3e}, "
                f"V[min,max]=({field.V.min():.3f}, {field.V.max():.3f})"
            )

        if t % 5 == 0:
            im.set_data(field.V)
            ax.set_title(f"t = {t}")
            plt.pause(0.005)

    plt.ioff()
    plt.show()

if __name__ == "__main__":
    main()