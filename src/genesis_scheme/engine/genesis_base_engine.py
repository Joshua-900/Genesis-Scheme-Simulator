#engine.py

import numpy as np

#Engine v0 (one field duality)
#Unity Field + local tension + diffusion/ growth duality
# Dyanamics: always converge to uniform high state for tested params.
# Role: Proof of concpept for coding Gensisi operators, not a candidate for emergence.

class Field:
    """
    Simple scalar field on a 2D grid.
    F: ndarray of shape (H, W), dtype=float
    u0: scalar unity value
    """
    def __init__(self, F: np.ndarray, u0: float = 0.0):
        self.F = F.astype(float)
        self.u0 = float(u0)

    @property
    def shape(self):
        return self.F.shape

def tension(F: Field) -> float:
    """
    T(F) = 1/2 * sum_x (F(x) - u0)^2
    """
    G = F.F - F.u0
    return 0.5 * np.sum(G * G)

def diffusion_contractive(field: Field, alpha: float = 0.2) -> np.ndarray:
    """
    D_-(F): simple 2D Laplacian-like smoothing.
    """
    F = field.F
    F_up    = np.roll(F, -1, axis=0)
    F_down  = np.roll(F,  1, axis=0)
    F_left  = np.roll(F, -1, axis=1)
    F_right = np.roll(F,  1, axis=1)

    lap = F_up + F_down + F_left + F_right - 4.0 * F
    return alpha * lap

def reaction_expansive(field: Field, beta: float = 0.5) -> np.ndarray:
    """
    D_+(F): local expansive nonlinearity.
    """
    F = field.F
    G = F - field.u0
    return beta * (G - G**3)

def nonlinear_coupling(field: Field, gamma: float = 0.1) -> np.ndarray:
    """
    N(F): extra nonlinear term (off by default).
    """
    F = field.F
    G = F - field.u0
    return gamma * G *(1.0 - G**2)

def step(field: Field,
         alpha: float = 0.2,
         beta: float = 0.5,
         gamma: float = 0.0,
         dt: float = 1.0) -> Field:
    """
    One time-step:
    F_{t+1} = F_t + dt * (D_-(F_t) + D_+(F_t) + N(F_t))
    """
    D_minus = diffusion_contractive(field, alpha=alpha)
    D_plus  = reaction_expansive(field,  beta=beta)
    N_term  = nonlinear_coupling(field,  gamma=gamma)

    F_next = field.F + dt * (D_minus + D_plus + N_term)
    return Field(F_next, u0=field.u0)