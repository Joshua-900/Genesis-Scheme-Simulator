"""Read-only coherent-region candidates for v2-beta."""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
from scipy import ndimage

from src.genesis_grid.backend import to_cpu


@dataclass
class Region:
    mask: np.ndarray
    area: int
    centroid_y: float
    centroid_x: float
    coherence: float
    boundary_contrast: float


@dataclass
class RegionTrack:
    id: int
    birth_frame: int
    last_seen_frame: int
    samples: int = 0
    max_area: int = 0
    mean_coherence_total: float = 0.0
    mean_boundary_total: float = 0.0
    missed: int = 0
    history: list[dict] = field(default_factory=list)

    def observe(self, frame: int, region: Region) -> None:
        self.last_seen_frame = frame
        self.samples += 1
        self.max_area = max(self.max_area, region.area)
        self.mean_coherence_total += region.coherence
        self.mean_boundary_total += region.boundary_contrast
        self.missed = 0
        self.history.append({"frame": frame, "area": region.area, "centroid": [region.centroid_y, region.centroid_x]})


def local_coherence(state) -> np.ndarray:
    theta = np.asarray(to_cpu(state.theta))
    neighbors = (np.cos(np.roll(theta, -1, 0) - theta) + np.cos(np.roll(theta, 1, 0) - theta) + np.cos(np.roll(theta, -1, 1) - theta) + np.cos(np.roll(theta, 1, 1) - theta)) / 4.0
    return 0.5 * (1.0 + neighbors)


def detect_regions(state, threshold: float = 0.94, min_area: int = 24) -> list[Region]:
    coherence = local_coherence(state)
    labels, count = ndimage.label(coherence >= threshold)
    theta = np.asarray(to_cpu(state.theta))
    regions = []
    for label in range(1, count + 1):
        mask = labels == label
        area = int(mask.sum())
        if area < min_area:
            continue
        ys, xs = np.nonzero(mask)
        edge = ndimage.binary_dilation(mask) & ~mask
        boundary = float(np.mean(np.abs(np.arctan2(np.sin(theta[edge][:, None] - theta[mask].mean()), np.cos(theta[edge][:, None] - theta[mask].mean()))))) if edge.any() else 0.0
        regions.append(Region(mask, area, float(ys.mean()), float(xs.mean()), float(coherence[mask].mean()), boundary))
    return regions


class RegionTracker:
    def __init__(self, min_iou: float = 0.25, max_missed: int = 2):
        self.min_iou, self.max_missed, self.next_id = min_iou, max_missed, 1
        self.active: dict[int, tuple[RegionTrack, np.ndarray]] = {}
        self.finished: list[RegionTrack] = []

    def update(self, frame: int, regions: list[Region]) -> None:
        unmatched = set(range(len(regions)))
        candidates = []
        for track_id, (_, prior) in self.active.items():
            for index, region in enumerate(regions):
                overlap = np.logical_and(prior, region.mask).sum()
                union = np.logical_or(prior, region.mask).sum()
                if union and overlap / union >= self.min_iou:
                    candidates.append((overlap / union, track_id, index))
        used = set()
        for _, track_id, index in sorted(candidates, reverse=True):
            if track_id in used or index not in unmatched:
                continue
            track, _ = self.active[track_id]
            track.observe(frame, regions[index])
            self.active[track_id] = (track, regions[index].mask)
            used.add(track_id); unmatched.remove(index)
        for index in unmatched:
            track = RegionTrack(self.next_id, frame, frame)
            track.observe(frame, regions[index])
            self.active[self.next_id] = (track, regions[index].mask); self.next_id += 1
        for track_id in list(self.active):
            if track_id not in used and all(self.active[track_id][1] is not region.mask for region in regions):
                track, mask = self.active[track_id]; track.missed += 1
                if track.missed > self.max_missed:
                    self.finished.append(track); del self.active[track_id]

    def reports(self, min_samples: int) -> list[dict]:
        tracks = self.finished + [track for track, _ in self.active.values()]
        return [{"id": t.id, "birth_frame": t.birth_frame, "last_seen_frame": t.last_seen_frame, "samples": t.samples, "max_area": t.max_area, "mean_coherence": t.mean_coherence_total / t.samples, "mean_boundary_contrast": t.mean_boundary_total / t.samples, "status": "persistent_candidate" if t.samples >= min_samples else "transient_candidate", "history": t.history} for t in tracks]


def detect_relation_domains(state, permeability_cutoff: float, min_area: int = 24) -> list[Region]:
    """Partition a field using its explicit right/down relation-edge strengths.

    This is a structural probe for gamma's proposed boundary mechanism, not an
    object detector by itself.  A cutoff is deliberately supplied by the
    experiment so its sensitivity can be reported rather than concealed.
    """
    theta = np.asarray(to_cpu(state.theta))
    rx, ry = np.asarray(to_cpu(state.rx)), np.asarray(to_cpu(state.ry))
    height, width = theta.shape
    parent = np.arange(height * width)

    def find(index: int) -> int:
        while parent[index] != index:
            parent[index] = parent[parent[index]]
            index = parent[index]
        return index

    def join(first: int, second: int) -> None:
        first, second = find(first), find(second)
        if first != second:
            parent[second] = first

    for row in range(height):
        for column in range(width):
            cell = row * width + column
            if rx[row, column] >= permeability_cutoff:
                join(cell, row * width + (column + 1) % width)
            if ry[row, column] >= permeability_cutoff:
                join(cell, ((row + 1) % height) * width + column)

    labels = np.array([find(index) for index in range(height * width)]).reshape(height, width)
    regions: list[Region] = []
    for label in np.unique(labels):
        mask = labels == label
        area = int(mask.sum())
        if area < min_area:
            continue
        ys, xs = np.nonzero(mask)
        angle = np.angle(np.mean(np.exp(1j * theta[mask])))
        coherence = float(np.mean(np.cos(theta[mask] - angle)))
        right_out = mask & ~np.roll(mask, -1, 1)
        down_out = mask & ~np.roll(mask, -1, 0)
        differences = []
        if right_out.any():
            differences.append(np.abs(np.angle(np.exp(1j * (np.roll(theta, -1, 1)[right_out] - theta[right_out])))))
        if down_out.any():
            differences.append(np.abs(np.angle(np.exp(1j * (np.roll(theta, -1, 0)[down_out] - theta[down_out])))))
        contrast = float(np.mean(np.concatenate(differences))) if differences else 0.0
        regions.append(Region(mask, area, float(ys.mean()), float(xs.mean()), coherence, contrast))
    return regions
