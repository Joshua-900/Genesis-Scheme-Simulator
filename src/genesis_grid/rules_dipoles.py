# rules_dipoles.py


from backend import xp

def dipole_rule(state, params, extra):
    """
    Dipole interaction:
    - uses deformed positions X+ux, Y+uy
    - computes torque that tends to align 'head' and 'tail' ends.
    """
    if params.dipole == 0.0:
        return {"torque": 0.0}

    N      = state.N
    theta  = state.theta
    X_def  = state.X + state.ux
    Y_def  = state.Y + state.uy

    dipole_torque = xp.zeros_like(theta)

    neighbor_offsets = [(1, 0), (-1, 0), (0, 1), (0, -1)]

    for i in range(N):
        for j in range(N):
            for di, dj in neighbor_offsets:
                ni = i + di
                nj = j + dj
                if 0 <= ni < N and 0 <= nj < N:
                    dx = X_def[ni, nj] - X_def[i, j]
                    dy = Y_def[ni, nj] - Y_def[i, j]
                    phi = xp.arctan2(dy, dx)

                    QA = xp.cos(theta[i, j]   - phi)
                    QB = xp.cos(theta[ni, nj] - (phi + xp.pi))
                    Q  = QA * QB

                    dipole_torque[i, j]   += Q * xp.sin(phi        - theta[i, j])
                    dipole_torque[ni, nj] += Q * xp.sin(phi + xp.pi - theta[ni, nj])

    dipole_torque *= params.dipole
    return {"torque": dipole_torque}