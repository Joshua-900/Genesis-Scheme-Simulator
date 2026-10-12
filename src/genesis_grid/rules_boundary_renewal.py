"""Experimental compression-gated local coherence renewal for V1.

The rule is deliberately inactive by default.  A compressed cell reads only
its compressed cardinal neighbors and is pulled toward their circular mean;
there is no global preferred orientation or object tracker feedback.
"""

from .backend import xp


def boundary_renewal_rule(state, params, extra):
    strength = params.boundary_renewal
    if strength == 0.0:
        return {"torque": 0.0}

    compression = extra.get("C", state.C)
    theta = state.theta
    weighted_cos = xp.zeros_like(theta)
    weighted_sin = xp.zeros_like(theta)
    weight = xp.zeros_like(theta)
    for axis, shift in ((0, -1), (0, 1), (1, -1), (1, 1)):
        neighbor_c = xp.roll(compression, shift, axis=axis)
        neighbor_theta = xp.roll(theta, shift, axis=axis)
        weighted_cos += neighbor_c * xp.cos(neighbor_theta)
        weighted_sin += neighbor_c * xp.sin(neighbor_theta)
        weight += neighbor_c
    target = xp.arctan2(weighted_sin, weighted_cos)
    coherence = xp.sqrt(weighted_cos * weighted_cos + weighted_sin * weighted_sin) / (weight + 1e-8)
    return {"torque": strength * compression * coherence * xp.sin(target - theta)}
