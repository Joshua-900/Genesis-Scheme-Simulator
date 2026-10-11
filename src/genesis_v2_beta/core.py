"""Genesis v2-beta: distinct P/A/R dynamics with explicit rules.

The alpha prototype let potentiality imitate actuality.  Beta instead treats
potentiality as a latent directional substrate plus a bounded availability
reservoir.  Actualization consumes availability; unresolved relational
difference replenishes and redirects it.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np

from src.genesis_grid.backend import to_cpu, xp


@dataclass
class BetaParams:
    potential_transport: float = 0.10
    potential_source_restore: float = 0.08
    potential_turn: float = 0.24
    availability_replenish: float = 0.10
    availability_tension_gain: float = 0.28
    actualization_depletion: float = 0.35
    actual_alignment: float = 0.28
    potential_to_actual: float = 0.20
    relation_rate: float = 0.12
    relation_baseline: float = 0.20
    relation_difference_gain: float = 0.55


class BetaState:
    """State with latent P direction, P availability, actual A, and edge R."""

    def __init__(self, N: int, dt: float = 0.05, seed: int | None = None):
        if seed is not None:
            xp.random.seed(seed)
        self.N = int(N)
        self.dt = float(dt)
        source_angle = xp.random.rand(N, N) * 2.0 * xp.pi
        self.source_x, self.source_y = xp.cos(source_angle), xp.sin(source_angle)
        self.px, self.py = self.source_x.copy(), self.source_y.copy()
        self.availability = xp.clip(0.45 + 0.10 * xp.random.normal(size=(N, N)), 0.05, 0.95)
        self.theta = xp.random.rand(N, N) * 2.0 * xp.pi
        self.rx = xp.full((N, N), 0.20, dtype=float)
        self.ry = xp.full((N, N), 0.20, dtype=float)

    def clone(self) -> "BetaState":
        duplicate = object.__new__(BetaState)
        duplicate.N, duplicate.dt = self.N, self.dt
        for name in ("source_x", "source_y", "px", "py", "availability", "theta", "rx", "ry"):
            setattr(duplicate, name, getattr(self, name).copy())
        return duplicate


def _unit(x: Any, y: Any) -> tuple[Any, Any]:
    magnitude = xp.sqrt(x * x + y * y) + 1e-8
    return x / magnitude, y / magnitude


def _laplacian(field: Any) -> Any:
    return xp.roll(field, -1, 0) + xp.roll(field, 1, 0) + xp.roll(field, -1, 1) + xp.roll(field, 1, 1) - 4.0 * field


def _edge_tension(theta: Any, px: Any, py: Any) -> tuple[Any, Any]:
    """Difference across each edge, using both actual and latent directions."""
    ax, ay = xp.cos(theta), xp.sin(theta)
    actual_right = ax * xp.roll(ax, -1, 1) + ay * xp.roll(ay, -1, 1)
    actual_down = ax * xp.roll(ax, -1, 0) + ay * xp.roll(ay, -1, 0)
    potential_right = px * xp.roll(px, -1, 1) + py * xp.roll(py, -1, 1)
    potential_down = px * xp.roll(px, -1, 0) + py * xp.roll(py, -1, 0)
    return 0.25 * (2.0 - actual_right - potential_right), 0.25 * (2.0 - actual_down - potential_down)


def relation_rule(state: BetaState, params: BetaParams, extra: dict) -> None:
    """Relations strengthen at managed difference and relax toward a baseline."""
    tension_x, tension_y = _edge_tension(state.theta, state.px, state.py)
    target_x = params.relation_baseline + params.relation_difference_gain * tension_x
    target_y = params.relation_baseline + params.relation_difference_gain * tension_y
    state.rx = xp.clip(state.rx + state.dt * params.relation_rate * (target_x - state.rx), 0.0, 1.0)
    state.ry = xp.clip(state.ry + state.dt * params.relation_rate * (target_y - state.ry), 0.0, 1.0)
    extra["local_tension"] = 0.25 * (tension_x + xp.roll(tension_x, 1, 1) + tension_y + xp.roll(tension_y, 1, 0))


def potential_rule(state: BetaState, params: BetaParams, extra: dict) -> None:
    """Transport latent alternatives; replenish and consume availability."""
    tension = extra["local_tension"]
    p_angle = xp.arctan2(state.py, state.px)
    mismatch = 0.5 * (1.0 - xp.cos(p_angle - state.theta))
    actualization = state.availability * mismatch
    state.availability = xp.clip(
        state.availability + state.dt * (
            params.availability_replenish * (0.50 - state.availability)
            + params.availability_tension_gain * tension * (1.0 - state.availability)
            - params.actualization_depletion * actualization
        ),
        0.0,
        1.0,
    )

    # The latent direction is restored toward an independent source and turns
    # under relational tension. It never receives an A-to-P imitation term.
    turn = params.potential_turn * tension
    next_px = state.px + state.dt * (
        params.potential_transport * _laplacian(state.px)
        + params.potential_source_restore * (state.source_x - state.px)
        - turn * state.py
    )
    next_py = state.py + state.dt * (
        params.potential_transport * _laplacian(state.py)
        + params.potential_source_restore * (state.source_y - state.py)
        + turn * state.px
    )
    state.px, state.py = _unit(next_px, next_py)
    extra["actualization"] = actualization


def actuality_rule(state: BetaState, params: BetaParams, extra: dict) -> None:
    """Realized orientation responds to both relational context and available P."""
    theta = state.theta
    right, left = xp.roll(theta, -1, 1), xp.roll(theta, 1, 1)
    down, up = xp.roll(theta, -1, 0), xp.roll(theta, 1, 0)
    alignment = (
        state.rx * xp.sin(right - theta)
        + xp.roll(state.rx, 1, 1) * xp.sin(left - theta)
        + state.ry * xp.sin(down - theta)
        + xp.roll(state.ry, 1, 0) * xp.sin(up - theta)
    )
    p_angle = xp.arctan2(state.py, state.px)
    potential_torque = state.availability * xp.sin(p_angle - theta)
    state.theta = (theta + state.dt * (params.actual_alignment * alignment + params.potential_to_actual * potential_torque)) % (2.0 * xp.pi)


RULES = (relation_rule, potential_rule, actuality_rule)


def step(state: BetaState, params: BetaParams) -> BetaState:
    """Execute the named beta rules in their deliberate, documented order."""
    extra: dict = {}
    for rule in RULES:
        rule(state, params, extra)
    return state


def summary(state: BetaState) -> dict[str, float]:
    theta = np.asarray(to_cpu(state.theta))
    px, py = np.asarray(to_cpu(state.px)), np.asarray(to_cpu(state.py))
    availability = np.asarray(to_cpu(state.availability))
    rx, ry = np.asarray(to_cpu(state.rx)), np.asarray(to_cpu(state.ry))
    return {
        "actual_order": float(np.hypot(np.mean(np.cos(theta)), np.mean(np.sin(theta)))),
        "potential_strength": float(np.mean(availability)),
        "potential_actual_alignment": float(np.mean(np.cos(theta - np.arctan2(py, px)))),
        "relation_mean": float(0.5 * (np.mean(rx) + np.mean(ry))),
        "availability_std": float(np.std(availability)),
    }
