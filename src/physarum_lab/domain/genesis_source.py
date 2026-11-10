"""Read-only Genesis samples in Physarum's periodic coordinate system."""
from types import MappingProxyType

import numpy as np
from scipy.ndimage import map_coordinates

FIELD_NAMES = ('C', 'ux', 'uy')


class FrozenGenesis:
    def __init__(self, seed, tick, fields):
        self.seed, self.tick = seed, tick
        arrays = {name: np.asarray(fields[name], dtype=np.float32) for name in FIELD_NAMES}
        shape = arrays['C'].shape
        if (len(shape) != 2 or shape[0] != shape[1] or shape[0] < 2 or
                any(a.shape != shape or not np.isfinite(a).all() for a in arrays.values())):
            raise ValueError('Genesis fields must be finite arrays on the same square grid.')
        self.fields = MappingProxyType({
            name: np.frombuffer(array.tobytes(), dtype=np.float32).reshape(shape)
            for name, array in arrays.items()
        })

    def grid(self, size, names):
        width = self.fields['C'].shape[0]
        if width == size:
            return {name: self.fields[name] for name in names}
        axis = (np.arange(size, dtype=np.float32) + .5) * width / size - .5
        y, x = np.meshgrid(axis, axis, indexing='ij')
        return {name: map_coordinates(self.fields[name], (y, x), order=1, mode='grid-wrap')
                for name in names}

    def snapshot(self):
        return dict(seed=self.seed, tick=self.tick,
                    fields={name: array.tolist() for name, array in self.fields.items()})
