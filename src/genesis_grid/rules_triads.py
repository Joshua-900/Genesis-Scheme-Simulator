# rules_triads.py

import numpy as np
from core import angle_diff   # or wherever you defined it

# predefine the triad templates once

_TRIADS = [
    ((0, 0), (1, 0), (0, 1),  (0.25 * np.pi, 0.0,        0.5 * np.pi)),
    ((0, 0), (-1, 0), (0, 1),  (0.75 * np.pi, np.pi,      0.5 * np.pi)),
    ((0, 0), (1, 0), (0, -1), (-0.25 * np.pi, 0.0,      -0.5 * np.pi)),
    ((0, 0), (-1, 0), (0, -1), (-0.75 * np.pi, np.pi,    -0.5 * np.pi)),
]

_TRI_SIGMA2 = (0.4 ** 2)     # same as before

def triad_rule(state, params, extra):
    """
    Triadic alignment rule:
    - encourages local triples to approximate target angles.
    """
    if params.triads == 0.0:
        return {"torque": 0.0}

    N     = state.N
    theta = state.theta

    tri_torque = np.zeros_like(theta)

    for i in range(N):
        for j in range(N):
            for (o0, o1, o2, angs) in _TRIADS:
                i0, j0 = i + o0[0], j + o0[1]
                i1, j1 = i + o1[0], j + o1[1]
                i2, j2 = i + o2[0], j + o2[1]
                if not (0 <= i0 < N and 0 <= j0 < N and
                        0 <= i1 < N and 0 <= j1 < N and
                        0 <= i2 < N and 0 <= j2 < N):
                    continue

                th0 = theta[i0, j0]
                th1 = theta[i1, j1]
                th2 = theta[i2, j2]

                a0, a1, a2 = angs

                d0 = angle_diff(th0, a0)
                d1 = angle_diff(th1, a1)
                d2 = angle_diff(th2, a2)

                sq_err = d0*d0 + d1*d1 + d2*d2
                S = np.exp(-sq_err / _TRI_SIGMA2)
                if S < 1e-3:
                    continue

                tri_torque[i0, j0] += params.triads * S * np.sin(a0 - th0)
                tri_torque[i1, j1] += params.triads * S * np.sin(a1 - th1)
                tri_torque[i2, j2] += params.triads * S * np.sin(a2 - th2)

    return {"torque": tri_torque}