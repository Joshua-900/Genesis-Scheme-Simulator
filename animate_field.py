#animate_field.py

import matplotlib.pyplot as plt
import numpy as np

from src.genesis_scheme.field_unity import (
create_unity_field,
step_field,
FieldUnity,
)

def main():
    # create initial Unity field (200x200)
    unity: FieldUnity = create_unity_field(size=200, eps=0.02)

    plt.ion()

    fig, ax = plt.subplots()
    fig.suptitle("GenesisScheme – 2D Unity Field Emergence")

    # initial image: vmin/vmax set for visible contrast
    img = ax.imshow(
        unity.field,
        origin="lower",
        vmin=-0.5,
        vmax=1.5,
        interpolation="nearest",
    )
    ax.set_xticks([])
    ax.set_yticks([])

    for step_idx in range(1000):
        # evolve field (this is the call to step_field)
        unity = step_field(
            unity,
            diff_rate=0.10, #orig 0.10
            drive=3.5, #orig 1.5
            nonlin_strength=9.9, #orig 1.2
            dt=0.6, #orig 0.4
            noise_scale=0.0,
        )

        img.set_data(unity.field)

        # occasionally rescale color limits to show detail
        if step_idx % 50 == 0:
            data = unity.field
            lo, hi = np.percentile(data, 5), np.percentile(data, 95)
            if hi > lo:
                img.set_clim(lo, hi)

        fig.canvas.draw()
        fig.canvas.flush_events()
        plt.pause(0.03)

    plt.ioff()
    plt.show()

if __name__ == "__main__":
    main()