"""Adapter for the v2-epsilon resource-renewal hypothesis."""

from .core import EpsilonParams, EpsilonState, step as _step


class GenesisV2EpsilonEngine:
    @property
    def name(self) -> str:
        return "genesis-v2-epsilon"

    @property
    def description(self) -> str:
        return "Gamma boundary dynamics with slow, renewable potential availability"

    @property
    def created(self) -> str:
        return "2026-10-11"

    def create_state(self, **kwargs) -> EpsilonState:
        return EpsilonState(kwargs.get("N", 100), kwargs.get("dt", 0.05), kwargs.get("seed"))

    def step(self, state: EpsilonState, **kwargs) -> EpsilonState:
        return _step(state, kwargs.get("params", EpsilonParams()))
