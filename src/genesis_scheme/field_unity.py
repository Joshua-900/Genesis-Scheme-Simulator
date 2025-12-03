# #src/genesis_scheme/field_unity.py

# from dataclasses import dataclass
# import numpy as np

# @dataclass
# class FieldUnity:
# 	"""
# 	2D Unity field with a scalar 'tension' parameter.
# 	field: 2D numpy array (H, W)
# 	tension: scalar representing initial perturbation magnitude
# 	"""
# 	field: np.ndarray
# 	tension: float

# def create_unity_field(
# 	size: int = 200,
# 	eps: float = 0.01,
# ) -> FieldUnity:
# 	"""
# 	Create a nearly uniform Unity field with tiny random noise
# 	(to break perfect symmetry) and a small central bump (tension seed).
# 	"""
# 	field = np.zeros((size, size), dtype=np.float32)

# 	# tiny random noise everywhere (symmetry-breaking)
# 	noise = np.random.normal(loc=0.0, scale=0.002, size=(size, size)).astype(np.float32)
# 	field += noise

# 	# central bump as main tension seed
# 	cx, cy = size // 2, size // 2
# 	field[cx, cy] += eps

# 	return FieldUnity(field=field, tension=eps)

# def laplacian(field: np.ndarray) -> np.ndarray:
# 	"""
# 	Discrete Laplacian with periodic boundaries using np.roll.
# 	Encodes neighbor interaction (local coupling).
# 	"""
# 	up    = np.roll(field, -1, axis=0)
# 	down  = np.roll(field,  1, axis=0)
# 	left  = np.roll(field, -1, axis=1)
# 	right = np.roll(field,  1, axis=1)

# 	return up + down + left + right - 4.0 * field

# def F(field: np.ndarray, diff_rate: float) -> np.ndarray:
# 	"""
# 	Form-Capacity mode: diffusion/smoothing.
# 	Tends to spread and smooth out differences.
# 	"""
# 	return field + diff_rate * laplacian(field)

# def A(field: np.ndarray, drive: float, nonlin_strength: float) -> np.ndarray:
# 	"""
# 	Force-Activation mode: reaction/activation.
# 	Tends to amplify contrasts and drive pattern formation.
# 	"""
# 	# cubic reaction term: has multiple "preferred" levels
# 	reaction = field * (1.0 - field) * (field - 0.5)
# 	return field + drive * reaction * nonlin_strength

# def step_field(
# 	unity: FieldUnity,
# 	diff_rate: float = 0.10,
# 	drive: float = 1.5,
# 	nonlin_strength: float = 1.2,
# 	dt: float = 0.4,
# 	noise_scale: float = 0.001,
# ) -> FieldUnity:
# 	u = unity.field

# 	u_form  = F(u, diff_rate)
# 	u_force = A(u, drive, nonlin_strength)

# 	delta_form  = u_form - u
# 	delta_force = u_force - u

# 	u_next = u + dt * (delta_form + delta_force)

# 	# inject a little fresh tension everywhere
# 	if noise_scale > 0.0:
# 		u_next += np.random.normal(0.0, noise_scale, size=u.shape).astype(u.dtype)

# 	u_next = np.clip(u_next, -1.0, 2.0)

# 	return FieldUnity(field=u_next, tension=unity.tension)