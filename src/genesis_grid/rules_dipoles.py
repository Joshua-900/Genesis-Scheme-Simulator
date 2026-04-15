# rules_dipoles.py
#
# Head-tail dipole interaction — vectorized with numpy rolls.
# Each cell interacts with its 4 cardinal neighbors on the deformed grid.

from .backend import xp


def dipole_rule(state, params, extra):
    if params.dipole == 0.0:
        return {"torque": 0.0}

    theta = state.theta
    X_def = state.X + state.ux
    Y_def = state.Y + state.uy

    dipole_torque = xp.zeros_like(theta)

    for shift_ax, shift_dir in [(0, 1), (0, -1), (1, 1), (1, -1)]:
        # Neighbor's deformed position
        Xn = xp.roll(X_def, shift_dir, axis=shift_ax)
        Yn = xp.roll(Y_def, shift_dir, axis=shift_ax)
        theta_n = xp.roll(theta, shift_dir, axis=shift_ax)

        # Vector from self to neighbor
        dx = Xn - X_def
        dy = Yn - Y_def
        phi = xp.arctan2(dy, dx)

        # Dipole quality: does self point toward neighbor, neighbor point away?
        QA = xp.cos(theta - phi)
        QB = xp.cos(theta_n - (phi + xp.pi))
        Q = QA * QB

        # Torque on self and neighbor
        dipole_torque += Q * xp.sin(phi - theta)
        # Torque on the neighbor (rolled back to its home position)
        neighbor_contrib = Q * xp.sin(phi + xp.pi - theta_n)
        dipole_torque += xp.roll(neighbor_contrib, -shift_dir, axis=shift_ax)

    dipole_torque *= params.dipole
    return {"torque": dipole_torque}
