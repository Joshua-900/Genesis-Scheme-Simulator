# Adapter: wraps engine v0 (single-field duality) to conform to GenesisEngine.

from __future__ import annotations

import numpy as np
from .genesis_base_engine import Field, step as _step, tension


class EngineV0:
    """Engine v0 — single-field duality proof-of-concept."""

    @property
    def name(self) -> str:
        return "engine-v0"

    @property
    def description(self) -> str:
        return "Single-field duality: diffusion/growth on a 2D scalar grid"

    @property
    def created(self) -> str:
        return "2025-12-02"

    def create_state(self, **kwargs) -> Field:
        size = kwargs.get("size", 200)
        u0 = kwargs.get("u0", 0.5)
        F = np.random.rand(size, size).astype(float) * 0.1
        return Field(F, u0=u0)

    def step(self, state: Field, **kwargs) -> Field:
        return _step(
            state,
            alpha=kwargs.get("alpha", 0.2),
            beta=kwargs.get("beta", 0.5),
            gamma=kwargs.get("gamma", 0.0),
            dt=kwargs.get("dt", 1.0),
        )
