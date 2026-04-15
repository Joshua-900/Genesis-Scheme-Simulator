# Adapter: wraps engine v1 (two-field reaction-diffusion) to conform to GenesisEngine.

from __future__ import annotations

import numpy as np
from .field2 import Field2
from .ops_genesis import step_genesis as _step_genesis


class EngineV1:
    """Engine v1 — two-field reaction-diffusion with Genesis tension feedback."""

    @property
    def name(self) -> str:
        return "engine-v1"

    @property
    def description(self) -> str:
        return "Two-field Gray-Scott with Genesis tension feedback"

    @property
    def created(self) -> str:
        return "2025-12-02"

    def create_state(self, **kwargs) -> Field2:
        size = kwargs.get("size", 512)
        U = np.ones((size, size), float)
        V = np.zeros((size, size), float)
        # central seed patch
        r = kwargs.get("seed_radius", 20)
        cy, cx = size // 2, size // 2
        U[cy - r:cy + r, cx - r:cx + r] = 0.50
        V[cy - r:cy + r, cx - r:cx + r] = 0.25
        return Field2(U, V)

    def step(self, state: Field2, **kwargs) -> Field2:
        return _step_genesis(
            state,
            Du=kwargs.get("Du", 0.5),
            Dv=kwargs.get("Dv", 0.0106),
            alpha=kwargs.get("alpha", 0.0214),
            beta=kwargs.get("beta", 0.00314),
            kappa=kwargs.get("kappa", 1e-7),
            T0=kwargs.get("T0", 0.5),
            dt=kwargs.get("dt", 0.02),
        )
