"""Track free travel of two opposite-charge V3 knots."""

import argparse
import json
import math
from pathlib import Path

import numpy as np

from .model import measure
from .rotation import precess, relaxed_knot
from .scattering import read


def run(size, distance, phase, duration, padding=0, factor=.1, prepared=None):
    h = 1 / (size - 1)
    knot, steepness, axis_weight = relaxed_knot(size) if prepared is None else prepared
    # Pad before shifting so the larger box uses exactly the same lattice spacing.
    width = 1 + 2*padding*h
    axis = np.linspace(-width/2, width/2, size+2*padding)
    xy = knot[..., 0] + 1j*knot[..., 1]
    z = knot[..., 2]
    w = np.where(z > -1+1e-12, xy/np.maximum(1+z, 1e-12), 1e6)
    w = np.pad(w, padding)
    shift = round(distance/(2*h))
    pair = np.roll(w, -shift, axis=1) + np.exp(1j*phase)*np.roll(w.conj(), shift, axis=1)
    denominator = 1 + np.abs(pair)**2
    field = np.stack((2*pair.real/denominator, 2*pair.imag/denominator, 2/denominator-1), axis=-1)
    field[[0, -1]] = (0, 0, 1)
    field[:, [0, -1]] = (0, 0, 1)
    samples = math.ceil(duration/.005)
    steps = math.ceil(duration/(samples*h*h*factor))
    dt = duration/(samples*steps)
    records = []
    for sample in range(samples+1):
        time = sample*duration/samples
        observation = read(field, axis, h)
        geometry = measure(field, steepness, axis_weight, width)
        rows, cols = np.nonzero(field[..., 2] < 0)
        extent = [h*(int(np.ptp(indices))+1) for indices in (cols, rows)] if len(rows) else None
        observation.update(time=time, energy=geometry['energy'], core_count=geometry['core_count'],
                           core_extent=extent)
        records.append(observation)
        left, right = observation['regions'].values()
        if left is None or right is None or observation['core_count'] != 2:
            break
        if sample < samples:
            for _ in range(steps):
                precess(field, dt/h**2, steepness, axis_weight)
    return dict(size=size, width=width, dt=dt, separation=2*shift*h, phase=phase,
                duration=duration, records=records)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--size', type=int, default=97)
    parser.add_argument('--separation', type=float, default=.19)
    parser.add_argument('--phase', type=float, default=0.)
    parser.add_argument('--duration', type=float, default=.1)
    parser.add_argument('--padding', type=int, default=0)
    parser.add_argument('--factor', type=float, default=.1)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    if (args.size < 65 or args.size % 2 == 0 or args.padding < 0
            or not .12 <= args.separation <= .4 or not math.isfinite(args.phase)
            or not 0 < args.duration <= 1 or not 0 < args.factor <= .1):
        parser.error('Use odd size ≥65, separation 0.12–0.4, positive duration ≤1 and step factor ≤0.1.')
    result = run(args.size, args.separation, args.phase, args.duration, args.padding, args.factor)
    report = json.dumps(result, indent=2, allow_nan=False) + '\n'
    if args.output:
        args.output.write_text(report, encoding='utf-8')
    else:
        print(report, end='')


if __name__ == '__main__':
    main()
