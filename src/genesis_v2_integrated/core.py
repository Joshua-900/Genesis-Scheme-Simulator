"""A V1-derived implementation of the potentiality/actuality bridge.

This module deliberately reuses the V1 structural loop:

    relational mismatch -> stored tension -> deformation -> compression

It adds potentiality as an independent directional field and records relation
as persistent edge-level incompatibility.  With every v2 coupling set to zero,
the update is intentionally identical to the V1 rule pipeline.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.genesis_grid import GenesisParams, GenesisState, rules_locking
from src.genesis_grid import rules_compression, rules_curvature
from src.genesis_grid.backend import xp
from src.genesis_grid.core import step as v1_step


@dataclass
class IntegratedParams(GenesisParams):
    """V1 parameters plus couplings that make P, A, and R causally distinct.

    All added couplings default to zero.  That is a regression guard, not a
    claim that zero coupling is a useful v2 regime: it preserves a known V1
    baseline while each new causal link is introduced and measured separately.
    """

    potential_transport: float = 0.0
    potential_source_restore: float = 0.0
    actuality_to_potential: float = 0.0
    potential_to_actual: float = 0.0
    potential_actual_tension: float = 0.0
    potential_neighbor_tension: float = 0.0
    relation_memory_rate: float = 0.0
    relation_memory_decay: float = 0.0
    relation_memory_tension: float = 0.0

    def __post_init__(self) -> None:
        # GenesisParams predates dataclasses, so explicitly initialize its
        # established V1 parameters before the bridge adds its own fields.
        GenesisParams.__init__(self)


class IntegratedState(GenesisState):
    """V1 structural state plus potentiality P and edge relation memory R."""

    def __init__(self, N: int, dt: float = 0.05, seed: int | None = None):
        if seed is not None:
            xp.random.seed(seed)
        super().__init__(N, dt)

        source_angle = xp.random.rand(N, N) * 2.0 * xp.pi
        self.source_px = xp.cos(source_angle)
        self.source_py = xp.sin(source_angle)
        self.px = self.source_px.copy()
        self.py = self.source_py.copy()

        # rx and ry live on rightward and downward edges.  They retain the
        # local history of incompatibility; tau remains V1's cell-level,
        # accumulated structural tension.
        self.rx = xp.zeros((N, N))
        self.ry = xp.zeros((N, N))


def _laplacian(field: Any) -> Any:
    return (
        xp.roll(field, -1, axis=0)
        + xp.roll(field, 1, axis=0)
        + xp.roll(field, -1, axis=1)
        + xp.roll(field, 1, axis=1)
        - 4.0 * field
    )


def _unit(x: Any, y: Any) -> tuple[Any, Any]:
    magnitude = xp.sqrt(x * x + y * y) + 1e-8
    return x / magnitude, y / magnitude


def relational_tension_rule(state: IntegratedState, params: IntegratedParams, extra: dict) -> dict:
    """Compute V1 alignment plus P/A/R mismatch without erasing V1 behavior."""
    theta = state.theta
    up = xp.roll(theta, -1, axis=0)
    down = xp.roll(theta, 1, axis=0)
    left = xp.roll(theta, -1, axis=1)
    right = xp.roll(theta, 1, axis=1)
    dtheta_align = xp.sin(up - theta) + xp.sin(down - theta) + xp.sin(left - theta) + xp.sin(right - theta)

    p_angle = xp.arctan2(state.py, state.px)
    potential_actual = 0.5 * (1.0 - xp.cos(p_angle - theta))

    actual_right = 0.5 * (1.0 - xp.cos(xp.roll(theta, -1, axis=1) - theta))
    actual_down = 0.5 * (1.0 - xp.cos(xp.roll(theta, -1, axis=0) - theta))
    potential_right = 0.5 * (1.0 - (state.px * xp.roll(state.px, -1, axis=1) + state.py * xp.roll(state.py, -1, axis=1)))
    potential_down = 0.5 * (1.0 - (state.px * xp.roll(state.px, -1, axis=0) + state.py * xp.roll(state.py, -1, axis=0)))
    relation_target_x = 0.5 * (actual_right + potential_right)
    relation_target_y = 0.5 * (actual_down + potential_down)

    if params.relation_memory_rate or params.relation_memory_decay:
        state.rx = xp.clip(
            state.rx + state.dt * (params.relation_memory_rate * (relation_target_x - state.rx) - params.relation_memory_decay * state.rx),
            0.0,
            1.0,
        )
        state.ry = xp.clip(
            state.ry + state.dt * (params.relation_memory_rate * (relation_target_y - state.ry) - params.relation_memory_decay * state.ry),
            0.0,
            1.0,
        )

    relation_memory = 0.25 * (
        state.rx + xp.roll(state.rx, 1, axis=1) + state.ry + xp.roll(state.ry, 1, axis=0)
    )
    relational_mismatch = (
        xp.abs(dtheta_align)
        + params.potential_actual_tension * potential_actual
        + params.potential_neighbor_tension * 0.5 * (relation_target_x + relation_target_y)
        + params.relation_memory_tension * relation_memory
    )

    # compression_rule reads grad_align.  Retaining that shared contract keeps
    # the V1 memory/deformation machinery intact while broadening its source.
    extra.update(
        dtheta_align=dtheta_align,
        grad_align=relational_mismatch,
        potential_actual_mismatch=potential_actual,
        relation_memory=relation_memory,
    )
    torque = params.alpha * dtheta_align + params.potential_to_actual * xp.sin(p_angle - theta)
    return {"torque": torque}


def potential_rule(state: IntegratedState, params: IntegratedParams, extra: dict) -> None:
    """Update P independently; actuality may influence it only by a named term."""
    if not (params.potential_transport or params.potential_source_restore or params.actuality_to_potential):
        return

    actual_x, actual_y = xp.cos(state.theta), xp.sin(state.theta)
    next_px = state.px + state.dt * (
        params.potential_transport * _laplacian(state.px)
        + params.potential_source_restore * (state.source_px - state.px)
        + params.actuality_to_potential * (actual_x - state.px)
    )
    next_py = state.py + state.dt * (
        params.potential_transport * _laplacian(state.py)
        + params.potential_source_restore * (state.source_py - state.py)
        + params.actuality_to_potential * (actual_y - state.py)
    )
    state.px, state.py = _unit(next_px, next_py)


# This is deliberately the same three-rule substrate used by
# genesis_object_census.py: alignment, compression, and curvature.  Optional
# V1 rules remain available to a future named bridge experiment, but they are
# not silently introduced into the baseline whose candidates we measure.
INTEGRATED_RULES = (
    relational_tension_rule,
    rules_compression.compression_rule,
    rules_curvature.curvature_rule,
    potential_rule,
)


def step(state: IntegratedState, params: IntegratedParams) -> IntegratedState:
    """Advance one V1-derived P/A/R step."""
    v1_step(state, params, INTEGRATED_RULES, post=rules_locking.locking_postprocess)
    return state
