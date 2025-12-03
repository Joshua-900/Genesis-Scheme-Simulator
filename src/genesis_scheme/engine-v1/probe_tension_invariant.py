#probe_tension_invariant.py



import numpy as np
import matplotlib.pyplot as plt

from run import make_unity, add_central_patch
from ops import step
from tension import tension_norm

def main():
    # -----------------------------------
    # 1. Deterministic randomness
    # -----------------------------------
    np.random.seed(200)

    # -----------------------------------
    # 2. Create initial field (same as run.py)
    # -----------------------------------
    field = make_unity(shape=(200,200))
    field = add_central_patch(field)

    # -----------------------------------
    # 3. Parameters (copy from your run.py)
    # -----------------------------------
    Du, Dv = 0.23, 0.066
    F, k  = 0.016, 0.070
    dt    = 1.0
    steps = 25000

    # -----------------------------------
    # 4. Logging arrays
    # -----------------------------------
    T_series = []
    T_prev = tension_norm(field)

    # -----------------------------------
    # 5. Simulation loop
    # -----------------------------------
    for t in range(1, steps+1):
        field = step(field, Du=Du, Dv=Dv, F=F, k=k, dt=dt)

        T_curr = tension_norm(field)
        T_series.append(T_curr)

        # Optional printing
        if t % 500 == 0:
            print(f"t = {t:5d}, T = {T_curr:10.3f}")

        T_prev = T_curr

    # -----------------------------------
    # 6. Compute the invariant candidates
    # -----------------------------------
    T_arr = np.array(T_series)
    tail = min(2000, len(T_arr))
    T_tail = T_arr[-tail:]

    print("\n=== Genesis Tension Signature ===")
    print(f"T_mean = {T_tail.mean():.3f}")
    print(f"T_std  = {T_tail.std():.3f}")

    # -----------------------------------
    # 7. Plot
    # -----------------------------------
    plt.plot(T_series)
    plt.title("Tension T(t)")
    plt.xlabel("t")
    plt.ylabel("T")
    plt.show()

if __name__ == "__main__":
    main()