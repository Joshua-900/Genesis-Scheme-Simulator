"""Exchange the region containing both knots between two wall-born fields."""

import argparse
import json
import math
from pathlib import Path

import numpy as np

from .formation import localized
from .model import charge_map, measure
from .rotation import precess
from .wall_handoff import opposite_pair, prepare


def pad_north(field, cells):
    if not cells:
        return field.copy()
    padded = np.zeros((len(field)+2*cells, len(field)+2*cells, 3))
    padded[..., 2] = 1
    padded[cells:-cells, cells:-cells] = field
    return padded


def swap(background, donor, background_center, donor_center, h):
    # Integer translation keeps the donor texture exact in the inner disk.
    dx, dy = np.rint((background_center-donor_center)/h).astype(int)
    translated = np.roll(donor, (dy, dx), axis=(0, 1))
    x, y = np.meshgrid(np.arange(len(background))*h, np.arange(len(background))*h)
    radius = np.hypot(x-background_center[0], y-background_center[1])
    blend = np.clip((.29-radius)/.07, 0, 1)
    width = (len(background)-1)*h
    edge = np.minimum.reduce((x, y, width-x, width-y))
    guard = np.clip(edge/.035, 0, 1)
    weight = (blend**2*(3-2*blend)*guard**2*(3-2*guard))[..., None]
    field = (1-weight)*background + weight*translated
    norms = np.linalg.norm(field, axis=-1, keepdims=True)
    if norms.min() < .1:
        raise ValueError('The swap crosses nearly opposite orientations in the blending region.')
    field /= norms
    return field, [int(dx), int(dy)], float(norms.min())


def pair_midpoint(field, h):
    pair = opposite_pair(localized(field, spacing=h), field=field, spacing=h)
    if pair is None:
        raise ValueError('Initial field does not contain a qualifying pair.')
    return np.mean([[core['x'], core['y']] for core in pair], axis=0)


def evolve(field, h, gradient, axis, duration, *, impulse_budget=False):
    samples = 16
    steps = math.ceil(duration/(samples*.08*h*h))
    dt = duration/(samples*steps)
    records, previous, parent_ids = [], None, None
    if impulse_budget:
        coordinates = (np.arange(len(field)-1)+.5)*h
        x, y = np.meshgrid(coordinates, coordinates)
        offset = (len(field)-1)*h/2
    for sample in range(samples+1):
        labels = np.empty(field.shape[:2], dtype=np.int32)
        reading = localized(field, labels_out=labels, previous_labels=previous, spacing=h)
        previous = labels
        reading.update(time=sample*duration/samples, energy=measure(field, gradient, axis)['energy'])
        records.append(reading)
        pair = opposite_pair(reading, field=field, spacing=h)
        if pair is None or (parent_ids is not None and any(
                parent not in core['parents'] for parent, core in zip(parent_ids, pair))):
            reading['tracking_limit'] = True
            break
        parent_ids = tuple(core['component'] for core in pair)
        points = np.array([[core['x'], core['y']] for core in pair])
        reading.update(separation=float(np.linalg.norm(points[0]-points[1])),
                       midpoint=points.mean(axis=0).tolist())
        if impulse_budget:
            charge, _ = charge_map(field)
            disks = [(x-cx)**2+(y-cy)**2 <= .09**2 for cx, cy in points]
            inside = disks[0] | disks[1]
            total = np.array([np.sum((coordinate-offset)*charge) for coordinate in (x, y)])
            cores = np.array([np.sum((coordinate[inside]-offset)*charge[inside])
                              for coordinate in (x, y)])
            reading['charge_moment'] = dict(total=total.tolist(), cores=cores.tolist(),
                                            exterior=(total-cores).tolist())
        if sample < samples:
            for _ in range(steps):
                precess(field, dt/h**2, gradient, axis)
    return records, dt


def run(size, output, *, padded=False):
    h = 1/(size-1)
    padding = (size-1)//8 if padded else 0
    traveling, _, gradient, axis = prepare(size, 405, mature=True)
    with np.load(output/f'damping_handoff_{size}.npz') as saved:
        contracting = saved['field']
    fields = {'traveling': pad_north(traveling, padding),
              'contracting': pad_north(contracting, padding)}
    centers = {name: pair_midpoint(field, h) for name, field in fields.items()}
    runs = {}
    for background in fields:
        for donor in fields:
            if donor == background:
                field, shift, minimum = fields[donor].copy(), [0, 0], 1.
            else:
                field, shift, minimum = swap(fields[background], fields[donor],
                                             centers[background], centers[donor], h)
            records, dt = evolve(field, h, gradient, axis, .04)
            runs[f'{donor}_pair_{background}_background'] = dict(
                donor=donor, background=background, shift_cells=shift,
                minimum_blend_norm=minimum, records=records)
    result = dict(size=size, width=1+2*padding*h, dt=dt, runs=runs)
    suffix = '' if padded else '_fixed_boundary'
    (output/f'pair_swap_{size}{suffix}.json').write_text(json.dumps(result, indent=2, allow_nan=False)+'\n',
                                                encoding='utf-8')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--size', type=int, choices=(113, 129), required=True)
    parser.add_argument('--padded', action='store_true', help='Move the boundary outward before the swap')
    args = parser.parse_args()
    run(args.size, Path('results/genesis_v3_fixed_rule'), padded=args.padded)


if __name__ == '__main__':
    main()
