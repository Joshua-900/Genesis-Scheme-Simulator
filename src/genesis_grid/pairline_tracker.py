"""Pairline tracking for Genesis Grid.

Passive relational tracker for vortex-antivortex pairs.

This module does not modify theta/tau/C or any field state. It only reads
tracked defect objects and creates higher-level PairLine objects.

Expected defect object attributes, by duck typing:
    id: int
    charge: +1 or -1
    x: float  # column coordinate
    y: float  # row coordinate
    age: optional
    status: optional

Typical usage inside the Napari tick loop:

    pair_tracker.update(
        frame=frame["i"],
        defect_tracks=defect_tracker.tracks.values(),
        C=C_now,
        C_avg=accum["C"],
    )
    pairline_layer.data = pair_tracker.as_napari_lines()
    pair_summary = pair_tracker.summary()

Napari line coordinates are returned as [[row, col], [row, col]], i.e. [[y,x],[y,x]].
"""

from __future__ import annotations

from dataclasses import dataclass, field
from math import atan2, hypot
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

import numpy as np


@dataclass
class PairLine:
    """A tracked relation between one + defect and one - defect."""

    id: int
    plus_id: int
    minus_id: int

    # Current endpoint positions. x=col, y=row.
    plus_x: float
    plus_y: float
    minus_x: float
    minus_y: float

    birth_frame: int
    last_seen_frame: int
    age: int = 0
    missed_frames: int = 0

    length: float = 0.0
    prev_length: Optional[float] = None
    length_change: float = 0.0
    closing_speed: float = 0.0  # positive means endpoints moved closer this update
    orientation: float = 0.0    # radians, atan2(dy, dx), plus -> minus
    midpoint_x: float = 0.0
    midpoint_y: float = 0.0

    mean_C_along_line: float = 0.0
    max_C_along_line: float = 0.0
    mean_C_avg_along_line: float = 0.0
    max_C_avg_along_line: float = 0.0

    # Passive relational accumulator. This is analysis-only unless a later
    # feedback module explicitly reads it.
    pair_tau: float = 0.0

    status: str = "active"  # active, lost, annihilation_candidate
    trail: List[Tuple[float, float, float]] = field(default_factory=list)  # midpoint trail: x,y,length

    def update(
        self,
        *,
        frame: int,
        plus_x: float,
        plus_y: float,
        minus_x: float,
        minus_y: float,
        mean_C: float = 0.0,
        max_C: float = 0.0,
        mean_C_avg: float = 0.0,
        max_C_avg: float = 0.0,
        pair_tau_decay: float = 0.98,
        pair_tau_length_gain: float = 0.05,
        pair_tau_cavg_gain: float = 0.01,
        max_trail: int = 256,
    ) -> None:
        self.prev_length = self.length if self.last_seen_frame != self.birth_frame or self.age > 0 else None

        self.plus_x = float(plus_x)
        self.plus_y = float(plus_y)
        self.minus_x = float(minus_x)
        self.minus_y = float(minus_y)

        dx = self.minus_x - self.plus_x
        dy = self.minus_y - self.plus_y

        new_length = hypot(dx, dy)
        self.length_change = 0.0 if self.prev_length is None else new_length - self.prev_length
        self.closing_speed = -self.length_change
        self.length = new_length
        self.orientation = atan2(dy, dx)
        self.midpoint_x = 0.5 * (self.plus_x + self.minus_x)
        self.midpoint_y = 0.5 * (self.plus_y + self.minus_y)

        self.mean_C_along_line = float(mean_C)
        self.max_C_along_line = float(max_C)
        self.mean_C_avg_along_line = float(mean_C_avg)
        self.max_C_avg_along_line = float(max_C_avg)

        # Analysis-only relational activity accumulator.
        # It rises when pair length changes and when the pair lies on persistent compression.
        self.pair_tau = (
            pair_tau_decay * self.pair_tau
            + pair_tau_length_gain * abs(self.length_change)
            + pair_tau_cavg_gain * self.mean_C_avg_along_line
        )

        self.last_seen_frame = int(frame)
        self.age = int(frame - self.birth_frame)
        self.missed_frames = 0
        self.status = "active"

        self.trail.append((self.midpoint_x, self.midpoint_y, self.length))
        if len(self.trail) > max_trail:
            self.trail = self.trail[-max_trail:]

    def mark_missed(self) -> None:
        self.missed_frames += 1

    def as_napari_line(self) -> np.ndarray:
        """Return one line in Napari coordinates: [[row,col], [row,col]]."""
        return np.array(
            [[self.plus_y, self.plus_x], [self.minus_y, self.minus_x]],
            dtype=np.float32,
        )


