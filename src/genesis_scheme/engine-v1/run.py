#run.py
import numpy as np
import matplotlib.pyplot as plt

from field2 import Field2
from tension import tension_norm
from ops_grayscott import step_gs,step_gs_genesis
from genesis_signature import tension_signature
from genesis_logging import save_tension_csv

def make_unity(shape=(512, 512)) -> Field2:
    # Baseline: U = 1, V = 0
    U = np.ones(shape, float)
    V = np.zeros(shape, float)
    return Field2(U, V)

def add_central_patch(field: Field2,
r: int = 20,
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

    # # Duality parameters (known ‘worms’ regime)
    # Du, Dv = 0.11, 0.066 #0.16, 0.08
    # F, k   = 0.0210000999,0.055396396396  #0.022, 0.051
    # dt     = 1.0 # 1.0
    # steps  = 50000

    # Duality parameters (known ‘worms’ regime)
    Du, Dv = 0.5, 0.0106
    F,k = 0.018, 0.061
    alpha = 0.0214         # start with NO local damping
    beta  = 0.00314       # contrast strength
    kappa = 1e-7    # very gentle global feedba
    gamma = 0.5         # nonlinear term
    dt    = 0.02
    steps = 15000

    #kappa = F * 3.14/k  # Genesis feedback strength
    #k = alpha + 3.14 * 0.5   # map Genesis params to Gray–Scott
    #F = dt * F/1.645



    #use initial tension as T0 (target)

    T_prev = tension_norm(field)
    T0 = T_prev 
    print(f"t = 0, T = {T_prev:.6f}")

    #probe1
    #--- probe one cell over time (center cell) ---
    # H, W = field.U.shape
    # i0, j0 = H // 2, W // 2          # center index

    # probe_times = [0]
    # probe_series = [field.U[i0, j0]]
    T_times = [0]
    T_series = [T_prev]
    #end probe1

    plt.ion()
    fig, ax = plt.subplots()

    # Visualize V, which tends to show clearer patterns
    im = ax.imshow(
        field.V,
        cmap="inferno",
        interpolation="bicubic",
        origin="lower",
        vmin=0.0,
        vmax=1.0,
    )
    plt.colorbar(im, ax=ax)

    for t in range(1, steps + 1):
        #field = step_genesis(field, Du=Du, Dv=Dv, F=F, k=k, dt=dt)
        field = step_gs_genesis(field, Du=Du, Dv=Dv, F=F, k=k, dt=dt, kappa=kappa, T0=T0)

        #probe 2
        #record probe

        # probe_times.append(t)
        # probe_series.append(field.U[i0, j0])
        T_curr = tension_norm(field)
        dT = T_curr - T_prev
        T_prev = T_curr

        T_times.append(t)
        T_series.append(T_curr)

        print(f"t = {t:5d}, "
              f"T = {T_curr:.6f}, dT = {dT:.3e},"
              f" V[min,max]=({field.V.min():.3f}, {field.V.max():.3f})"
              )

        #end probe 2

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
            plt.pause(0.0005)

    plt.ioff()
    plt.show()

    save_tension_csv("tension_sig_log.csv",range(len(T_series)),T_series)
                        
                           # Geneisis Signature
    sig = tension_signature(T_series)
    print(sig)

    #end signature

    #--- plot probe time series ---

    plt.figure()
    plt.plot(T_times, T_series)
    plt.title("Tension T(t)")
    plt.xlabel("t")
    plt.ylabel("T")
    plt.show()

if __name__ == "__main__":
    main()