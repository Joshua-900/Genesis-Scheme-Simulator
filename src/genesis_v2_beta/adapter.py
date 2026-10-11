"""Adapter for the experimental rule-based Genesis v2-beta engine."""

from __future__ import annotations

from .core import BetaParams, BetaState, step as _step


class GenesisV2BetaEngine:
    @property
    def name(self) -> str:
        return "genesis-v2-beta"

    @property
    def description(self) -> str:
        return "Rule-based coupled potentiality, actuality, and relation field engine"

    @property
    def created(self) -> str:
        return "2026-10-11"

    def create_state(self, **kwargs) -> BetaState:
        return BetaState(kwargs.get("N", 100), kwargs.get("dt", 0.05), kwargs.get("seed"))

    def step(self, state: BetaState, **kwargs) -> BetaState:
        return _step(state, kwargs.get("params", BetaParams()))
