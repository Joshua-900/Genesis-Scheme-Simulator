#engine-v1/ops_genesis.py

import numpy as np
from .field2 import Field2

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
	Global Genesis tension T_t = mean(U^2 + V^2)
	"""
	return float(np.mean(U**2 + V**2))

def step_genesis(
	field: Field2,
	Du: float,
	Dv: float,
	alpha: float,
	beta: float,
	kappa: float,
	T0: float,
	dt: float,
) -> Field2:
	U = field.U
	V = field.V

	# --- local smoothing (Dual–) ---
	Lu = laplacian(U)
	Lv = laplacian(V)
	Dm_U = Du * Lu - alpha * U
	Dm_V = Dv * Lv - alpha * V

	# --- local contrast (Dual+) ---
	U_mean = U.mean()
	V_mean = V.mean()
	Dp_U = beta * (U - U_mean)
	Dp_V = beta * (V - V_mean)

	# --- global Genesis tension feedback ---
	T_t = compute_tension(U, V)
	sigma = kappa * (T_t - T0)

	# --- explicit Euler update ---
	U_new = U + dt * (Dm_U + Dp_U - sigma * U)
	V_new = V + dt * (Dm_V + Dp_V + sigma * V)

	# --- numerical safety: prevent blow-up / NaN ---
	U_new = np.clip(U_new, -2.0, 2.0)
	V_new = np.clip(V_new, -2.0, 2.0)

	# replace any NaNs/Infs with finite values
	U_new = np.nan_to_num(U_new, nan=0.0, posinf=2.0, neginf=-2.0)
	V_new = np.nan_to_num(V_new, nan=0.0, posinf=2.0, neginf=-2.0)

	return Field2(U_new, V_new)