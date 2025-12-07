#engine-v1/ops_grayscott.py

import numpy as np
from field2 import Field2

def laplacian(Z: np.ndarray) -> np.ndarray:
    """
    Standard 5-point Laplacian with periodic (wrap-around) boundary conditions.
    """
    return (
        -4.0 * Z
        + np.roll(Z, 1, 0)
        + np.roll(Z, -1, 0)
        + np.roll(Z, 1, 1)
        + np.roll(Z, -1, 1)
    )

def compute_tension(U: np.ndarray, V: np.ndarray) -> float:
    U2 = U ** 2
    V2 = V ** 2
    return float(np.mean(U2 + V2))

def step_gs(
    field: Field2,
    Du: float,
    Dv: float,
    F: float,
    k: float,
    dt: float,
) -> Field2:
    """
    Classic Gray–Scott reaction–diffusion step.

    U_t+1 = U + dt * (Du * ∇²U - U*V² + F*(1 - U))
    V_t+1 = V + dt * (Dv * ∇²V + U*V² - (F + k)*V)

    Args:
        field: Field2 holding U, V arrays.
        Du, Dv: diffusion coefficients for U and V.
        F: feed rate.
        k: kill rate.
        dt: time step.

    Returns:
        New Field2(U_new, V_new).
    """
    U = field.U
    V = field.V

    Lu = laplacian(U)
    Lv = laplacian(V)

    # Reaction–diffusion RHS
    UVV = U * V * V

    dU = Du * Lu - UVV + F * (1.0 - U)
    dV = Dv * Lv + UVV - (F + k) * V

    U_new = U + dt * dU
    V_new = V + dt * dV

    return Field2(U_new, V_new)


def step_gs_genesis(
    field: Field2,
    Du: float,
    Dv: float,
    F: float,
    k: float,
    dt: float,
    kappa: float,
    T0: float,
) -> Field2:
    U = field.U
    V = field.V

    Lu = laplacian(U)
    Lv = laplacian(V)

    # standard Gray–Scott pieces
    reactU = -U * V * V + F * (1.0 - U)
    reactV =  U * V * V - (F + k) * V

    # Genesis tension feedback
    T_t = compute_tension(U, V) / 3.14 * (1.618033988749895 / kappa-U*V)
    sigma = kappa * (T_t - T0)

    U_new = U + dt * (Du * Lu + reactU - sigma * U)
    V_new = V + dt * (Dv * Lv + reactV + sigma * V)



    return Field2(U_new, V_new)