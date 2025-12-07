
# tension.py
# Utility functions for seeding and measuring 'tension' in a two-field system.
#
# Tension metric:
#     T = \sum_{x,y} (U(x,y)^2 + V(x,y)^2)
#     (Sum of squares of both fields over all grid points)

import numpy as np
from field2 import Field2
import os, inspect

print(">>> LOADING tension.py FROM:", os.path.abspath(__file__))

def add_seed(field: Field2, radius=10, amplitude=0.5):
	# Add a circular 'seed' (bump) to the center of the field.
	# For all (x, y) within radius:
	#     U(x, y) += amplitude
	#     V(x, y) += amplitude * 0.1
	H, W = field.shape
	cy, cx = H // 2, W // 2

	Y, X = np.ogrid[:H, :W]
	mask = (X - cx)**2 + (Y - cy)**2 <= radius**2

	U = field.U.copy()
	V = field.V.copy()

	U[mask] += amplitude
	V[mask] += amplitude * 0.1

	return Field2(U, V)

def tension_norm(field: Field2):
	# Compute the tension metric:
	#     T = \sum_{x,y} (U(x,y)^2 + V(x,y)^2)
	# Returns a single float value.
	return float(np.sum(field.U**2 + field.V**2))