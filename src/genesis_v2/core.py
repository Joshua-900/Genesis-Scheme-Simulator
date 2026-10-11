"""Minimal coupled-field implementation of the v2 bridge contract.

This is a falsifiable prototype, not a final Genesis equation.  It keeps
potentiality (P), actuality (A), and relation (R) distinct in state and gives
each a bidirectional role in the update.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.genesis_grid.backend import xp, to_cpu


@dataclass
class V2Params:
    """Parameters for the smallest coupled P/A/R model."""

    potential_diffusion: float = 0.08
    potential_relation_gain: float = 0.14
    actual_to_potential: float = 0.10
    potential_decay: float = 0.03
    actual_alignment: float = 0.35
    potential_to_actual: float = 0.45
    relation_rate: float = 0.12
    relation_floor: float = 0.05


class V2State:
    """Coupled lattice state: P=(px, py), A=theta, R=(rx, ry)."""

    def __init__(self, N: int, dt: float = 0.05, seed: int | None = None):
        if seed is not None:
            xp.random.seed(seed)
        self.N = int(N)
        self.dt = float(dt)

        # P: latent directional disposition. Its magnitude is also meaningful:
        # weak P means little directional availability; strong P biases A.
        self.px = xp.random.normal(0.0, 0.25, (N, N))
        self.py = xp.random.normal(0.0, 0.25, (N, N))

        # A: realized orientation.
        self.theta = xp.random.rand(N, N) * 2.0 * xp.pi

        # R: dynamic reciprocal edge weights. rx couples each cell to its
        # right neighbor, ry couples it to its down neighbor.
        self.rx = xp.ones((N, N), dtype=float)
        self.ry = xp.ones((N, N), dtype=float)

    def clone(self) -> "V2State":
        duplicate = object.__new__(V2State)
        duplicate.N = self.N
        duplicate.dt = self.dt
        for name in ("px", "py", "theta", "rx", "ry"):
            setattr(duplicate, name, getattr(self, name).copy())
        return duplicate


def _unit(x: Any, y: Any) -> tuple[Any, Any]:
    magnitude = xp.sqrt(x * x + y * y) + 1e-8
    return x / magnitude, y / magnitude


def _laplacian(field: Any) -> Any:
    return (
        xp.roll(field, -1, axis=0)
        + xp.roll(field, 1, axis=0)
        + xp.roll(field, -1, axis=1)
        + xp.roll(field, 1, axis=1)
        - 4.0 * field
    )


def _relation_weighted_neighbors(field: Any, rx: Any, ry: Any) -> Any:
    """Average neighbors using the reciprocal edge fields around each cell."""
    right = xp.roll(field, -1, axis=1)
    left = xp.roll(field, 1, axis=1)
    down = xp.roll(field, -1, axis=0)
    up = xp.roll(field, 1, axis=0)
    left_weight = xp.roll(rx, 1, axis=1)
    up_weight = xp.roll(ry, 1, axis=0)
    total = rx + left_weight + ry + up_weight + 1e-8
    return (rx * right + left_weight * left + ry * down + up_weight * up) / total


def step(state: V2State, params: V2Params) -> V2State:
    """Advance P, A, and R once without collapsing their roles together."""
    theta = state.theta
    actual_x, actual_y = xp.cos(theta), xp.sin(theta)
    potential_x, potential_y = _unit(state.px, state.py)

    # R changes only when both realized and latent neighboring directions are
    # mutually compatible. This is an explicit relational state, not a fixed
    # neighborhood constant.
    actual_right = actual_x * xp.roll(actual_x, -1, 1) + actual_y * xp.roll(actual_y, -1, 1)
    actual_down = actual_x * xp.roll(actual_x, -1, 0) + actual_y * xp.roll(actual_y, -1, 0)
    potential_right = potential_x * xp.roll(potential_x, -1, 1) + potential_y * xp.roll(potential_y, -1, 1)
    potential_down = potential_x * xp.roll(potential_x, -1, 0) + potential_y * xp.roll(potential_y, -1, 0)
    target_rx = 0.25 * (1.0 + actual_right) * (1.0 + potential_right)
    target_ry = 0.25 * (1.0 + actual_down) * (1.0 + potential_down)
    state.rx = xp.clip((1.0 - params.relation_rate) * state.rx + params.relation_rate * target_rx, params.relation_floor, 1.0)
    state.ry = xp.clip((1.0 - params.relation_rate) * state.ry + params.relation_rate * target_ry, params.relation_floor, 1.0)

    # P has its own memory, diffusion, and relational propagation. Actuality
    # reshapes P, but does not replace it.
    p_neighbor_x = _relation_weighted_neighbors(state.px, state.rx, state.ry)
    p_neighbor_y = _relation_weighted_neighbors(state.py, state.rx, state.ry)
    state.px = state.px + state.dt * (
        params.potential_diffusion * _laplacian(state.px)
        + params.potential_relation_gain * (p_neighbor_x - state.px)
        + params.actual_to_potential * (actual_x - state.px)
        - params.potential_decay * state.px
    )
    state.py = state.py + state.dt * (
        params.potential_diffusion * _laplacian(state.py)
        + params.potential_relation_gain * (p_neighbor_y - state.py)
        + params.actual_to_potential * (actual_y - state.py)
        - params.potential_decay * state.py
    )

    # A is realized orientation. It responds to the relationally weighted
    # actual neighborhood and to the distinct latent P state.
    right = xp.roll(theta, -1, axis=1)
    left = xp.roll(theta, 1, axis=1)
    down = xp.roll(theta, -1, axis=0)
    up = xp.roll(theta, 1, axis=0)
    alignment = (
        state.rx * xp.sin(right - theta)
        + xp.roll(state.rx, 1, axis=1) * xp.sin(left - theta)
        + state.ry * xp.sin(down - theta)
        + xp.roll(state.ry, 1, axis=0) * xp.sin(up - theta)
    )
    p_angle = xp.arctan2(state.py, state.px)
    p_strength = xp.clip(xp.sqrt(state.px * state.px + state.py * state.py), 0.0, 1.0)
    potential_torque = p_strength * xp.sin(p_angle - theta)
    state.theta = (theta + state.dt * (params.actual_alignment * alignment + params.potential_to_actual * potential_torque)) % (2.0 * xp.pi)
    return state


def summary(state: V2State) -> dict[str, float]:
    """Small, read-only summary for intervention and regression experiments."""
    theta = to_cpu(state.theta)
    px, py = to_cpu(state.px), to_cpu(state.py)
    rx, ry = to_cpu(state.rx), to_cpu(state.ry)
    p_angle = xp.arctan2(py, px)
    alignment = xp.mean(xp.cos(theta - p_angle))
    return {
        "actual_order": float(xp.sqrt(xp.mean(xp.cos(theta)) ** 2 + xp.mean(xp.sin(theta)) ** 2)),
        "potential_strength": float(xp.mean(xp.sqrt(px * px + py * py))),
        "potential_actual_alignment": float(alignment),
        "relation_mean": float(0.5 * (xp.mean(rx) + xp.mean(ry))),
    }
