"""Adapter for the v2-zeta activator-refractory benchmark."""

from .core import ZetaParams, ZetaState, step as _step


class GenesisV2ZetaEngine:
    @property
    def name(self) -> str:
        return "genesis-v2-zeta"

    @property
    def description(self) -> str:
        return "Coherence-driven refractory renewal benchmark for bounded v2 domains"

    @property
    def created(self) -> str:
        return "2026-10-11"

    def create_state(self, **kwargs) -> ZetaState:
        return ZetaState(kwargs.get("N", 100), kwargs.get("dt", 0.05), kwargs.get("seed"))

    def step(self, state: ZetaState, **kwargs) -> ZetaState:
        return _step(state, kwargs.get("params", ZetaParams()))
