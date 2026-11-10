"""Periodic conservative tracking and local descriptors for motion experiments."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from src.genesis_audit.analysis import winding


KINEMATIC = ("charge", "age_updates", "vx", "vy", "partner_dx", "partner_dy", "partner_distance", "partner_observed")
ANGULAR = ("cos_mean", "sin_mean", "coherence", "cos_std", "sin_std", "cos_sin_mean", "winding_mean", "abs_winding_mean")
ANGULAR_EXTRA = ("cos2_mean", "sin2_mean", "cos3_mean", "sin3_mean", "x_cos", "y_cos", "x_sin", "y_sin")
STRUCTURAL = ("tau_mean", "tau_std", "C_mean", "C_std", "ux_mean", "uy_mean", "displacement_rms", "C_radial_moment")


def delta(a: np.ndarray, b: np.ndarray, n: int) -> np.ndarray:
    return (np.asarray(a) - np.asarray(b) + n / 2) % n - n / 2


@dataclass
class Track:
    id: int
    charge: int
    x: float
    y: float
    birth: int
    frame: int
    vx: float = 0.
    vy: float = 0.


class PeriodicTracker:
    """Mutual-nearest same-charge matches with distance and ambiguity gates.

    No gap bridging: unmatched IDs end immediately. A fresh ID never inherits
    an ended identity. This is conservative observed continuation, not a proof
    that disappearance is physical annihilation.
    """

    def __init__(self, n: int, maximum: float = 2.5, margin: float = .25):
        self.n, self.maximum, self.margin = n, maximum, margin
        self.tracks: dict[int, Track] = {}
        self.next_id = 1

    def update(self, theta: np.ndarray, frame: int) -> dict[int, Track]:
        charge = winding(theta)
        new = {}
        for sign in (1, -1):
            rc = np.argwhere(charge == sign)
            positions = rc[:, ::-1].astype(float) + .5
            old = sorted([t for t in self.tracks.values() if t.charge == sign], key=lambda t: t.id)
            matches = {}
            if len(old) and len(positions):
                previous = np.asarray([[t.x, t.y] for t in old])
                distances = np.linalg.norm(delta(previous[:, None, :], positions[None, :, :], self.n), axis=2)
                nearest_detection = distances.argmin(axis=1)
                nearest_track = distances.argmin(axis=0)
                for i, j in enumerate(nearest_detection):
                    if nearest_track[j] != i or distances[i, j] > self.maximum:
                        continue
                    row = np.sort(distances[i])
                    col = np.sort(distances[:, j])
                    if (len(row) > 1 and row[1] - row[0] < self.margin) or (len(col) > 1 and col[1] - col[0] < self.margin):
                        continue
                    matches[int(j)] = old[i]
            for j, (x, y) in enumerate(positions):
                previous = matches.get(j)
                if previous is None:
                    t = Track(self.next_id, sign, float(x), float(y), frame, frame)
                    self.next_id += 1
                else:
                    elapsed = frame - previous.frame
                    if elapsed <= 0:
                        raise ValueError("Tracker frames must strictly increase.")
                    velocity = delta(np.asarray([x, y]), np.asarray([previous.x, previous.y]), self.n) / elapsed
                    t = Track(previous.id, sign, float(x), float(y), previous.birth, frame, float(velocity[0]), float(velocity[1]))
                new[t.id] = t
        self.tracks = new
        return new


def disk(n: int, x: float, y: float, radius: float) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    rows, cols = np.indices((n, n))
    dx, dy = delta(cols, x, n), delta(rows, y, n)
    return dx * dx + dy * dy <= radius * radius, dx, dy


def choose_pair(tracks: dict[int, Track], snapshot: dict[str, np.ndarray], frame: int, minimum_age: int, minimum_distance: float, maximum_distance: float) -> tuple[int, int] | None:
    """Select using present state only: highest midpoint compression, then age."""
    n = len(snapshot["theta"])
    choices = []
    for plus in tracks.values():
        if plus.charge != 1 or frame - plus.birth < minimum_age:
            continue
        for minus in tracks.values():
            if minus.charge != -1 or frame - minus.birth < minimum_age:
                continue
            vector = delta(np.asarray([minus.x, minus.y]), np.asarray([plus.x, plus.y]), n)
            distance = float(np.linalg.norm(vector))
            if minimum_distance <= distance <= maximum_distance:
                midpoint = (np.asarray([plus.x, plus.y]) + vector / 2) % n
                mask, _, _ = disk(n, *midpoint, 5.)
                score = float(snapshot["C"][mask].mean())
                choices.append((score, min(frame - plus.birth, frame - minus.birth), -distance, -plus.id, -minus.id, plus.id, minus.id))
    return tuple(max(choices)[-2:]) if choices else None


def erase_structure(state, center: np.ndarray, radius: float) -> None:
    """Compact cosine taper; changes tau/ux/uy/C together, never theta."""
    mask, dx, dy = disk(state.N, *center, radius)
    weight = np.where(mask, .5 * (1 + np.cos(np.pi * np.sqrt(dx * dx + dy * dy) / radius)), 0.)
    for name in ("tau", "ux", "uy", "C"):
        setattr(state, name, getattr(state, name) * (1 - weight))


def features(snapshot: dict[str, np.ndarray], track: Track, partner: Track | None, frame: int, radius: float = 5.) -> dict[str, np.ndarray]:
    n = len(snapshot["theta"])
    mask, dx, dy = disk(n, track.x, track.y, radius)
    theta = snapshot["theta"][mask]
    c, s = np.cos(theta), np.sin(theta)
    charge = winding(snapshot["theta"])[mask]
    if partner is None:
        vector = np.zeros(2)
    else:
        vector = delta(np.asarray([partner.x, partner.y]), np.asarray([track.x, track.y]), n)
    common = [track.charge, frame - track.birth, track.vx, track.vy, *vector, np.linalg.norm(vector), float(partner is not None)]
    angular = [c.mean(), s.mean(), np.hypot(c.mean(), s.mean()), c.std(), s.std(), (c * s).mean(), charge.mean(), np.abs(charge).mean()]
    angular_extra = [np.cos(2 * theta).mean(), np.sin(2 * theta).mean(), np.cos(3 * theta).mean(), np.sin(3 * theta).mean(),
        (dx[mask] * c / radius).mean(), (dy[mask] * c / radius).mean(), (dx[mask] * s / radius).mean(), (dy[mask] * s / radius).mean()]
    tau, compression = snapshot["tau"][mask], snapshot["C"][mask]
    ux, uy = snapshot["ux"][mask], snapshot["uy"][mask]
    structure = [tau.mean(), tau.std(), compression.mean(), compression.std(), ux.mean(), uy.mean(), np.sqrt(np.mean(ux * ux + uy * uy)),
        (compression * np.sqrt(dx[mask] ** 2 + dy[mask] ** 2) / radius).mean()]
    return {"kinematic": np.asarray(common), "local_field": np.asarray(common + angular),
        "field_matched": np.asarray(common + angular + angular_extra), "structural": np.asarray(common + angular + structure)}
