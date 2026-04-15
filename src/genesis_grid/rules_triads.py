# rules_triads.py
#
# 3-body triangular cohesion — vectorized with numpy rolls.
# Each L-shaped triad template is evaluated across the entire grid at once.

from .backend import xp
from .core import angle_diff

# Triad templates: (offset_0, offset_1, offset_2, (target_angle_0, target_angle_1, target_angle_2))
# Each is an L-shaped triple of cells with preferred orientation angles.
_TRIADS = [
    ((0, 0), (1, 0), (0, 1),  (0.25 * xp.pi, 0.0,        0.5 * xp.pi)),    # NE
    ((0, 0), (-1, 0), (0, 1),  (0.75 * xp.pi, xp.pi,      0.5 * xp.pi)),   # NW
    ((0, 0), (1, 0), (0, -1), (-0.25 * xp.pi, 0.0,      -0.5 * xp.pi)),    # SE
    ((0, 0), (-1, 0), (0, -1), (-0.75 * xp.pi, xp.pi,   -0.5 * xp.pi)),   # SW
]


def triad_rule(state, params, extra):
    if params.triads == 0.0:
        return {"torque": 0.0}

    theta = state.theta
    tri_sigma2 = params.tri_sigma2
    strength = params.triads

    tri_torque = xp.zeros_like(theta)

    for (o0, o1, o2, angs) in _TRIADS:
        a0, a1, a2 = angs

        # Roll theta to align each triad member with cell (i,j)
        th0 = xp.roll(xp.roll(theta, -o0[0], axis=0), -o0[1], axis=1)
        th1 = xp.roll(xp.roll(theta, -o1[0], axis=0), -o1[1], axis=1)
        th2 = xp.roll(xp.roll(theta, -o2[0], axis=0), -o2[1], axis=1)

        # Angle errors for all cells at once
        d0 = angle_diff(th0, a0)
        d1 = angle_diff(th1, a1)
        d2 = angle_diff(th2, a2)

        # Triad coherence score (Gaussian)
        sq_err = d0 * d0 + d1 * d1 + d2 * d2
        S = xp.exp(-sq_err / tri_sigma2)

        # Mask out negligible contributions
        mask = S > 1e-3

        # Torque on each member, rolled back to its home position
        t0 = strength * S * xp.sin(a0 - th0) * mask
        t1 = strength * S * xp.sin(a1 - th1) * mask
        t2 = strength * S * xp.sin(a2 - th2) * mask

        tri_torque += xp.roll(xp.roll(t0, o0[0], axis=0), o0[1], axis=1)
        tri_torque += xp.roll(xp.roll(t1, o1[0], axis=0), o1[1], axis=1)
        tri_torque += xp.roll(xp.roll(t2, o2[0], axis=0), o2[1], axis=1)

    extra["tri_torque"] = tri_torque
    return {"torque": tri_torque}
