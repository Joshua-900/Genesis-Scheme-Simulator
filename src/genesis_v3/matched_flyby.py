"""Flybys matched in encounter phase with an impulse outside the donor core."""

import argparse
import json
import math
from pathlib import Path

import numpy as np

from .rotation import kick, precess
from .scattering import evolve, read, setup


def run(size):
    axis, h, left, right, support, steepness, axis_weight, transport, dx, dy = setup(size)
    x, y = np.meshgrid(axis, axis)
    radius = np.hypot(x+dx*h, y+dy*h)
    annulus = np.sin(np.pi*np.clip((radius-.065)/.060, 0, 1))**2
    annulus[radius >= .125] = 0
    interval = .0015
    steps = math.ceil(interval / (.1*h*h))
    dt = interval / steps
    encounter_sample = 12
    samples = 26
    args = (axis, h, dt, steps, steepness, axis_weight, transport)
    runs = {'right': evolve(right.copy(), *args, samples=samples)}
    fits = {}
    for strength in (0., .5, -.5):
        donor = left.copy()
        active = annulus > 0
        if strength:
            donor[active] = kick(left, strength, annulus)[active]

        def paired(phase):
            field = donor.copy()
            spins = right[support].copy()
            xy = (spins[:, 0] + 1j*spins[:, 1]) * np.exp(1j*phase)
            spins[:, 0], spins[:, 1] = xy.real, xy.imag
            field[support] = spins
            return field

        phase = math.pi
        corrections = []
        if strength:
            for _ in range(4):
                field = paired(phase)
                for _ in range(encounter_sample*steps):
                    precess(field, dt/h**2, steepness, axis_weight, transport)
                regions = read(field, axis, h)['regions']
                error = math.remainder(regions['right']['phase'] - regions['left']['phase'] - math.pi,
                                       2*math.pi)
                corrections.append(dict(phase=phase, error=error))
                if abs(error) < .015:
                    break
                phase -= error
        fits[str(strength)] = dict(start_phase=phase, trials=corrections)
        runs[f'pair_{strength}'] = evolve(paired(phase), *args, samples=samples)
        runs[f'left_{strength}'] = evolve(donor.copy(), *args, samples=samples)
    return dict(size=size, dt=dt, encounter_sample=encounter_sample,
                offsets=[dx*h, dy*h], fits=fits, runs=runs)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--size', type=int, nargs='+', default=[97, 113])
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    if any(size < 65 or size % 2 == 0 for size in args.size):
        parser.error('Use odd sizes of at least 65.')
    result = json.dumps([run(size) for size in args.size], indent=2, allow_nan=False) + '\n'
    if args.output:
        args.output.write_text(result, encoding='utf-8')
    else:
        print(result, end='')


if __name__ == '__main__':
    main()