class PairLineTracker:
    """Tracks vortex-antivortex pairline relations from tracked defects.

    Pairing is intentionally simple and conservative:
      - split live defects into + and -
      - compute all distances
      - greedily match shortest unique pairs within max_pair_distance

    This gives stable first-pass pairlines without pretending we know the true
    interaction law yet.
    """

    def __init__(
        self,
        *,
        max_pair_distance: float = 64.0,
        max_missed_frames: int = 8,
        annihilation_distance: float = 4.0,
        pair_tau_decay: float = 0.98,
        pair_tau_length_gain: float = 0.05,
        pair_tau_cavg_gain: float = 0.01,
        line_sample_count: int = 32,
        max_trail: int = 256,
    ) -> None:
        self.max_pair_distance = float(max_pair_distance)
        self.max_missed_frames = int(max_missed_frames)
        self.annihilation_distance = float(annihilation_distance)
        self.pair_tau_decay = float(pair_tau_decay)
        self.pair_tau_length_gain = float(pair_tau_length_gain)
        self.pair_tau_cavg_gain = float(pair_tau_cavg_gain)
        self.line_sample_count = int(line_sample_count)
        self.max_trail = int(max_trail)

        self.pairs: Dict[Tuple[int, int], PairLine] = {}
        self.next_id: int = 1
        self.events: List[Dict[str, Any]] = []

    def reset(self) -> None:
        self.pairs.clear()
        self.events.clear()
        self.next_id = 1

    def update(
        self,
        *,
        frame: int,
        defect_tracks: Iterable[Any],
        C: Optional[np.ndarray] = None,
        C_avg: Optional[np.ndarray] = None,
    ) -> List[PairLine]:
        """Update pairlines from currently tracked defects.

        Args:
            frame: integer frame counter.
            defect_tracks: iterable of tracked defect objects. Needs id, charge, x, y.
            C: optional raw compression field for line sampling.
            C_avg: optional averaged compression field for line sampling.

        Returns:
            List of active PairLine objects after update.
        """
        plus_tracks, minus_tracks = self._split_live_defects(defect_tracks)
        matches = self._greedy_opposite_charge_matches(plus_tracks, minus_tracks)

        seen_keys = set()

        for plus, minus, distance in matches:
            plus_id = int(getattr(plus, "id"))
            minus_id = int(getattr(minus, "id"))
            key = (plus_id, minus_id)
            seen_keys.add(key)

            px, py = float(getattr(plus, "x")), float(getattr(plus, "y"))
            mx, my = float(getattr(minus, "x")), float(getattr(minus, "y"))

            mean_C, max_C = sample_line_stats(C, px, py, mx, my, self.line_sample_count)
            mean_C_avg, max_C_avg = sample_line_stats(C_avg, px, py, mx, my, self.line_sample_count)

            if key not in self.pairs:
                pair = PairLine(
                    id=self.next_id,
                    plus_id=plus_id,
                    minus_id=minus_id,
                    plus_x=px,
                    plus_y=py,
                    minus_x=mx,
                    minus_y=my,
                    birth_frame=int(frame),
                    last_seen_frame=int(frame),
                )
                self.next_id += 1
                self.pairs[key] = pair
                self.events.append({"frame": int(frame), "type": "pair_birth", "pair_id": pair.id, "key": key})

            self.pairs[key].update(
                frame=int(frame),
                plus_x=px,
                plus_y=py,
                minus_x=mx,
                minus_y=my,
                mean_C=mean_C,
                max_C=max_C,
                mean_C_avg=mean_C_avg,
                max_C_avg=max_C_avg,
                pair_tau_decay=self.pair_tau_decay,
                pair_tau_length_gain=self.pair_tau_length_gain,
                pair_tau_cavg_gain=self.pair_tau_cavg_gain,
                max_trail=self.max_trail,
            )

        # Handle pairs that were not matched this frame.
        to_delete: List[Tuple[int, int]] = []
        for key, pair in self.pairs.items():
            if key in seen_keys:
                continue

            pair.mark_missed()

            if pair.length <= self.annihilation_distance:
                pair.status = "annihilation_candidate"
                self.events.append(
                    {
                        "frame": int(frame),
                        "type": "annihilation_candidate",
                        "pair_id": pair.id,
                        "key": key,
                        "last_length": pair.length,
                        "age": pair.age,
                    }
                )

            if pair.missed_frames > self.max_missed_frames:
                pair.status = "lost"
                self.events.append(
                    {
                        "frame": int(frame),
                        "type": "pair_lost",
                        "pair_id": pair.id,
                        "key": key,
                        "last_length": pair.length,
                        "age": pair.age,
                    }
                )
                to_delete.append(key)

        for key in to_delete:
            self.pairs.pop(key, None)

        return self.active_pairs()

    def active_pairs(self) -> List[PairLine]:
        return [p for p in self.pairs.values() if p.status == "active"]

    def as_napari_lines(self) -> List[np.ndarray]:
        return [p.as_napari_line() for p in self.active_pairs()]

    def summary(self) -> Dict[str, Any]:
        pairs = self.active_pairs()
        n = len(pairs)
        if n == 0:
            return {
                "alive": 0,
                "avg_length": 0.0,
                "min_length": 0.0,
                "avg_closing_speed": 0.0,
                "closing_count": 0,
                "avg_C_avg": 0.0,
                "avg_pair_tau": 0.0,
                "events": len(self.events),
                "births": self.event_count("pair_birth"),
                "lost": self.event_count("pair_lost"),
                "annihilation_candidates": self.event_count("annihilation_candidate"),
            }

        lengths = np.array([p.length for p in pairs], dtype=float)
        closing = np.array([p.closing_speed for p in pairs], dtype=float)
        cavg = np.array([p.mean_C_avg_along_line for p in pairs], dtype=float)
        pair_tau = np.array([p.pair_tau for p in pairs], dtype=float)

        return {
            "alive": n,
            "avg_length": float(np.mean(lengths)),
            "min_length": float(np.min(lengths)),
            "avg_closing_speed": float(np.mean(closing)),
            "closing_count": int(np.sum(closing > 0.0)),
            "avg_C_avg": float(np.mean(cavg)),
            "avg_pair_tau": float(np.mean(pair_tau)),
            "events": len(self.events),
            "births": self.event_count("pair_birth"),
            "lost": self.event_count("pair_lost"),
            "annihilation_candidates": self.event_count("annihilation_candidate"),
        }

    def event_count(self, event_type: str) -> int:
        return sum(1 for e in self.events if e.get("type") == event_type)

    def _split_live_defects(self, defect_tracks: Iterable[Any]) -> Tuple[List[Any], List[Any]]:
        plus: List[Any] = []
        minus: List[Any] = []

        for tr in defect_tracks:
            # Skip stale/dead tracks if the defect tracker exposes a status.
            status = getattr(tr, "status", "active")
            if status not in ("active", "alive"):
                continue

            charge = int(getattr(tr, "charge"))
            if charge > 0:
                plus.append(tr)
            elif charge < 0:
                minus.append(tr)

        return plus, minus

    def _greedy_opposite_charge_matches(self, plus_tracks: Sequence[Any], minus_tracks: Sequence[Any]) -> List[Tuple[Any, Any, float]]:
        candidates: List[Tuple[float, Any, Any]] = []

        for p in plus_tracks:
            px, py = float(getattr(p, "x")), float(getattr(p, "y"))
            for m in minus_tracks:
                mx, my = float(getattr(m, "x")), float(getattr(m, "y"))
                d = hypot(mx - px, my - py)
                if d <= self.max_pair_distance:
                    candidates.append((d, p, m))

        candidates.sort(key=lambda item: item[0])

        used_plus = set()
        used_minus = set()
        matches: List[Tuple[Any, Any, float]] = []

        for d, p, m in candidates:
            pid = int(getattr(p, "id"))
            mid = int(getattr(m, "id"))
            if pid in used_plus or mid in used_minus:
                continue
            used_plus.add(pid)
            used_minus.add(mid)
            matches.append((p, m, d))

        return matches


def sample_line_stats(
    field: Optional[np.ndarray],
    x1: float,
    y1: float,
    x2: float,
    y2: float,
    sample_count: int = 32,
) -> Tuple[float, float]:
    """Sample a scalar field along a line and return mean/max.

    Coordinates use x=col, y=row. Sampling uses nearest-neighbor indexing.
    If field is None or empty, returns (0.0, 0.0).
    """
    if field is None:
        return 0.0, 0.0

    arr = np.asarray(field)
    if arr.ndim != 2 or arr.size == 0:
        return 0.0, 0.0

    h, w = arr.shape
    n = max(2, int(sample_count))

    xs = np.linspace(float(x1), float(x2), n)
    ys = np.linspace(float(y1), float(y2), n)

    cols = np.clip(np.rint(xs).astype(int), 0, w - 1)
    rows = np.clip(np.rint(ys).astype(int), 0, h - 1)

    values = arr[rows, cols].astype(float)
    if values.size == 0:
        return 0.0, 0.0

    return float(np.mean(values)), float(np.max(values))
