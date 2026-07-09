from dataclasses import dataclass, field
from typing import List, Optional, Tuple

# Cap trail length so long-lived tracks don't accumulate unbounded history.
MAX_TRAIL = 256


@dataclass
class TrackedDefect:
    id: int
    charge: int
    x: float
    y: float
    birth_frame: int
    last_seen_frame: int
    age: int = 0

    local_C: float = 0.0
    local_C_avg: float = 0.0

    vx: float = 0.0
    vy: float = 0.0

    status: str = "born"

    trail: List[Tuple[int, float, float]] = field(default_factory=list)

    def update(
        self,
        frame: int,
        x: float,
        y: float,
        local_C: float = 0.0,
        local_C_avg: float = 0.0,
    ) -> None:
        old_x, old_y = self.x, self.y

        self.x = float(x)
        self.y = float(y)
        self.vx = self.x - old_x
        self.vy = self.y - old_y

        self.last_seen_frame = frame
        self.age = frame - self.birth_frame
        self.local_C = float(local_C)
        self.local_C_avg = float(local_C_avg)
        self.status = "alive"
        self.trail.append((frame, self.x, self.y))
        if len(self.trail) > MAX_TRAIL:
            del self.trail[: len(self.trail) - MAX_TRAIL]
