import math
from typing import Dict, List, Tuple, Optional

import numpy as np
from scipy.spatial import cKDTree

try:
    from .course_objects import TrackedDefect
except ImportError:
    from course_objects import TrackedDefect


class DefectTracker:
    """
    Passive tracker for vortex/antivortex defects.

    This does not modify the Genesis field.
    It only assigns persistent IDs to detected defects across frames.
    """

    def __init__(
        self,
        max_match_distance: float = 6.0,
        max_missed_frames: int = 5,
        annihilation_distance: float = 4.0,
        max_events: int = 2000,
    ):
        self.max_match_distance = float(max_match_distance)
        self.max_missed_frames = int(max_missed_frames)
        self.annihilation_distance = float(annihilation_distance)

        self.next_id = 1
        self.tracks: Dict[int, TrackedDefect] = {}

        # `events` is a bounded rolling log (memory-safe); `event_count` is the
        # true running total so the readout stays accurate even after trimming.
        self.events: List[dict] = []
        self.event_count = 0
        self.max_events = int(max_events)

    def _record_event(self, ev: dict) -> None:
        self.event_count += 1
        self.events.append(ev)
        if len(self.events) > self.max_events:
            del self.events[: len(self.events) - self.max_events]

    def _dist2(self, a: Tuple[float, float], b: Tuple[float, float]) -> float:
        dx = a[0] - b[0]
        dy = a[1] - b[1]
        return dx * dx + dy * dy

    def _build_candidates(self, detections, track_ids):
        """
        Return [(d2, det_idx, track_id), ...] for every detection/track pair of
        the same charge within max_match_distance.

        Equivalent to the old all-pairs loop, but a KDTree restricts the search
        to nearby pairs, so cost scales with matches found rather than
        len(tracks) * len(detections).
        """
        candidates = []
        r = self.max_match_distance

        # Group detection indices and track ids by charge.
        for charge in (+1, -1):
            det_idx = [i for i, (_, _, c) in enumerate(detections) if c == charge]
            tids = [t for t in track_ids if self.tracks[t].charge == charge]
            if not det_idx or not tids:
                continue

            det_pts = np.array(
                [(detections[i][0], detections[i][1]) for i in det_idx], dtype=float
            )
            track_pts = np.array(
                [(self.tracks[t].x, self.tracks[t].y) for t in tids], dtype=float
            )

            tree = cKDTree(track_pts)
            neighbor_lists = tree.query_ball_point(det_pts, r)

            for local_di, nbrs in enumerate(neighbor_lists):
                di = det_idx[local_di]
                dx0, dy0 = det_pts[local_di]
                for ti in nbrs:
                    tx, ty = track_pts[ti]
                    d2 = (dx0 - tx) ** 2 + (dy0 - ty) ** 2
                    candidates.append((d2, di, tids[ti]))

        return candidates

    def _sample_field(self, field, x: float, y: float) -> float:
        if field is None:
            return 0.0

        # x/y are usually image coordinates. Adjust if your convention is reversed.
        iy = int(round(y))
        ix = int(round(x))

        h, w = field.shape
        ix = max(0, min(w - 1, ix))
        iy = max(0, min(h - 1, iy))

        val = field[iy, ix]

        # Works for numpy scalars and cupy scalars if already transferred.
        try:
            return float(val)
        except TypeError:
            return float(val.get())

    def update(
        self,
        frame: int,
        detections: List[Tuple[float, float, int]],
        C=None,
        C_avg=None,
    ) -> List[TrackedDefect]:
        """
        detections should be a list of:
            (x, y, charge)

        charge should be +1 or -1.
        """

        unmatched_track_ids = set(self.tracks.keys())
        unmatched_detections = set(range(len(detections)))

        # Candidate matches: same charge, within max_match_distance.
        # Use a KDTree per charge so we only consider nearby pairs instead of
        # the full tracks x detections product (that all-pairs loop is what
        # made this bog down at high defect counts).
        candidates = self._build_candidates(detections, unmatched_track_ids)

        # Greedy nearest-neighbor matching.
        candidates.sort(key=lambda z: z[0])

        matched_tracks = set()
        matched_detections = set()

        for d2, det_idx, track_id in candidates:
            if det_idx in matched_detections:
                continue
            if track_id in matched_tracks:
                continue

            x, y, charge = detections[det_idx]

            local_C = self._sample_field(C, x, y)
            local_C_avg = self._sample_field(C_avg, x, y)

            self.tracks[track_id].update(
                frame=frame,
                x=x,
                y=y,
                local_C=local_C,
                local_C_avg=local_C_avg,
            )

            matched_tracks.add(track_id)
            matched_detections.add(det_idx)

        unmatched_track_ids -= matched_tracks
        unmatched_detections -= matched_detections

        # New detections become new tracks.
        for det_idx in unmatched_detections:
            x, y, charge = detections[det_idx]

            local_C = self._sample_field(C, x, y)
            local_C_avg = self._sample_field(C_avg, x, y)

            track = TrackedDefect(
                id=self.next_id,
                charge=int(charge),
                x=float(x),
                y=float(y),
                birth_frame=frame,
                last_seen_frame=frame,
                age=0,
                local_C=local_C,
                local_C_avg=local_C_avg,
                status="born",
            )
            track.trail.append((frame, float(x), float(y)))

            self.tracks[self.next_id] = track

            self._record_event({
                "frame": frame,
                "event": "birth",
                "id": self.next_id,
                "charge": int(charge),
                "x": float(x),
                "y": float(y),
            })

            self.next_id += 1

        # Mark stale tracks.
        stale_ids = []
        for track_id in list(unmatched_track_ids):
            tr = self.tracks[track_id]
            missed = frame - tr.last_seen_frame

            if missed > self.max_missed_frames:
                tr.status = "lost"
                stale_ids.append(track_id)

        # Before removing stale tracks, check possible annihilation candidates.
        self._detect_annihilation_candidates(frame, stale_ids)

        for track_id in stale_ids:
            tr = self.tracks[track_id]
            self._record_event({
                "frame": frame,
                "event": tr.status,
                "id": tr.id,
                "charge": tr.charge,
                "x": tr.x,
                "y": tr.y,
                "age": tr.age,
            })
            del self.tracks[track_id]

        return list(self.tracks.values())

    def _detect_annihilation_candidates(self, frame: int, stale_ids: List[int]) -> None:
        """
        Simple heuristic:
        If a + and - track both disappear near each other around the same time,
        mark them as annihilation candidates.
        """

        stale = [self.tracks[i] for i in stale_ids if i in self.tracks]

        used = set()

        for i, a in enumerate(stale):
            if a.id in used:
                continue

            best = None
            best_d2 = None

            for b in stale[i + 1:]:
                if b.id in used:
                    continue
                if a.charge + b.charge != 0:
                    continue

                d2 = self._dist2((a.x, a.y), (b.x, b.y))

                if d2 <= self.annihilation_distance * self.annihilation_distance:
                    if best is None or d2 < best_d2:
                        best = b
                        best_d2 = d2

            if best is not None:
                a.status = "annihilated_candidate"
                best.status = "annihilated_candidate"
                used.add(a.id)
                used.add(best.id)

                self._record_event({
                    "frame": frame,
                    "event": "annihilation_candidate",
                    "id_a": a.id,
                    "charge_a": a.charge,
                    "id_b": best.id,
                    "charge_b": best.charge,
                    "x": 0.5 * (a.x + best.x),
                    "y": 0.5 * (a.y + best.y),
                    "age_a": a.age,
                    "age_b": best.age,
                })

    def summary(self) -> dict:
        alive = list(self.tracks.values())
        pos = sum(1 for t in alive if t.charge > 0)
        neg = sum(1 for t in alive if t.charge < 0)

        if alive:
            avg_age = sum(t.age for t in alive) / len(alive)
            max_age = max(t.age for t in alive)
        else:
            avg_age = 0.0
            max_age = 0

        return {
            "alive": len(alive),
            "positive": pos,
            "negative": neg,
            "net_charge": pos - neg,
            "avg_age": avg_age,
            "max_age": max_age,
            "events": self.event_count,
        }
