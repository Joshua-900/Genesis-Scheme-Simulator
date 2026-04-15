# rules_triads_relative.py
#
# Rotationally invariant triad rule — depends ONLY on angle differences
# between cells, never on absolute angles. The templates specify what the
# relative angles between three cells should be, not what any individual
# cell's angle should be.
#
# This means the entire triad can rotate freely as a unit. The rule has
# no preferred orientation in space. If discrete domains still emerge,
# that is genuine spontaneous symmetry breaking.
#
# The distinction principle: in an L-shaped triple, the two arm cells
# should differ from the corner cell by ±π/4. This encodes "same,
# differentiating, different" as a relationship, not a prescription.

from .backend import xp
from .core import angle_diff

# Relative triad templates:
#   (offset_0, offset_1, offset_2, (rel_angle_01, rel_angle_02))
#   rel_angle_01 = target for (theta_1 - theta_0)
#   rel_angle_02 = target for (theta_2 - theta_0)
#
# cell 0 = corner of the L, cell 1 and 2 = the two arms
# The arms should differ from the corner by ±π/4

_TRIADS_REL = [
    ((0, 0), ( 1, 0), (0,  1), (-0.25 * xp.pi,  0.25 * xp.pi)),  # NE
    ((0, 0), (-1, 0), (0,  1), ( 0.25 * xp.pi, -0.25 * xp.pi)),  # NW
    ((0, 0), ( 1, 0), (0, -1), ( 0.25 * xp.pi, -0.25 * xp.pi)),  # SE
    ((0, 0), (-1, 0), (0, -1), (-0.25 * xp.pi,  0.25 * xp.pi)),  # SW
]


def triad_relative_rule(state, params, extra):
    """
    Rotationally invariant triad rule.

    Computes torque based on how far each L-shaped triple's internal
    angles are from the target relative angles. The absolute orientation
    of the triple doesn't matter — only the relationships.
    """
    if params.triads == 0.0:
        return {"torque": 0.0}

    theta = state.theta
    tri_sigma2 = params.tri_sigma2
    strength = params.triads

    tri_torque = xp.zeros_like(theta)

    for (o0, o1, o2, (r01, r02)) in _TRIADS_REL:
        # Roll theta to align each triad member with the (i,j) position
        th0 = xp.roll(xp.roll(theta, -o0[0], axis=0), -o0[1], axis=1)
        th1 = xp.roll(xp.roll(theta, -o1[0], axis=0), -o1[1], axis=1)
        th2 = xp.roll(xp.roll(theta, -o2[0], axis=0), -o2[1], axis=1)

        # Relative angle errors (rotationally invariant)
        e1 = angle_diff(th1 - th0, r01)  # how far is (th1-th0) from target?
        e2 = angle_diff(th2 - th0, r02)  # how far is (th2-th0) from target?

        # Triad coherence score
        sq_err = e1 * e1 + e2 * e2
        S = xp.exp(-sq_err / tri_sigma2)
        mask = S > 1e-3

        # Torques that push toward correct relative angles
        # Cell 0 (corner): pushed by both constraints
        t0 = strength * S * (xp.sin(e1) + xp.sin(e2)) * mask
        # Cell 1 (arm): pushed by constraint 1 only
        t1 = strength * S * (-xp.sin(e1)) * mask
        # Cell 2 (arm): pushed by constraint 2 only
        t2 = strength * S * (-xp.sin(e2)) * mask

        # Roll torques back to home positions
        tri_torque += xp.roll(xp.roll(t0, o0[0], axis=0), o0[1], axis=1)
        tri_torque += xp.roll(xp.roll(t1, o1[0], axis=0), o1[1], axis=1)
        tri_torque += xp.roll(xp.roll(t2, o2[0], axis=0), o2[1], axis=1)

    extra["tri_torque"] = tri_torque
    return {"torque": tri_torque}
