#ops_genesis.py

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
	# global Genesis tension
	return float(np.mean(U**2 + V**2))

def step_genesis(
	field: Field2,
	Du: float,
	Dv: float,
	alpha: float,
	beta: float,
	gamma: float,
	kappa: float,
	T0: float,
	dt: float,
) -> Field2:
    U = field.U
    V = field.V

    Lu = laplacian(U)
    Lv = laplacian(V)

    # --- Dual− (smoothing + mild damping) ---
    Dm_U = Du * Lu - alpha * U
    Dm_V = Dv * Lv - alpha * V

    # --- Dual+ (contrast + local nonlinear saturation) ---
    U_mean = U.mean()
    V_mean = V.mean()

    # contrast term: pushes away from mean
    C_U = U - U_mean
    C_V = V - V_mean

    # cubic saturation: prevents runaway growth
    NL_U = -gamma * (U**3)
    NL_V = -gamma * (V**3)

    Dp_U = beta * C_U + NL_U
    Dp_V = beta * C_V + NL_V

    # --- global tension feedback (Genesis) ---
    T_t = compute_tension(U, V)
    sigma = kappa * (T_t - T0)

    # --- final update ---
    U_new = U + dt * (Dm_U + Dp_U - sigma * U)
    V_new = V + dt * (Dm_V + Dp_V + sigma * V)

    return Field2(U_new, V_new)