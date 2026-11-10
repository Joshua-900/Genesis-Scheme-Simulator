"""Matched lanes, local edits and deterministic recipe replay; no GUI state."""
from __future__ import annotations

import copy
import hashlib
from pathlib import Path

import numpy as np

from src.genesis_gallery import legacy

ROOT = Path(__file__).resolve().parents[2]
LANES = ('geometry_on', 'geometry_off')
LABELS = ('Geometry on', 'Geometry off')


def source_hashes():
    paths = (legacy.SOURCE, Path(legacy.__file__), Path(__file__))
    return {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}


class Sandbox:
    """Both lanes receive the same seed and timestamped brush prescriptions."""

    def __init__(self, seed=1, n=64):
        if not isinstance(n, int) or not 8 <= n <= 128:
            raise ValueError('Grid size must be an integer from 8 to 128.')
        if not isinstance(seed, int) or not 0 <= seed <= 2**32-1:
            raise ValueError('Seed must be an integer from 0 to 4294967295.')
        self.n, self.seed, self.update = n, seed, 0
        self.edits = []
        theta = np.random.default_rng(seed).uniform(0, 2*np.pi, (n, n))
        self.states, self.parameters = {}, {}
        for name in LANES:
            state = {key: np.zeros((n,n)) for key in ('tau', 'ux', 'uy', 'C')}
            state['theta'] = theta.copy()
            params = legacy.defaults()
            if name == 'geometry_off':
                params.update(kappa0=0., curv0=0., shell_geom_gain=0.)
            self.states[name], self.parameters[name] = state, params

    def advance(self, count=1):
        if not isinstance(count, int) or count < 0:
            raise ValueError('Update count must be a nonnegative integer.')
        for _ in range(count):
            for name in LANES:
                legacy.step(self.states[name], self.parameters[name])
            self.update += 1

    def paint(self, x, y, radius=4., angle=np.pi/2, mode='turn'):
        """Cosine-tapered disk; clipped at edges. Only theta is edited.

        Turn adds an angle; set follows the shortest circular path to a target.
        The prescription is identical in both lanes even after they diverge.
        """
        x, y, radius, angle = map(float, (x, y, radius, angle))
        if not all(np.isfinite(v) for v in (x,y,radius,angle)):
            raise ValueError('Brush values must be finite.')
        if not (0 <= x <= self.n-1 and 0 <= y <= self.n-1 and 0 < radius <= self.n):
            raise ValueError('Brush center or radius is outside the grid.')
        if mode not in ('turn', 'set'):
            raise ValueError('Brush mode must be turn or set.')
        rows, cols = np.indices((self.n,self.n))
        r = np.hypot(cols-x, rows-y)
        mask = r < radius
        weight = .5*(1+np.cos(np.pi*r[mask]/radius))
        for state in self.states.values():
            theta = state['theta']
            delta = angle if mode == 'turn' else (angle-theta[mask]+np.pi)%(2*np.pi)-np.pi
            theta[mask] = (theta[mask]+weight*delta)%(2*np.pi)
        self.edits.append(dict(update=self.update, x=x, y=y, radius=radius, angle=angle, mode=mode))

    def recipe(self):
        return dict(format='genesis-sandbox', version=1, seed=self.seed, n=self.n,
                    update=self.update, parameters=copy.deepcopy(self.parameters),
                    edits=copy.deepcopy(self.edits), source_sha256=source_hashes(),
                    initialization='default_rng(seed) uniform theta; other fields zero in both lanes',
                    brush='cosine disk clipped at grid edges; turn adds angle, set uses shortest circular path')

    @classmethod
    def replay(cls, recipe):
        if recipe.get('format') != 'genesis-sandbox' or recipe.get('version') != 1:
            raise ValueError('Unsupported sandbox recipe.')
        if recipe.get('source_sha256') != source_hashes():
            raise ValueError('Recipe dynamics source fingerprints differ from this checkout.')
        model = cls(recipe['seed'], recipe['n'])
        if recipe.get('parameters') != model.parameters:
            raise ValueError('Recipe parameters differ from the preserved presets.')
        end = recipe['update']
        if not isinstance(end,int) or end < 0:
            raise ValueError('Invalid final update.')
        for edit in recipe['edits']:
            tick = edit['update']
            if not isinstance(tick,int) or not model.update <= tick <= end:
                raise ValueError('Edits must be ordered within the replay interval.')
            model.advance(tick-model.update)
            model.paint(**{k:edit[k] for k in ('x','y','radius','angle','mode')})
        model.advance(end-model.update)
        return model
