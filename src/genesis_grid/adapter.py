# Adapter: wraps genesis_grid (modular rule-based engine) to conform to GenesisEngine.

from __future__ import annotations

from .core import GenesisState, GenesisParams, step as _step
from . import rules_alignment, rules_phase, rules_dipoles
from . import rules_triads, rules_curvature, rules_compression, rules_locking, relax

# Default rule set — the full 7-rule pipeline
DEFAULT_RULES = [
    rules_alignment.alignment_rule,
    rules_compression.compression_rule,
    relax.relaxation_rule,
    rules_phase.phase_rule,
    rules_dipoles.dipole_rule,
    rules_triads.triad_rule,
    rules_curvature.curvature_rule,
]


class GenesisGridEngine:
    """Genesis Grid — modular rule-based orientation field engine."""

    @property
    def name(self) -> str:
        return "genesis-grid"

    @property
    def description(self) -> str:
        return "Modular rule-based orientation field with 7 pluggable physics rules"

    @property
    def created(self) -> str:
        return "2025-12-02"

    def create_state(self, **kwargs) -> GenesisState:
        N = kwargs.get("N", 40)
        dt = kwargs.get("dt", 0.05)
        return GenesisState(N, dt)

    def step(self, state: GenesisState, **kwargs) -> GenesisState:
        params = kwargs.get("params", GenesisParams())
        rules = kwargs.get("rules", DEFAULT_RULES)
        post = kwargs.get("post", rules_locking.locking_postprocess)
        _step(state, params, rules, post=post)
        return state
