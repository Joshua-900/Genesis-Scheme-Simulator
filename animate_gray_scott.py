#animate_gray_scott.py

import matplotlib.pyplot as plt
import numpy as np

from src.genesis_scheme.gray_scott import (
create_gray_scott,
step_gray_scott,
GrayScottState,
)

def main():
    state: GrayScottState = create_gray_scott(size=200)

    plt.ion()

    fig, ax = plt.subplots()
    fig.suptitle("GenesisScheme – Gray-Scott Emergent Patterns (Soft View)")

    # Much gentler visualization:
    # - fixed bounds
    # - smoother interpolation
    # - muted map
    img = ax.imshow(
        state.V,
        origin="lower",
        vmin=0.0,
        vmax=0.8,
        interpolation="bilinear",  # smooths out blocky pixels
        cmap="gray",
    )
    ax.set_xticks([])
    ax.set_yticks([])

    # Run fewer visual updates, more simulation steps per frame
    while True : #for frame_idx in range(6000)
        # advance the system several internal steps per visual frame
        for _ in range(5):
            state = step_gray_scott(state, dt=1.0)

        img.set_data(state.V)

        # no dynamic rescaling -> less flashing
        fig.canvas.draw()
        fig.canvas.flush_events()
        plt.pause(0.001)   # slower refresh = calmer motion

    plt.ioff()
    plt.show()

if __name__ == "__main__":
    main()