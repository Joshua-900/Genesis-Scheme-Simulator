#tension.py
import numpy as np
from field2 import Field2
import os, inspect

print(">>> LOADING tension.py FROM:", os.path.abspath(__file__))

def add_seed(field: Field2, radius=10, amplitude=0.5):
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
    # DEBUG: show what attributes this Field2 actually has
    #print("tension_norm() using Field2 with attrs:", [a for a in dir(field) if not a.startswith('_')])

    # THIS is the only line that should run.
    return float(np.sum(field.U**2 + field.V**2))