"""Explicit state interventions for causal gamma experiments."""

from __future__ import annotations

import numpy as np

from src.genesis_grid.backend import to_cpu, xp
from .core import GammaParams, GammaState


def perimeter_edges(mask: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Return right/down edge masks covering all four sides of a region."""
    right = mask & ~np.roll(mask, -1, 1)
    left = mask & ~np.roll(mask, 1, 1)
    down = mask & ~np.roll(mask, -1, 0)
    up = mask & ~np.roll(mask, 1, 0)
    return right | np.roll(left, 1, 1), down | np.roll(up, 1, 0)


def apply_boundary(state: GammaState, mask: np.ndarray, params: GammaParams, mode: str, strength: float) -> None:
    """Directly weaken or strengthen a selected region's stored perimeter."""
    edge_x, edge_y = perimeter_edges(mask)
    edge_x, edge_y = xp.asarray(edge_x), xp.asarray(edge_y)
    if mode == "weaken":
        state.boundary_x[edge_x] *= 1.0 - strength
        state.boundary_y[edge_y] *= 1.0 - strength
    elif mode == "strengthen":
        state.boundary_x[edge_x] += strength * (1.0 - state.boundary_x[edge_x])
        state.boundary_y[edge_y] += strength * (1.0 - state.boundary_y[edge_y])
    else:
        raise ValueError(f"Unknown boundary intervention: {mode}")
    state.rx = params.boundary_permeability_floor + params.boundary_permeability_span * (1.0 - state.boundary_x)
    state.ry = params.boundary_permeability_floor + params.boundary_permeability_span * (1.0 - state.boundary_y)


def perimeter_boundary_mean(state: GammaState, mask: np.ndarray) -> float:
    edge_x, edge_y = perimeter_edges(mask)
    bx, by = np.asarray(to_cpu(state.boundary_x)), np.asarray(to_cpu(state.boundary_y))
    values = [value for value in (bx[edge_x], by[edge_y]) if value.size]
    return float(np.mean(np.concatenate(values))) if values else 0.0
