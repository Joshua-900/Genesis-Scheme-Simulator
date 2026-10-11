"""Adapter for the boundary-forming Genesis v2-gamma hypothesis."""

from __future__ import annotations

from .core import GammaParams, GammaState, step as _step


class GenesisV2GammaEngine:
    @property
    def name(self) -> str:
        return "genesis-v2-gamma"

    @property
    def description(self) -> str:
        return "Boundary-forming potentiality, actuality, and relation field hypothesis"

    @property
    def created(self) -> str:
        return "2026-10-11"

    def create_state(self, **kwargs) -> GammaState:
        return GammaState(kwargs.get("N", 100), kwargs.get("dt", 0.05), kwargs.get("seed"))

    def step(self, state: GammaState, **kwargs) -> GammaState:
        return _step(state, kwargs.get("params", GammaParams()))
