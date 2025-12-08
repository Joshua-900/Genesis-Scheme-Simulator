
from backend import xp

def alignment_rule(state, params, extra):
    # Ensure 'state' is defined and has attribute 'theta'
    if not hasattr(state, 'theta'):
        raise AttributeError("'state' object must have a 'theta' attribute")
    theta = state.theta
    up    = xp.roll(theta, -1, axis=0)
    down  = xp.roll(theta,  1, axis=0)
    left  = xp.roll(theta, -1, axis=1)
    right = xp.roll(theta,  1, axis=1)

    dtheta_align = (
        xp.sin(up - theta) +
        xp.sin(down - theta) +
        xp.sin(left - theta) +
        xp.sin(right - theta)
    )

    # save for other rules (tension uses this)
    extra["dtheta_align"] = dtheta_align
    extra["grad_align"]   = xp.abs(dtheta_align)

    torque = params.alpha * dtheta_align
    return {"torque": torque}