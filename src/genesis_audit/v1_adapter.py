"""An opt-in caller of the unchanged V1 engine, isolated from V2 packages."""

from __future__ import annotations

import copy

import numpy as np

from src.genesis_grid import GenesisParams, GenesisState, rules_alignment, rules_compression, rules_curvature, rules_locking, step
from src.genesis_grid.backend import xp


FIELDS = ("theta", "tau", "ux", "uy", "C")
RULES = (rules_alignment.alignment_rule, rules_compression.compression_rule, rules_curvature.curvature_rule)


class V1Adapter:
    """Frozen V1 structural preset with explicitly named comparison pipelines.

    geometry_ablation sets kappa AND shell_geom_gain to zero: both pathways
    that can write geometric displacement are off. alignment_only runs only
    alignment, with locking off. Neither modifies an engine implementation.
    """

    def __init__(self, mode: str = "v1", kappa: float = .1, dt: float = .05):
        if xp is not np:
            raise ValueError("This reproducible audit requires GENESIS_USE_CUPY=False.")
        if mode not in ("v1", "geometry_ablation", "alignment_only"):
            raise ValueError(f"Unknown pipeline: {mode}")
        self.mode, self.dt = mode, dt
        self.params = GenesisParams()
        for key, value in dict(alpha=.30, gamma=.01, kappa=kappa, curv=.04, phase=0., dipole=0., triads=0., lock_strength=.96, phase_lock_gain=0., tri_lock_gain=0., shell_geom_gain=.08).items():
            setattr(self.params, key, value)
        self.rules = RULES
        if mode == "geometry_ablation":
            self.params.kappa = self.params.shell_geom_gain = 0.
        if mode == "alignment_only":
            self.rules = (rules_alignment.alignment_rule,)
            self.params.lock_strength = 0.

    def create(self, n: int, seed: int) -> GenesisState:
        # GenesisState initializes via the global NumPy RNG. Restore the caller's
        # RNG and use our own generator so audit runs do not alter caller RNG state.
        rng_state = np.random.get_state()
        try:
            state = GenesisState(n, self.dt)
        finally:
            np.random.set_state(rng_state)
        state.theta = np.random.default_rng(seed).uniform(0, 2 * np.pi, (n, n))
        return state

    def advance(self, state: GenesisState, frames: int) -> None:
        for _ in range(frames):
            step(state, self.params, self.rules, post=rules_locking.locking_postprocess)

    @staticmethod
    def snapshot(state: GenesisState) -> dict[str, np.ndarray]:
        return {name: np.asarray(getattr(state, name), dtype=np.float64).copy() for name in FIELDS}

    @staticmethod
    def clone(state: GenesisState) -> GenesisState:
        return copy.deepcopy(state)

    @staticmethod
    def perturb(state: GenesisState, center: tuple[int, int], amplitude: float, width: float) -> None:
        from .analysis import offsets

        dr, dc = offsets(state.N, center)
        state.theta = (state.theta + amplitude * np.exp(-(dr * dr + dc * dc) / (2 * width * width))) % (2 * np.pi)
