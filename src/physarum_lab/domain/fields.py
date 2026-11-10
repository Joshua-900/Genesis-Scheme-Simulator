"""Authored environmental formulas, independent of agents and presentation."""
from __future__ import annotations

import math
import numpy as np

TAU = 2 * math.pi


def wave_field(size: int, m: int, n: int) -> np.ndarray:
    """Designed Chladni-like interference; not a physical plate solver.

    Integer cosine modes make both value and first derivative continuous at
    the periodic seams. Squared amplitude supplies the nodal attraction cost.
    """
    axis = (np.arange(size, dtype=np.float32) + .5) / size * TAU
    cm, cn = np.cos(m * axis), np.cos(n * axis)
    return ((cm[:, None] * cn[None, :] - cn[:, None] * cm[None, :]) * .5).astype(np.float32)


def current_velocity(x: np.ndarray, y: np.ndarray, size: int, tick: int) -> tuple[np.ndarray, np.ndarray]:
    """An authored periodic curl field, not a solved fluid or emergent force.

    This is the analytic curl of a multiscale stream function. Each term is
    divergence-free, and time depends on model ticks rather than frame rate.
    """
    x, y, t = x * (TAU / size), y * (TAU / size), tick * .003
    vx, vy = np.zeros_like(x), np.zeros_like(y)
    for kx, ky, amplitude, phase in ((2, 3, .34, .3), (3, 2, .26, 1.7),
                                     (5, 7, .055, 2.4), (9, 6, .025, .8)):
        a, b = kx * x + t + phase, ky * y - t * .7 - phase
        vx += amplitude * ky * np.sin(a) * np.cos(b)
        vy -= amplitude * kx * np.cos(a) * np.sin(b)
    return vx, vy

