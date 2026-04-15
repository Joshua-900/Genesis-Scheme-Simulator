
# field2.py
#
# Defines Field2, a two-channel field for reaction-diffusion systems.
#
# Mathematical structure:
#   U(x, y): first field (e.g., chemical concentration)
#   V(x, y): second field (e.g., chemical concentration)
#
# Field2 holds two 2D arrays of shape (H, W):
#   self.U: ndarray, shape (H, W)
#   self.V: ndarray, shape (H, W)
#
# Methods:
#   .copy() -- returns a deep copy of the field

import numpy as np

class Field2:
    """
    Two-channel field for reaction-diffusion systems.

    U(x, y): float array, first channel
    V(x, y): float array, second channel
    shape: tuple, (height, width)
    """
    def __init__(self, U: np.ndarray, V: np.ndarray):
        # Store U and V as float arrays
        self.U = U.astype(float)
        self.V = V.astype(float)
        self.shape = U.shape

    def copy(self):
        """Return a deep copy of the field."""
        return Field2(self.U.copy(), self.V.copy())