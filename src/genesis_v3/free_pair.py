"""Predict undriven knot trajectories from a static interaction energy."""

import argparse
import json
import math
from pathlib import Path

import numpy as np
from scipy.ndimage import map_coordinates, spline_filter

from .model import measure
from .rotation import precess, relaxed_knot
from .scattering import read


def run(size, factor=.1):
    h = 1 / (size - 1)
    axis = np.linspace(-.5, .5, size)
    row, col = np.indices((size, size), dtype=float)
    relaxed, steepness, axis_weight = relaxed_knot(size)
    coefficients = [spline_filter(relaxed[..., i], mode='nearest') for i in range(3)]
    duration, samples = .008, 8
    steps = math.ceil(duration / (samples*h*h*factor))
    dt = duration / (samples*steps)

    def shifted(center):
        grid = (row, col-center/h)
        field = np.stack([map_coordinates(component, grid, mode='nearest', prefilter=False)
                          for component in coefficients], axis=-1)
        field /= np.linalg.norm(field, axis=-1, keepdims=True)
        return field

    def stereographic(field):
        z = field[..., 2]
        xy = field[..., 0] + 1j*field[..., 1]
        return np.where(z > -1 + 1e-12, xy / np.maximum(1+z, 1e-12), 1e6)

    def prepare(distance, phase):
        left, right = shifted(-distance/2), shifted(distance/2)
        w = stereographic(left) + phase*stereographic(right)
        norm = 1 + np.abs(w)**2
        field = np.stack((2*w.real/norm, 2*w.imag/norm, 2/norm-1), axis=-1)
        for state in (left, right, field):
            state[[0, -1]] = (0, 0, 1)
            state[:, [0, -1]] = (0, 0, 1)
        return field, left, right

    def interaction(distance, phase):
        field, left, right = prepare(distance, phase)
        energies = [measure(state, steepness, axis_weight)['energy'] for state in (field, left, right)]
        return energies[0] - energies[1] - energies[2]

    predictions = []
    for distance in (.19, .24, .29):
        for phase in (1, -1):
            field, left, _ = prepare(distance, phase)
            initial = read(field, axis, h)['regions']
            delta = h/4
            derivative = (interaction(distance+delta, phase) - interaction(distance-delta, phase))/(2*delta)
            radius = (initial['right']['x']-initial['left']['x'])/2
            omega = -derivative/(4*np.pi*initial['left']['charge']*radius)
            predictions.append((distance, phase, derivative, omega, field, left, initial))

    runs = []
    for distance, phase, derivative, omega, field, left, initial in predictions:
        records = []
        for sample in range(samples+1):
            time = sample*duration/samples
            reading = read(field, axis, h)
            solo = read(left, axis, h)['regions']['left']
            predicted = {}
            for name, point in initial.items():
                x, y = point['x'], point['y']
                predicted[name] = [x*math.cos(omega*time)-y*math.sin(omega*time),
                                   x*math.sin(omega*time)+y*math.cos(omega*time)]
            records.append(dict(time=time, predicted=predicted, solo_left=solo, **reading))
            if sample < samples:
                for _ in range(steps):
                    precess(field, dt/h**2, steepness, axis_weight)
                    precess(left, dt/h**2, steepness, axis_weight)
        runs.append(dict(distance=distance, phase=0 if phase==1 else math.pi,
                         energy_slope=derivative, predicted_omega=omega, records=records))
    return dict(size=size, dt=dt, duration=duration, runs=runs)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--size', type=int, nargs='+', default=[97, 113])
    parser.add_argument('--factor', type=float, default=.1)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    if any(size < 65 or size % 2 == 0 for size in args.size) or not 0 < args.factor <= .1:
        parser.error('Use odd sizes of at least 65 and 0 < factor <= 0.1.')
    report = json.dumps([run(n, args.factor) for n in args.size], indent=2, allow_nan=False) + '\n'
    if args.output:
        args.output.write_text(report, encoding='utf-8')
    else:
        print(report, end='')


if __name__ == '__main__':
    main()
