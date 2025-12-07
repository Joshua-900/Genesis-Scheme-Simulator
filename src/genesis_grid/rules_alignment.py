import numpy as np

def alignment_rule(state, params, extra):
    # Ensure 'state' is defined and has attribute 'theta'
    if not hasattr(state, 'theta'):
        raise AttributeError("'state' object must have a 'theta' attribute")
    theta = state.theta
    up    = np.roll(theta, -1, axis=0)
    down  = np.roll(theta,  1, axis=0)
    left  = np.roll(theta, -1, axis=1)
    right = np.roll(theta,  1, axis=1)

    dtheta_align = (
        np.sin(up - theta) +
        np.sin(down - theta) +
        np.sin(left - theta) +
        np.sin(right - theta)
    )

    # save for other rules (tension uses this)
    extra["dtheta_align"] = dtheta_align
    extra["grad_align"]   = np.abs(dtheta_align)

    torque = params.alpha * dtheta_align
    return {"torque": torque}