
# ops.py
# Numerical implementation of a two-field reaction-diffusion system (Gray-Scott style).
#
# Let U(x, y, t), V(x, y, t) be two fields evolving over time.
#
# Diffusion (Laplacian):
#     \nabla^2 Z = -4Z + Z_{up} + Z_{down} + Z_{left} + Z_{right}
#
# Contractive (D_minus):
#     dU/dt = D_u * \nabla^2 U + F * (1 - U)
#     dV/dt = D_v * \nabla^2 V - (F + k) * V
#
# Expansive (D_plus, Gray-Scott reaction):
#     dU/dt += -U * V^2
#     dV/dt += +U * V^2
#
# Full update:
#     U_{t+1} = U_t + dt * (D_minus_U + D_plus_U)
#     V_{t+1} = V_t + dt * (D_minus_V + D_plus_V)

import numpy as np
from field2 import Field2

def laplacian(Z: np.ndarray) -> np.ndarray:
	# 5-point Laplacian with periodic boundaries:
	# \nabla^2 Z = -4Z + Z_{up} + Z_{down} + Z_{left} + Z_{right}
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
	# Contractive part of Duality:
	# Diffusion + baseline attraction
	# dU/dt = D_u * \nabla^2 U + F * (1 - U)
	# dV/dt = D_v * \nabla^2 V - (F + k) * V
	U, V = field.U, field.V

	lapU = laplacian(U)
	lapV = laplacian(V)

	dU_minus = Du * lapU + F * (1.0 - U)
	dV_minus = Dv * lapV - (F + k) * V

	return dU_minus, dV_minus

def D_plus(field: Field2):
	# Expansive part of Duality:
	# Nonlinear autocatalytic reaction (Gray-Scott):
	# dU/dt += -U * V^2
	# dV/dt += +U * V^2
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
	# Full update step:
	# U_{t+1} = U_t + dt * (D_minus_U + D_plus_U)
	# V_{t+1} = V_t + dt * (D_minus_V + D_plus_V)
	dU_minus, dV_minus = D_minus(field, Du=Du, Dv=Dv, F=F, k=k)
	dU_plus,  dV_plus  = D_plus(field)

	dU = dU_minus + dU_plus
	dV = dV_minus + dV_plus

	U_next = field.U + dt * dU
	V_next = field.V + dt * dV

	return Field2(U_next, V_next)