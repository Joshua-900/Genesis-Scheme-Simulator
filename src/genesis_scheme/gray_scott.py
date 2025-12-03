# #src/genesis_scheme/gray_scott.py

# from dataclasses import dataclass
# import numpy as np

# @dataclass
# class GrayScottState:
# 	U: np.ndarray
# 	V: np.ndarray

# def laplacian(field: np.ndarray) -> np.ndarray:
# 	up    = np.roll(field, -1, axis=0)
# 	down  = np.roll(field,  1, axis=0)
# 	left  = np.roll(field, -1, axis=1)
# 	right = np.roll(field,  1, axis=1)
# 	return up + down + left + right - 4.0 * field

# def create_gray_scott(size: int = 200) -> GrayScottState:
# 	U = np.ones((size, size), dtype=np.float32)
# 	V = np.zeros((size, size), dtype=np.float32)

# 	s = size // 10
# 	cx, cy = size // 2, size // 2

# 	U[cx - s:cx + s, cy - s:cy + s] = 0.50
# 	V[cx - s:cx + s, cy - s:cy + s] = 0.25

# 	return GrayScottState(U=U, V=V)

# def step_gray_scott(
# 	state: GrayScottState,
# 	Du: float = 0.16,
# 	Dv: float = 0.08,
# 	F: float = 0.060,
# 	k: float = 0.062,
# 	dt: float = 1.0,
# ) -> GrayScottState:

# 	U, V = state.U, state.V

# 	lapU = laplacian(U)
# 	lapV = laplacian(V)

# 	UVV = U * V * V

# 	dU = Du * lapU - UVV + F * (1.0 - U)
# 	dV = Dv * lapV + UVV - (F + k) * V

# 	U_next = U + dt * dU
# 	V_next = V + dt * dV

# 	U_next = np.clip(U_next, 0.0, 1.5)
# 	V_next = np.clip(V_next, 0.0, 1.5)

# 	return GrayScottState(U=U_next, V=V_next)