#ops.py
import numpy as np
from field2 import Field2

def laplacian(Z: np.ndarray) -> np.ndarray:
	"""5-point Laplacian with periodic boundaries."""
	return (
		-4.0 * Z
		+ np.roll(Z, 1, 0) + np.roll(Z, -1, 0)
		+ np.roll(Z, 1, 1) + np.roll(Z, -1, 1)
	)

def D_minus(field: Field2,
			Du: float,
			Dv: float,
			F: float,
			k: float):
	"""
	Contractive part of Duality:
	- smooths (diffusion)
	- pulls U,V toward baseline (U→1, V→0)
	"""
	U, V = field.U, field.V

	lapU = laplacian(U)
	lapV = laplacian(V)

	dU_minus = Du * lapU + F * (1.0 - U)
	dV_minus = Dv * lapV - (F + k) * V

	return dU_minus, dV_minus

def D_plus(field: Field2):
	"""
	Expansive part of Duality:
	- nonlinear local term that amplifies patterns
	- here: auto-catalytic UV^2 (Gray-Scott style)
	"""
	U, V = field.U, field.V
	UVV = U * V * V

	dU_plus = -UVV
	dV_plus = +UVV

	return dU_plus, dV_plus

def step(field: Field2,
Du: float = 0.16,
Dv: float = 0.08,
F: float = 0.022,
k: float = 0.051,
dt: float = 1.0) -> Field2:
	"""
	Full Duality + Emergence step:
	dF = D_- + D_+
	F_{t+1} = F_t + dt * dF
	"""
	dU_minus, dV_minus = D_minus(field, Du=Du, Dv=Dv, F=F, k=k)
	dU_plus,  dV_plus  = D_plus(field)

	dU = dU_minus + dU_plus
	dV = dV_minus + dV_plus

	U_next = field.U + dt * dU
	V_next = field.V + dt * dV

	return Field2(U_next, V_next)