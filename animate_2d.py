#animate_2d.py
import numpy as np
import matplotlib.pyplot as plt

from src.genesis_scheme.algebra_2d import UnityState2D, step2d

def main():
    # initial state and tension
    s0 = np.array([1.0, 0.2], dtype=float)
    t0 = 0.4
    unity = UnityState2D(s=s0, t=t0)

    plt.ion()  # interactive mode on

    fig, ax = plt.subplots()
    ax.set_aspect("equal", adjustable="box")
    ax.grid(True)

    # initial limits
    ax.set_xlim(-3, 3)
    ax.set_ylim(-3, 3)

    point, = ax.plot([], [], "o")  # single point

    for n in range(300):
        # advance one step
        unity = step2d(unity)
        x, y = unity.s

        # update point position
        point.set_data([x], [y])

        # optional: auto-rescale if it drifts
        max_abs = max(abs(x), abs(y), 3)
        ax.set_xlim(-max_abs, max_abs)
        ax.set_ylim(-max_abs, max_abs)

        fig.canvas.draw()
        fig.canvas.flush_events()
        plt.pause(0.05)  # 50 ms pause so you can see motion

    # keep window open at the end
    plt.ioff()
    plt.show()

if __name__ == "__main__":
    main()