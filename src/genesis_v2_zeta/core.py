"""V2-zeta: a local coherence/refractory benchmark.

Coherent actuality is the local activator. It builds a delayed relational
refractory field, which spreads faster than coherence and directly suppresses
further alignment until it decays. This tests a genuine renewal loop without
using a global time pulse.
"""

from __future__ import annotations

from dataclasses import dataclass

from src.genesis_grid.backend import xp
from src.genesis_v2_beta.core import _laplacian, actuality_rule
from src.genesis_v2_epsilon.core import EpsilonParams, EpsilonState, local_coherence, renewal_rule
from src.genesis_v2_gamma.core import boundary_rule


@dataclass
class ZetaParams(EpsilonParams):
    refractory_production: float = 0.20
    refractory_decay: float = 0.035
    refractory_transport: float = 0.60
    refractory_alignment_gain: float = 0.85


class ZetaState(EpsilonState):
    def __init__(self, N: int, dt: float = 0.05, seed: int | None = None):
        super().__init__(N, dt, seed)
        self.refractory = xp.zeros((N, N))

    def clone(self):
        duplicate = super().clone()
        duplicate.__class__ = ZetaState
        duplicate.refractory = self.refractory.copy()
        return duplicate


def refractory_rule(state: ZetaState, params: ZetaParams, extra: dict) -> None:
    """Accumulate and spread a delayed local limit on realized coherence."""
    coherence = local_coherence(state.theta)
    state.refractory = xp.clip(
        state.refractory + state.dt * (
            params.refractory_production * coherence * coherence
            + params.refractory_transport * _laplacian(state.refractory)
            - params.refractory_decay * state.refractory
        ),
        0.0,
        1.0,
    )
    extra["refractory_alignment_scale"] = xp.clip(
        1.0 - params.refractory_alignment_gain * state.refractory,
        0.0,
        1.0,
    )


def refractory_actuality_rule(state: ZetaState, params: ZetaParams, extra: dict) -> None:
    """Apply the beta actuality rule with refractory-limited local alignment."""
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
    scale = extra["refractory_alignment_scale"]
    state.theta = (theta + state.dt * (params.actual_alignment * scale * alignment + params.potential_to_actual * potential_torque)) % (2.0 * xp.pi)


def step(state: ZetaState, params: ZetaParams) -> ZetaState:
    extra = {}
    boundary_rule(state, params, extra)
    renewal_rule(state, params, extra)
    refractory_rule(state, params, extra)
    refractory_actuality_rule(state, params, extra)
    return state
