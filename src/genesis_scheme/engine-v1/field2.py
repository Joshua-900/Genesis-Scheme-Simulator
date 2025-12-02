#field2.py

import numpy as np

class Field2:
    """
    Two-channel field U(x,y), V(x,y)
    """
    def __init__(self, U: np.ndarray, V: np.ndarray):
        self.U = U.astype(float)
        self.V = V.astype(float)
        self.shape = U.shape

    def copy(self):
        return Field2(self.U.copy(), self.V.copy())