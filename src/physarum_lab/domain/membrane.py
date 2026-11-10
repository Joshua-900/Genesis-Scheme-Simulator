"""Overdamped differential growth of a single closed elastic loop."""
from dataclasses import dataclass

import numpy as np
from scipy.spatial import cKDTree

from .formulas import Expression


@dataclass
class Membrane:
    seed: int = 7
    max_nodes: int = 1200

    def __post_init__(self):
        rng = np.random.default_rng(self.seed)
        angle = np.linspace(0, 2 * np.pi, 96, endpoint=False)
        phase = rng.uniform(0, 2 * np.pi, 4)
        radius = .38 + sum(.008 * np.sin(k * angle + p) for k, p in zip(range(3, 7), phase))
        self.points = radius[:, None] * np.stack((np.cos(angle), np.sin(angle)), axis=1)
        self.rest = np.linalg.norm(np.roll(self.points, -1, axis=0) - self.points, axis=1)
        self.paint = np.zeros(len(angle))
        self.tick = 0
        self.initial_area = self.area
        self.expression = None

    @property
    def area(self):
        x, y = self.points.T
        return float(.5 * np.sum(x * np.roll(y, -1) - y * np.roll(x, -1)))

    def set_formula(self, source):
        candidate = Expression(source) if source.strip() else None
        if candidate is not None:
            candidate.evaluate(*self.points.T, self.tick / 60)
        self.expression = candidate

    def brush(self, x, y, radius=.11):
        distance = np.linalg.norm(self.points - (x, y), axis=1)
        self.paint = np.maximum(self.paint, np.clip(1 - distance / radius, 0, 1))

    def step(self, growth=1.):
        points = self.points
        multiplier = 1.
        if self.expression is not None:
            multiplier = np.clip(self.expression.evaluate(*points.T, (self.tick + 1) / 60), 0, 3)
        if len(points) < self.max_nodes:
            self.rest *= 1 + .0025 * growth * multiplier + .008 * self.paint
        self.paint *= .989

        previous = np.roll(points, 1, axis=0)
        following = np.roll(points, -1, axis=0)
        edge = following - points
        length = np.maximum(np.linalg.norm(edge, axis=1), 1e-10)
        spring = edge * ((length - self.rest) / length)[:, None]
        curvature = previous + following - 2 * points
        bending = 2 * curvature - np.roll(curvature, 1, axis=0) - np.roll(curvature, -1, axis=0)
        force = spring - np.roll(spring, 1, axis=0) + .65 * bending

        # Area pressure lets the outline expand slowly while excess length folds.
        tangent = following - previous
        normal = np.stack((tangent[:, 1], -tangent[:, 0]), axis=1)
        target_area = self.initial_area * (1 + .65 * (1 - np.exp(-self.tick / 600)))
        force += (target_area - self.area) * normal * .8

        cutoff = .044
        pairs = cKDTree(points).query_pairs(cutoff, output_type='ndarray')
        separation = pairs[:, 1] - pairs[:, 0]
        pairs = pairs[(separation > 2) & (separation < len(points) - 2)]
        left, right = pairs.T
        offset = points[left] - points[right]
        distance = np.maximum(np.linalg.norm(offset, axis=1), 1e-10)
        repel = offset * (.7 * (cutoff - distance) / distance)[:, None]
        np.add.at(force, left, repel)
        np.add.at(force, right, -repel)

        force -= 2 * np.sign(points) * np.maximum(np.abs(points) - .92, 0)
        displacement = force * .11
        norm = np.maximum(np.linalg.norm(displacement, axis=1), 1e-10)
        self.points = points + displacement * np.minimum(1, .003 / norm)[:, None]
        self._subdivide()
        self.tick += 1

    def _subdivide(self):
        available = self.max_nodes - len(self.points)
        split = np.flatnonzero(self.rest > .033)[:available]
        if not len(split):
            return
        following = (split + 1) % len(self.points)
        self.rest[split] *= .5
        self.points = np.insert(self.points, split + 1, (self.points[split] + self.points[following]) / 2, axis=0)
        self.rest = np.insert(self.rest, split + 1, self.rest[split])
        self.paint = np.insert(self.paint, split + 1, (self.paint[split] + self.paint[following]) / 2)
