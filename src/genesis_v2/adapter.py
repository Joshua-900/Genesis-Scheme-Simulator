"""Adapter exposing the experimental v2 engine through GenesisEngine."""

from __future__ import annotations

from .core import V2Params, V2State, step as _step


class GenesisV2Engine:
    @property
    def name(self) -> str:
        return "genesis-v2"

    @property
    def description(self) -> str:
        return "Experimental coupled potentiality-actuality-relation field engine"

    @property
    def created(self) -> str:
        return "2026-10-11"

    def create_state(self, **kwargs) -> V2State:
        return V2State(kwargs.get("N", 100), kwargs.get("dt", 0.05), kwargs.get("seed"))

    def step(self, state: V2State, **kwargs) -> V2State:
        return _step(state, kwargs.get("params", V2Params()))
