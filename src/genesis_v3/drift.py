"""Test the charge-centroid drift predicted for an axial field gradient."""

import argparse
import json
import math
from pathlib import Path

import numpy as np

from .model import charge_map
from .rotation import kick, precess, relaxed_knot


def read(field, h, x, y):
    density, ambiguous = charge_map(field)
    charge = float(density.sum())
    deficit = float(h*h*np.sum(1 - field[..., 2]))
    rows, cols = np.nonzero(field[..., 2] < 0)
    core = float(np.sqrt(len(rows)/np.pi))
    core_center = [float(cols.mean()*h - .5), float(rows.mean()*h - .5)] if len(rows) else None
    return dict(charge=charge, ambiguous_triangles=ambiguous, axial_deficit=deficit,
                core_radius_cells=core, core_center=core_center,
                x=float(np.sum(x*density)/charge) if abs(charge) > .5 else None,
                y=float(np.sum(y*density)/charge) if abs(charge) > .5 else None)


def run(size, factor=.1, *, impulses=False):
    h = 1 / (size - 1)
    relaxed, steepness, axis_weight = relaxed_knot(size)
    axis = np.linspace(-.5, .5, size)
    mid = (axis[1:] + axis[:-1]) / 2
    x, y = np.meshgrid(mid, mid)
    duration, samples = .03, 12
    steps = math.ceil(duration / (samples*h*h*factor))
    dt = duration / (samples*steps)
    runs = []
    cases = ((150, 1, .25), (150, 1, -.25)) if impulses else (
        (0, 1, 0.), (150, 1, 0.), (-150, 1, 0.), (300, 1, 0.), (150, -1, 0.))
    for gradient, winding, impulse in cases:
        field = kick(relaxed, impulse) if impulse else relaxed.copy()
        field[..., 1] *= winding
        axial = gradient * h*h * axis[None, 1:-1] if gradient else None
        initial = read(field, h, x, y)
        predicted_vy = -gradient * initial['axial_deficit'] / (4*np.pi*initial['charge'])
        records = []
        for sample in range(samples + 1):
            records.append(dict(time=sample*duration/samples, **read(field, h, x, y)))
            if sample < samples:
                for _ in range(steps):
                    precess(field, dt/h**2, steepness, axis_weight, axial_field=axial)
        runs.append(dict(gradient=gradient, winding=winding, impulse=impulse, predicted_vy=predicted_vy,
                         records=records))
    return dict(size=size, dt=dt, duration=duration, runs=runs)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--size', type=int, nargs='+', default=[97, 113])
    parser.add_argument('--factor', type=float, default=.1)
    parser.add_argument('--impulses', action='store_true', help='Compare two axial deficits at the same gradient')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    if any(size < 65 or size % 2 == 0 for size in args.size) or not 0 < args.factor <= .1:
        parser.error('Use odd sizes of at least 65 and 0 < factor <= 0.1.')
    result = json.dumps([run(n, args.factor, impulses=args.impulses) for n in args.size],
                        indent=2, allow_nan=False) + '\n'
    if args.output:
        args.output.write_text(result, encoding='utf-8')
    else:
        print(result, end='')


if __name__ == '__main__':
    main()
