# diagnostics.py
#
# Diagnostic computations that don't affect the physics — read-only analysis
# of the current state. These are never part of the rule pipeline.
#
# Currently: vortex detection, unity (local coherence), winding number field.

from .backend import xp
import numpy as np


def detect_vortices(state):
    """
    Find topological defects (vortices) in the orientation field.

    A vortex exists at a grid plaquette (2x2 cell square) where the
    total winding of theta around the plaquette is +/-2pi.

    Returns:
        vortex_plus:  list of (row, col) positions of +1 vortices (counterclockwise winding)
        vortex_minus: list of (row, col) positions of -1 vortices (clockwise winding)
        winding:      NxN array of winding numbers (mostly 0, +/-1 at defects)
    """
    theta = state.theta
    if hasattr(theta, 'get'):
        theta = theta.get()  # CuPy -> NumPy

    N = theta.shape[0]

    # Angle differences along each edge of each plaquette
    # Plaquette corners: (i,j) -> (i,j+1) -> (i+1,j+1) -> (i+1,j) -> back
    def _wrap(d):
        """Wrap angle difference to [-pi, pi]."""
        return (d + np.pi) % (2 * np.pi) - np.pi

    # Right neighbor
    d1 = _wrap(np.roll(theta, -1, axis=1) - theta)
    # Down-right to down (shift down then compare)
    d2 = _wrap(np.roll(theta, -1, axis=0) - np.roll(np.roll(theta, -1, axis=1), 0, axis=0))
    # Actually, let's compute the 4 edges of each plaquette properly:
    # Corner A = (i, j), B = (i, j+1), C = (i+1, j+1), D = (i+1, j)
    # Winding = wrap(B-A) + wrap(C-B) + wrap(D-C) + wrap(A-D)

    A = theta
    B = np.roll(theta, -1, axis=1)        # right
    C = np.roll(np.roll(theta, -1, axis=0), -1, axis=1)  # down-right
    D = np.roll(theta, -1, axis=0)        # down

    winding = _wrap(B - A) + _wrap(C - B) + _wrap(D - C) + _wrap(A - D)

    # Normalize to winding number: divide by 2pi, round to nearest integer
    winding_number = np.round(winding / (2 * np.pi)).astype(int)

    # Extract vortex positions (plaquette center = i+0.5, j+0.5)
    plus_idx = np.argwhere(winding_number == 1)
    minus_idx = np.argwhere(winding_number == -1)

    vortex_plus = [(r + 0.5, c + 0.5) for r, c in plus_idx]
    vortex_minus = [(r + 0.5, c + 0.5) for r, c in minus_idx]

    return vortex_plus, vortex_minus, winding_number


def compute_unity(state):
    """
    Local coherence of orientation — magnitude of the neighborhood order parameter.
    Returns NxN array in [0, 1]. High = neighbors agree, low = disordered.
    """
    theta = state.theta
    if hasattr(theta, 'get'):
        theta = theta.get()

    ex = np.cos(theta)
    ey = np.sin(theta)
    ex_avg = (ex + np.roll(ex, 1, 0) + np.roll(ex, -1, 0)
              + np.roll(ex, 1, 1) + np.roll(ex, -1, 1)) / 5.0
    ey_avg = (ey + np.roll(ey, 1, 0) + np.roll(ey, -1, 0)
              + np.roll(ey, 1, 1) + np.roll(ey, -1, 1)) / 5.0
    return np.sqrt(ex_avg ** 2 + ey_avg ** 2)
