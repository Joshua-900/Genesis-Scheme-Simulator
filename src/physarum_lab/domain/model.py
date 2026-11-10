"""Seeded moving agents coupled through a diffusing, evaporating trail.

Coordinates and sensors wrap on a square periodic domain. One tick is a model
step, never an elapsed wall-clock interval. Numerical arrays use float32;
particle deposits accumulate deterministically in CPU memory.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, replace
import math

import numpy as np
from scipy.ndimage import gaussian_filter, map_coordinates

from .fields import TAU, current_velocity, wave_field
from .formulas import FormulaField, FormulaSpec
from .genesis_source import FrozenGenesis


@dataclass(frozen=True)
class Rules:
    size: int = 640
    agents: int = 150_000
    sensor_distance: float = 12.0
    sensor_angle: float = .65
    turn_angle: float = .38
    speed: float = 1.35
    diffusion: float = .65
    retention: float = .965
    jitter: float = .025
    crowding: float = .0
    flow: float = 0.
    mode_m: int = 3
    mode_n: int = 5

    def __post_init__(self):
        for name in ('size', 'agents', 'mode_m', 'mode_n'):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int):
                raise ValueError(f'{name} must be an integer')
        if not 32 <= self.size <= 2048 or not 1 <= self.agents <= 2_000_000:
            raise ValueError('Size must be 32..2048; agents must be 1..2,000,000')
        if not 1 <= self.mode_m <= 12 or not 1 <= self.mode_n <= 12 or self.mode_m == self.mode_n:
            raise ValueError('Wave modes must be distinct integers in 1..12')
        limits = dict(sensor_distance=(1, 100), sensor_angle=(.01, math.pi),
                      turn_angle=(0, math.pi), speed=(.01, 10), diffusion=(0, 4),
                      retention=(0, .9999), jitter=(0, 1), crowding=(0, 10), flow=(0, 4))
        for name, (low, high) in limits.items():
            value = getattr(self, name)
            if not math.isfinite(value) or not low <= value <= high:
                raise ValueError(f'{name} must be finite and in {low}..{high}')


PRESETS = {
    'Silk': Rules(sensor_distance=5, sensor_angle=.8, turn_angle=.48,
                  crowding=2.5, flow=.8, diffusion=.55, retention=.975),
    'Estuary': Rules(sensor_distance=8, sensor_angle=.6, turn_angle=.3,
                     speed=1.65, diffusion=.7, retention=.985, jitter=.012, flow=1.4, crowding=3.),
    'Filigree': Rules(sensor_distance=9, sensor_angle=.95, turn_angle=.6,
                      speed=1.1, diffusion=.45, retention=.95, jitter=.035),
}


class Simulation:
    """Small interface: step, disturb, snapshot. All randomness belongs here."""

    def __init__(self, seed: int = 7, rules: Rules | None = None, *, genesis=None):
        if isinstance(seed, bool) or not isinstance(seed, int) or not 0 <= seed < 2**63:
            raise ValueError('Seed must be an integer in 0..2**63-1')
        self.seed, self.rules, self.tick = seed, rules or Rules(), 0
        self.genesis = genesis
        self.rng = np.random.default_rng(seed)
        r = self.rules
        # A populated disk leaves breathing room around the initial activity.
        angle = self.rng.uniform(0, TAU, r.agents)
        radius = np.sqrt(self.rng.random(r.agents)) * r.size * .395
        self.x = (r.size / 2 + np.cos(angle) * radius).astype(np.float32)
        self.y = (r.size / 2 + np.sin(angle) * radius).astype(np.float32)
        self.heading = self.rng.uniform(0, TAU, r.agents).astype(np.float32)
        self.trail = np.zeros((r.size, r.size), np.float32)
        self.density = np.zeros_like(self.trail)
        self.wave = wave_field(r.size, r.mode_m, r.mode_n)
        self.formula = None

    def _sense(self, field: np.ndarray, heading: np.ndarray) -> np.ndarray:
        r = self.rules
        col = np.floor(self.x + np.cos(heading) * r.sensor_distance).astype(np.int32) % r.size
        row = np.floor(self.y + np.sin(heading) * r.sensor_distance).astype(np.int32) % r.size
        return field[row, col]

    def step(self, count: int = 1, guidance: float = 0.) -> None:
        if isinstance(count, bool) or not isinstance(count, int) or count < 0:
            raise ValueError('Step count must be a nonnegative integer')
        if not math.isfinite(guidance) or not 0 <= guidance <= 1:
            raise ValueError('Guidance must be finite and in 0..1')
        for _ in range(count):
            self._advance(guidance, self._prepare(guidance))

    def _prepare(self, guidance):
        """Evaluate inputs before mutating either population."""
        r = self.rules
        custom_velocity = None
        wave = self.wave
        if self.formula is not None:
            # Validate all results before consuming RNG or changing state.
            values = self.formula.grid(r.size, self.tick + 1)
            spec = self.formula.spec
            response = spec.response
            if response == 'flow':
                if spec.velocity_x == spec.velocity_y == '0':
                    # The matched control has zero velocity everywhere.
                    custom_velocity = (0., 0.)
                    wave = values[0]
                else:
                    # The validated grid is cell-centered. Interpolate it across
                    # the same periodic domain the agents move through.
                    positions = (self.y - .5, self.x - .5)
                    custom_velocity = tuple(
                        map_coordinates(component, positions, order=1, mode='grid-wrap')
                        for component in values
                    )
                    wave = np.hypot(*values)
                attraction = 0.
            else:
                wave = values[0]
                attraction = (-18 * np.minimum(wave**2, 16) if response == 'zero'
                              else (6 if response == 'high' else -6) * np.clip(wave, -4, 4))
        score = ((1 - .5 * guidance) * np.log1p(self.trail) - 18 * guidance * wave**2
                 if self.formula is None else (1 - .5 * guidance) * np.log1p(self.trail) + guidance * attraction)
        if r.crowding:
            score -= r.crowding * np.log1p(gaussian_filter(self.density, 1.2, mode='wrap'))
        return score, wave, custom_velocity

    def _advance(self, guidance, prepared):
        r = self.rules
        score, self.wave, custom_velocity = prepared
        forward = self._sense(score, self.heading)
        left = self._sense(score, self.heading + r.sensor_angle)
        right = self._sense(score, self.heading - r.sensor_angle)
        turn = np.zeros(r.agents, np.float32)
        # Keep moving forward when it is the strongest sensor. At local
        # minima choose either side; all tie breaking uses the seeded RNG.
        trapped = (forward < left) & (forward < right)
        turn[trapped] = self.rng.choice((-1., 1.), int(trapped.sum()))
        turn[(left > right) & (left > forward) & ~trapped] = 1
        turn[(right > left) & (right > forward) & ~trapped] = -1
        noise = self.rng.uniform(-r.jitter, r.jitter, r.agents)
        self.heading[:] = (self.heading + r.turn_angle * turn + noise) % TAU
        dx, dy = np.cos(self.heading) * r.speed, np.sin(self.heading) * r.speed
        if r.flow:
            vx, vy = current_velocity(self.x, self.y, r.size, self.tick)
            flow = r.flow * (1 - guidance if custom_velocity is not None else 1 - .9 * guidance)
            dx, dy = dx + flow * vx, dy + flow * vy
        if custom_velocity is not None:
            dx += 3 * guidance * np.clip(custom_velocity[0], -4, 4)
            dy += 3 * guidance * np.clip(custom_velocity[1], -4, 4)
        self.x[:] = (self.x + dx) % r.size
        self.y[:] = (self.y + dy) % r.size
        # Float32 can round a remainder just below size up to size itself.
        self.x[self.x >= r.size] = 0
        self.y[self.y >= r.size] = 0
        index = self.y.astype(np.int32) * r.size + self.x.astype(np.int32)
        self.density[:] = np.bincount(index, minlength=r.size**2).reshape(r.size, r.size)
        # A small blur removes pixel locking without inventing particles.
        self.trail += self.density
        if r.diffusion:
            gaussian_filter(self.trail, r.diffusion, mode='wrap', output=self.trail)
        self.trail *= r.retention
        self.tick += 1

    def set_modes(self, m: int, n: int) -> None:
        rules = replace(self.rules, mode_m=m, mode_n=n)
        self.wave = wave_field(rules.size, m, n)
        self.rules = rules
        self.formula = None

    def set_formula(self, spec: FormulaSpec | None) -> None:
        """Apply transactionally; a rejected formula leaves the field unchanged."""
        candidate = FormulaField(spec, self.genesis) if spec is not None else None
        values = candidate.grid(self.rules.size, self.tick) if candidate is not None else None
        wave = (np.hypot(*values) if spec.response == 'flow' else values[0]) if spec is not None else wave_field(self.rules.size, self.rules.mode_m, self.rules.mode_n)
        self.formula, self.wave = candidate, wave

    def disturb(self, x: float, y: float, radius: float = 24., strength: float = 1.) -> None:
        """A local stir changes headings, not externally scripted trajectories."""
        if not all(math.isfinite(v) for v in (x, y, radius, strength)) or radius <= 0 or not 0 <= strength <= 1:
            raise ValueError('Brush values must be finite, radius positive, strength in 0..1')
        size = self.rules.size
        dx = (self.x - x + size / 2) % size - size / 2
        dy = (self.y - y + size / 2) % size - size / 2
        distance = np.hypot(dx, dy)
        mask = distance < radius
        target = np.arctan2(dy[mask], dx[mask]) + math.pi / 2
        delta = np.angle(np.exp(1j * (target - self.heading[mask])))
        self.heading[mask] = (self.heading[mask] + delta * strength * (1 - distance[mask] / radius)) % TAU

    def snapshot(self) -> dict:
        """Owned arrays: a caller can render/save without mutating live state."""
        import copy
        return dict(seed=self.seed, rules=asdict(self.rules), tick=self.tick,
                    genesis=self.genesis.snapshot() if self.genesis is not None else None,
                    formula=asdict(self.formula.spec) if self.formula is not None else None,
                    rng=copy.deepcopy(self.rng.bit_generator.state),
                    **{name: getattr(self, name).copy() for name in ('x', 'y', 'heading', 'trail', 'density')})

    @classmethod
    def restore(cls, snapshot: dict, *, genesis=None) -> Simulation:
        rules = Rules(**snapshot['rules'])
        if genesis is None and snapshot.get('genesis') is not None:
            genesis = FrozenGenesis(**snapshot['genesis'])
        result = cls(snapshot['seed'], rules, genesis=genesis)
        if not isinstance(snapshot['tick'], int) or snapshot['tick'] < 0:
            raise ValueError('Invalid snapshot tick')
        for name in ('x', 'y', 'heading', 'trail', 'density'):
            value = np.asarray(snapshot[name], dtype=np.float32)
            target = getattr(result, name)
            if value.shape != target.shape or not np.isfinite(value).all():
                raise ValueError(f'Invalid snapshot {name}')
            if name in ('trail', 'density') and (value < 0).any():
                raise ValueError(f'Negative snapshot {name}')
            target[:] = value
        if ((result.x < 0) | (result.x >= rules.size) | (result.y < 0) | (result.y >= rules.size)).any():
            raise ValueError('Snapshot positions outside domain')
        result.tick = snapshot['tick']
        result.rng.bit_generator.state = snapshot['rng']
        if snapshot.get('formula') is not None:
            result.set_formula(FormulaSpec(**snapshot['formula']))
        return result
