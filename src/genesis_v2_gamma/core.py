"""Boundary-forming v2-gamma hypothesis; separate from beta."""
from __future__ import annotations

from dataclasses import dataclass

from src.genesis_grid.backend import xp
from src.genesis_v2_beta.core import BetaParams, BetaState, _edge_tension, actuality_rule, potential_rule


@dataclass
class GammaParams(BetaParams):
    boundary_rate: float = 0.18
    boundary_decay: float = 0.04
    boundary_permeability_floor: float = 0.04
    boundary_permeability_span: float = 0.82


class GammaState(BetaState):
    def __init__(self, N: int, dt: float = 0.05, seed: int | None = None):
        super().__init__(N, dt, seed)
        self.boundary_x = xp.zeros((N, N))
        self.boundary_y = xp.zeros((N, N))

    def clone(self):
        duplicate = super().clone()
        duplicate.__class__ = GammaState
        duplicate.boundary_x = self.boundary_x.copy()
        duplicate.boundary_y = self.boundary_y.copy()
        return duplicate


def boundary_rule(state: GammaState, params: GammaParams, extra: dict) -> None:
    """Persistent difference becomes a boundary that limits cross-edge flow."""
    tx, ty = _edge_tension(state.theta, state.px, state.py)
    state.boundary_x = xp.clip(state.boundary_x + state.dt * (params.boundary_rate * tx - params.boundary_decay * state.boundary_x), 0.0, 1.0)
    state.boundary_y = xp.clip(state.boundary_y + state.dt * (params.boundary_rate * ty - params.boundary_decay * state.boundary_y), 0.0, 1.0)
    state.rx = params.boundary_permeability_floor + params.boundary_permeability_span * (1.0 - state.boundary_x)
    state.ry = params.boundary_permeability_floor + params.boundary_permeability_span * (1.0 - state.boundary_y)
    extra["local_tension"] = 0.25 * (tx + xp.roll(tx, 1, 1) + ty + xp.roll(ty, 1, 0))


def step(state: GammaState, params: GammaParams) -> GammaState:
    extra = {}
    boundary_rule(state, params, extra)
    potential_rule(state, params, extra)
    actuality_rule(state, params, extra)
    return state
