"""V2-epsilon: gamma boundaries plus slow potential-resource renewal.

This is a distinct hypothesis, not a retuning of gamma. Coherent actuality
uses local potential availability; availability diffuses and replenishes more
slowly. The proposed role is to prevent one coherent region from retaining
unlimited fuel for further consolidation.
"""

from __future__ import annotations

from dataclasses import dataclass

from src.genesis_grid.backend import xp
from src.genesis_v2_beta.core import _laplacian, _unit, actuality_rule
from src.genesis_v2_gamma.core import GammaParams, GammaState, boundary_rule


@dataclass
class EpsilonParams(GammaParams):
    availability_transport: float = 0.22
    availability_replenish: float = 0.035
    coherence_depletion: float = 0.50
    baseline_depletion: float = 0.005


class EpsilonState(GammaState):
    def clone(self):
        duplicate = super().clone()
        duplicate.__class__ = EpsilonState
        return duplicate


def local_coherence(theta):
    """Return local realized agreement in [0, 1]."""
    agreement = (
        xp.cos(xp.roll(theta, -1, 0) - theta)
        + xp.cos(xp.roll(theta, 1, 0) - theta)
        + xp.cos(xp.roll(theta, -1, 1) - theta)
        + xp.cos(xp.roll(theta, 1, 1) - theta)
    ) * 0.25
    return 0.5 * (agreement + 1.0)


def renewal_rule(state: EpsilonState, params: EpsilonParams, extra: dict) -> None:
    """Renew and transport P availability while coherence consumes it slowly."""
    coherence = local_coherence(state.theta)
    consumption = state.availability * (params.baseline_depletion + params.coherence_depletion * coherence)
    state.availability = xp.clip(
        state.availability + state.dt * (
            params.availability_transport * _laplacian(state.availability)
            + params.availability_replenish * (0.50 - state.availability)
            - consumption
        ),
        0.0,
        1.0,
    )

    # Latent direction remains independent of actual orientation, as in beta.
    tension = extra["local_tension"]
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
    extra["coherence"] = coherence
    extra["resource_consumption"] = consumption


def step(state: EpsilonState, params: EpsilonParams) -> EpsilonState:
    extra = {}
    boundary_rule(state, params, extra)
    renewal_rule(state, params, extra)
    actuality_rule(state, params, extra)
    return state
