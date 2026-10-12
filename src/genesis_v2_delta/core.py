"""V2-delta: gamma plus short-range coherence and long-range counter-relation.

Delta tests a specific scale-selection hypothesis.  Gamma's local relations
cohere and then coarsen.  Delta keeps those local relations but adds a weaker,
broader contextual counter-torque so no one orientation can absorb the entire
field without opposition.  It is a separate hypothesis, not a gamma tuning.
"""

from __future__ import annotations

from dataclasses import dataclass

from src.genesis_grid.backend import xp
from src.genesis_v2_beta.core import _unit, potential_rule
from src.genesis_v2_gamma.core import GammaParams, GammaState, boundary_rule


@dataclass
class DeltaParams(GammaParams):
    long_range_passes: int = 8
    long_range_counter_gain: float = 0.08


class DeltaState(GammaState):
    def clone(self):
        duplicate = super().clone()
        duplicate.__class__ = DeltaState
        return duplicate


def scale_selection_rule(state: DeltaState, params: DeltaParams, extra: dict) -> None:
    """Oppose broad uniformity while leaving local relational coherence intact."""
    coarse_x, coarse_y = xp.cos(state.theta), xp.sin(state.theta)
    for _ in range(params.long_range_passes):
        coarse_x = (coarse_x + xp.roll(coarse_x, 1, 0) + xp.roll(coarse_x, -1, 0) + xp.roll(coarse_x, 1, 1) + xp.roll(coarse_x, -1, 1)) / 5.0
        coarse_y = (coarse_y + xp.roll(coarse_y, 1, 0) + xp.roll(coarse_y, -1, 0) + xp.roll(coarse_y, 1, 1) + xp.roll(coarse_y, -1, 1)) / 5.0
    coarse_x, coarse_y = _unit(coarse_x, coarse_y)
    actual_x, actual_y = xp.cos(state.theta), xp.sin(state.theta)
    # Cross-product torque points away from the coarse contextual direction.
    extra["scale_torque"] = -params.long_range_counter_gain * (actual_x * coarse_y - actual_y * coarse_x)


def actuality_rule(state: DeltaState, params: DeltaParams, extra: dict) -> None:
    theta = state.theta
    right, left = xp.roll(theta, -1, 1), xp.roll(theta, 1, 1)
    down, up = xp.roll(theta, -1, 0), xp.roll(theta, 1, 0)
    alignment = (state.rx * xp.sin(right - theta) + xp.roll(state.rx, 1, 1) * xp.sin(left - theta) + state.ry * xp.sin(down - theta) + xp.roll(state.ry, 1, 0) * xp.sin(up - theta))
    potential_angle = xp.arctan2(state.py, state.px)
    potential_torque = state.availability * xp.sin(potential_angle - theta)
    state.theta = (theta + state.dt * (params.actual_alignment * alignment + params.potential_to_actual * potential_torque + extra["scale_torque"])) % (2.0 * xp.pi)


RULES = (boundary_rule, potential_rule, scale_selection_rule, actuality_rule)


def step(state: DeltaState, params: DeltaParams) -> DeltaState:
    extra: dict = {}
    for rule in RULES:
        rule(state, params, extra)
    return state
