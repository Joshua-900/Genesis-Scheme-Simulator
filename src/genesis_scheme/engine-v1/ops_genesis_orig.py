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
	# global Genesis tension T_t = mean(U^2 + V^2)
	return float(np.mean(U**2 + V**2))

def step_genesis_nonlinear(
    field: Field2,
    Du: float,
    Dv: float,
    alpha: float,
    beta: float,
    kappa: float,
    T0: float,
    dt: float,
) -> Field2:
    """
    Nonlinear Genesis step:
    - Dual-: diffusion + linear damping
    - Dual+: nonlinear contrast term (cubic in centered fields)
    - global Genesis feedback via tanh(T - T0)
    """
    # U, V: fields
    U = field.U
    V = field.V

    # Laplacians (local smoothing)
    # \nabla^2 U, \nabla^2 V
    Lu = laplacian(U)
    Lv = laplacian(V)

    # Dual- (contractive):
    #   Dm_U = D_u * \nabla^2 U - alpha * U
    #   Dm_V = D_v * \nabla^2 V - alpha * V
    Dm_U = Du * Lu - alpha * U
    Dm_V = Dv * Lv - alpha * V

    # Centered fields (remove global mean)
    #   u_c = U - mean(U)
    #   v_c = V - mean(V)
    U_mean = U.mean()
    V_mean = V.mean()
    u_c = U - U_mean
    v_c = V - V_mean

    # Dual+ (nonlinear expansive / clustering)
    #   Dp_U = beta * u_c * (1 - u_c^2 - v_c^2)
    #   Dp_V = beta * v_c * (1 - v_c^2 - u_c^2)
    Dp_U = beta * u_c * (1.0 - u_c**2 - v_c**2)
    Dp_V = beta * v_c * (1.0 - v_c**2 - u_c**2)

    # Global Genesis tension feedback
    #   sigma = kappa * tanh(T_t - T0)
    #   T_t = mean(U^2 + V^2)
    T_t = compute_tension(U, V)
    sigma = kappa * np.tanh(T_t - T0)

    # Genesis update:
    #   U_new = U + dt * (Dm_U + Dp_U - sigma * U)
    #   V_new = V + dt * (Dm_V + Dp_V + sigma * V)
    U_new = U + dt * (Dm_U + Dp_U - sigma * U)
    V_new = V + dt * (Dm_V + Dp_V + sigma * V)

    return Field2(U_new, V_new)