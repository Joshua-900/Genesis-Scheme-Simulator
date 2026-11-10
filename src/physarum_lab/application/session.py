"""Playback and gradual guidance changes, expressed in simulation ticks."""
from __future__ import annotations

from dataclasses import dataclass
import math

from ..domain.model import Simulation


@dataclass
class Session:
    simulation: Simulation
    playing: bool = True
    guidance: float = 0.
    target_guidance: float = 0.
    transition_ticks: int = 100
    release_at: int | None = None

    def __post_init__(self):
        if not math.isfinite(self.target_guidance) or not 0 <= self.target_guidance <= 1:
            raise ValueError('Guidance must be finite and in 0..1')
        if self.release_at is not None and (type(self.release_at) is not int or self.release_at <= self.simulation.tick):
            raise ValueError('Scheduled release must be at a future tick')
        if not math.isfinite(self.guidance) or not 0 <= self.guidance <= 1:
            raise ValueError('Current guidance must be in 0..1')
        if not isinstance(self.transition_ticks, int) or self.transition_ticks < 1:
            raise ValueError('Transition duration must be a positive number of ticks')

    def guide(self, strength: float) -> None:
        if not math.isfinite(strength) or not 0 <= strength <= 1:
            raise ValueError('Guidance must be finite and in 0..1')
        self.target_guidance = float(strength)
        self.release_at = None

    def advance(self, count: int = 1, *, force: bool = False) -> None:
        if isinstance(count, bool) or not isinstance(count, int) or count < 0:
            raise ValueError('Step count must be a nonnegative integer')
        if not self.playing and not force:
            return
        for _ in range(count):
            delta = self.target_guidance - self.guidance
            next_guidance = self.guidance + max(-1 / self.transition_ticks, min(1 / self.transition_ticks, delta))
            self.simulation.step(guidance=next_guidance)
            self.guidance = next_guidance
            if self.release_at == self.simulation.tick:
                self.guide(0.)
