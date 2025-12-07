# Minimal placeholder for curvature_rule
def curvature_rule(state, params):
        """Placeholder curvature rule. Returns zero field or unchanged state."""
        # Example: return np.zeros_like(state.grid) if state has grid, or just return state
        try:
                import numpy as np
                return np.zeros_like(state.grid)
        except Exception:
                return state
# rules_curvature.py

import numpy as np

def curvature_rule(state, params, extra):
    """
    Curvature rule:
    - look at the Laplacian of the geometry field (ux, uy)
    - treat high curvature as a 'direction' that tugs theta
    - torque magnitude scaled by params.curv
    """
    if params.curv == 0.0:
        return {"torque": 0.0}

    ux = state.ux
    uy = state.uy

    # 5-point Laplacian (same as we used before)
    ux_lap = (np.roll(ux, -1, 0) + np.roll(ux, 1, 0) +
            np.roll(ux, -1, 1) + np.roll(ux, 1, 1) -
            4.0 * ux)

    uy_lap = (np.roll(uy, -1, 0) + np.roll(uy, 1, 0) +
            np.roll(uy, -1, 1) + np.roll(uy, 1, 1) -
            4.0 * uy)

    # curvature vector and its direction
    curv_mag = np.sqrt(ux_lap*ux_lap + uy_lap*uy_lap) + 1e-8
    phi_curv = np.arctan2(uy_lap, ux_lap)

    # save for other rules if they care
    extra["curv_mag"] = curv_mag
    extra["phi_curv"] = phi_curv

    # torque: theta tends to align with curvature direction
    theta = state.theta
    curvature_torque = params.curv * curv_mag * np.sin(phi_curv - theta)

    return {"torque": curvature_torque}