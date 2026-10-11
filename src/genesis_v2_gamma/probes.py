"""Shared read-only measurement helpers for gamma experiments."""

from __future__ import annotations

import numpy as np


def angular_distance(first: np.ndarray, second: np.ndarray) -> np.ndarray:
    return np.abs(np.angle(np.exp(1j * (first - second))))


def disk(shape: tuple[int, int], center_y: int, center_x: int, radius: float) -> np.ndarray:
    yy, xx = np.indices(shape)
    return (yy - center_y) ** 2 + (xx - center_x) ** 2 <= radius**2


def outside_patch(reference: np.ndarray, radius: float, buffer: int) -> np.ndarray | None:
    """Choose the nearest equal disk fully outside a candidate and its buffer."""
    blocked = reference.copy()
    for _ in range(buffer):
        blocked |= np.roll(blocked, 1, 0) | np.roll(blocked, -1, 0) | np.roll(blocked, 1, 1) | np.roll(blocked, -1, 1)
    center_y, center_x = np.argwhere(reference).mean(axis=0)
    options = []
    for row in range(reference.shape[0]):
        for column in range(reference.shape[1]):
            candidate = disk(reference.shape, row, column, radius)
            if not np.any(candidate & blocked):
                options.append(((row - center_y) ** 2 + (column - center_x) ** 2, candidate))
    return min(options, key=lambda option: option[0])[1] if options else None


def best_overlap(reference: np.ndarray, regions) -> tuple[float, int]:
    scores = []
    for region in regions:
        union = np.logical_or(reference, region.mask).sum()
        scores.append((float(np.logical_and(reference, region.mask).sum() / union) if union else 0.0, region.area))
    return max(scores, default=(0.0, 0))
