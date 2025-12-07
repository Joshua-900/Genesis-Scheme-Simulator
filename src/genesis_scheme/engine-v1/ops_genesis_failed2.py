#engine-v1/ops_genesis.py

import numpy as np
from field2 import Field2

def laplacian(Z: np.ndarray) -> np.ndarray:
    return (
        -4.0 * Z
        + np.roll(Z, 1, 0)
        + np.roll(Z, -1, 0)
        + np.roll(Z, 1, 1)
        + np.roll(Z, -1, 1)
    )

def compute_tension(U: np.ndarray, V: np.ndarray) -> float:
    """
    Global Genesis tension T_t.
    Right now: mean squared magnitude of the field.
    """
    U2 = U ** 2
    V2 = V ** 2
    return float(np.mean(U2 + V2))

def step_genesis(
field: Field2,
Du: float,
Dv: float,
alpha: float,
beta: float,
kappa: float,
T0: float,
dt: float,
gamma: float = 0.5,   # local nonlinear saturation strength
) -> Field2:
    """
    Nonlinear Genesis step:
    - Dual-  : diffusion + linear damping
    - Dual+  : contrast (deviation from mean)
    - Nonlin : local cubic saturation  (−gamma U^3, −gamma V^3)
    - Global : tension feedback via sigma * U / V

    This is *not* Gray–Scott. It is a Genesis-style PDE with:
      - local smoothing (Du, Dv, alpha)
      - local sharpening (beta)
      - local nonlinearity (gamma)
      - global feedback (kappa, T0)
    """

    U = field.U
    V = field.V

    # Laplacians (local smoothing)
    Lu = laplacian(U)
    Lv = laplacian(V)

    # Dual− : contractive part (diffusion + linear damping)
    Dm_U = Du * Lu - alpha * U
    Dm_V = Dv * Lv - alpha * V

    # Dual+ : expansive / contrast part (deviation from mean)
    U_mean = U.mean()
    V_mean = V.mean()
    Dp_U = beta * (U - U_mean)
    Dp_V = beta * (V - V_mean)

    # Local nonlinear saturation (keeps amplitudes bounded)
    N_U = -gamma * (U**3)
    N_V = -gamma * (V**3)

    # Global Genesis tension feedback
    T_t = compute_tension(U, V)
    sigma = kappa * (T_t - T0)

    # Genesis update
    U_new = U + dt * (Dm_U + Dp_U + N_U - sigma * U)
    V_new = V + dt * (Dm_V + Dp_V + N_V + sigma * V)

    return Field2(U_new, V_new)