"""Adapter for the scale-selection Genesis v2-delta hypothesis."""

from __future__ import annotations

from .core import DeltaParams, DeltaState, step as _step


class GenesisV2DeltaEngine:
    @property
    def name(self) -> str:
        return "genesis-v2-delta"

    @property
    def description(self) -> str:
        return "Short-range coherence with long-range counter-relation scale-selection hypothesis"

    @property
    def created(self) -> str:
        return "2026-10-11"

    def create_state(self, **kwargs) -> DeltaState:
        return DeltaState(kwargs.get("N", 100), kwargs.get("dt", 0.05), kwargs.get("seed"))

    def step(self, state: DeltaState, **kwargs) -> DeltaState:
        return _step(state, kwargs.get("params", DeltaParams()))
