"""Change the field outside a fixed pair without translating either knot."""

import argparse
import json
from pathlib import Path

import numpy as np

from .formation import localized
from .pair_swap import evolve, pad_north
from .wall_handoff import opposite_pair


def run(size, output, *, impulse_budget=False):
    h = 1/(size-1)
    with np.load(output/f'damping_handoff_{size}.npz') as saved:
        initial = saved['field']
    pair = opposite_pair(localized(initial))
    a, b = np.array([[c['x'], c['y']] for c in pair])
    x, y = np.meshgrid(np.linspace(0, 1, size), np.linspace(0, 1, size))
    points = np.stack((x, y), axis=-1)
    segment = b-a
    fraction = np.clip((points-a)@segment/(segment@segment), 0, 1)
    radius = np.linalg.norm(points-a-fraction[..., None]*segment, axis=-1)
    weight = np.clip((radius-.10)/.055, 0, 1)
    weight = (weight**2*(3-2*weight))[..., None]
    polar = np.arctan2(np.hypot(initial[..., 0], initial[..., 1]), initial[..., 2])
    azimuth = np.arctan2(initial[..., 1], initial[..., 0])
    runs = {}
    conditions = (('native', 1., 0.), ('quiet', 0., 0.))
    if not impulse_budget:
        conditions += (('rotated', 1., np.pi),)
    for name, amplitude, rotation in conditions:
        field = initial.copy()
        p = polar*(1-weight[..., 0]*(1-amplitude))
        q = azimuth+weight[..., 0]*rotation
        mask = weight[..., 0] > 0
        field[mask] = np.stack((np.sin(p)*np.cos(q), np.sin(p)*np.sin(q), np.cos(p)), axis=-1)[mask]
        assert np.array_equal(field[~mask], initial[~mask])
        assert np.array_equal(field[[0, -1]], initial[[0, -1]])
        assert np.array_equal(field[:, [0, -1]], initial[:, [0, -1]])
        records, dt = evolve(field, h, .0002/h**2, 225*h**2, .04,
                             impulse_budget=impulse_budget)
        runs[name] = records
    if impulse_budget:
        padded = pad_north(initial, (size-1)//8)
        runs['widened'], dt = evolve(padded, h, .0002/h**2, 225*h**2, .04, impulse_budget=True)
    result = dict(size=size, dt=dt, inner_radius=.10, outer_radius=.155, runs=runs)
    prefix = 'impulse_budget' if impulse_budget else 'halo_probe'
    (output/f'{prefix}_{size}.json').write_text(json.dumps(result, indent=2, allow_nan=False)+'\n',
                                               encoding='utf-8')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--size', type=int, choices=(113, 129), required=True)
    parser.add_argument('--impulse-budget', action='store_true')
    args = parser.parse_args()
    run(args.size, Path('results/genesis_v3_fixed_rule'), impulse_budget=args.impulse_budget)


if __name__ == '__main__':
    main()
