"""Passive tracers that record samples from the live Genesis sheet."""
from collections import deque
from dataclasses import dataclass, field

import numpy as np

MAX_BALLS = 24
MAX_SAMPLES = 3600


@dataclass(frozen=True)
class Sample:
    x: float
    y: float
    compression: float
    angle: float
    tick: int
    wrapped: bool = False


@dataclass
class Ball:
    position: np.ndarray
    velocity: np.ndarray = field(default_factory=lambda: np.zeros(2))
    trail: deque = field(default_factory=lambda: deque(maxlen=600))


def height(compression):
    """Fixed log display scale so small changes remain legible."""
    return np.log1p(200 * np.clip(compression, 0, 1)) / np.log(201)


def sample_field(state, position):
    n = len(state['theta'])
    x, y = position
    col, row = int(np.floor(x)), int(np.floor(y))
    fx, fy = x - col, y - row
    rows = np.array([row, row, row + 1, row + 1]) % n
    cols = np.array([col, col + 1, col, col + 1]) % n
    weight = np.array([(1 - fx) * (1 - fy), fx * (1 - fy), (1 - fx) * fy, fx * fy])
    phase = np.dot(weight, np.exp(1j * state['theta'][rows, cols]))
    return (*(float(np.dot(weight, state[key][rows, cols])) for key in ('ux', 'uy', 'C')),
            float(np.angle(phase) % (2 * np.pi)))


class TrailSession:
    def __init__(self, model):
        self.model = model
        self.balls = []

    @property
    def state(self):
        return self.model.states['geometry_on']

    def drop(self, x, y, count=1):
        if not isinstance(count, int) or not 1 <= count <= MAX_BALLS:
            raise ValueError(f'Choose 1 to {MAX_BALLS} balls.')
        if count == 1:
            offsets = ((0, 0),)
        elif count == 3:
            offsets = ((-1.2, -.55), (0, .7), (1.2, -.55))
        else:
            angles = np.linspace(0, 2 * np.pi, count, endpoint=False)
            offsets = min(4., .7 * np.sqrt(count)) * np.column_stack((np.cos(angles), np.sin(angles)))
        for offset in offsets:
            position = (np.array([x, y]) + offset) % self.model.n
            ball = Ball(position)
            _, _, compression, angle = sample_field(self.state, position)
            ball.trail.append(Sample(*position, compression, angle, self.model.update))
            self.balls.append(ball)
        self.balls = self.balls[-MAX_BALLS:]
        capacity = min(600, MAX_SAMPLES // len(self.balls))
        for ball in self.balls:
            if ball.trail.maxlen != capacity:
                ball.trail = deque(ball.trail, maxlen=capacity)

    def advance(self, count=1):
        n = self.model.n
        for _ in range(count):
            self.model.advance()
            for ball in self.balls:
                ux, uy, _, _ = sample_field(self.state, ball.position)
                velocity = np.array([ux, uy])
                target = .9 * velocity / (.18 + np.linalg.norm(velocity))
                ball.velocity += .27 * (target - ball.velocity)
                destination = ball.position + ball.velocity
                wrapped = bool(np.any((destination < 0) | (destination >= n)))
                ball.position = destination % n
                _, _, compression, angle = sample_field(self.state, ball.position)
                ball.trail.append(Sample(*ball.position, compression, angle, self.model.update, wrapped))
