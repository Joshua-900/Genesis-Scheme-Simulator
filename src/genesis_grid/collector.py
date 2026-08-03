from pathlib import Path

import numpy as np

from .backend import to_cpu

class RawStateCollector:
    def __init__(
        self,
        every=1,
        max_frames=None,
        fields=("theta", "C"),
        dtype=np.float32,
    ):
        self.every = max(1, int(every))
        self.max_frames = max_frames
        self.fields = tuple(fields)
        self.dtype = dtype

        self.steps = []
        self.data = {name: [] for name in self.fields}

    def capture(self, frame, state):
        if frame % self.every != 0:
            return

        if self.max_frames is not None and len(self.steps) >= self.max_frames:
            return

        self.steps.append(frame)

        for name in self.fields:
            value = getattr(state, name)
            array = np.asarray(to_cpu(value), dtype=self.dtype)
            self.data[name].append(array.copy())

    def save(self, path, metadata=None):
        if not self.steps:
            raise RuntimeError("No frames have been captured.")

        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)

        payload = {
            "steps": np.asarray(self.steps, dtype=np.int64),
        }

        for name, frames in self.data.items():
            payload[name] = np.stack(frames)

        if metadata is not None:
            payload["metadata"] = np.array(metadata, dtype=object)

        np.savez(path, **payload)
        return path.resolve()

    @property
    def frame_count(self):
        return len(self.steps)