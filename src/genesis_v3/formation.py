"""Run a fixed-seed disorder quench with matched rule-off controls."""

import argparse
import json
import math
from pathlib import Path

import numpy as np
from scipy.ndimage import center_of_mass, convolve, label

from .model import charge_map, measure, step


def disorder(size, seed, tilt_bias=0.):
    """Smooth random angles on the unit square with a fixed north perimeter."""
    axis = np.linspace(0., 1., size)
    x, y = np.meshgrid(axis, axis)
    rng = np.random.default_rng(seed)
    azimuth, vertical = np.zeros_like(x), np.zeros_like(x)
    for k in range(1, 9):
        for j in range(1, 9):
            wave = np.sin(k * np.pi * x) * np.sin(j * np.pi * y)
            a, z = rng.normal(size=2) * np.exp(-(k*k + j*j) / 80)
            azimuth += a * wave
            vertical += z * wave
    edge = np.minimum.reduce((x, 1 - x, y, 1 - y))
    blend = np.clip(edge / .08, 0., 1.)
    blend = blend**2 * (3 - 2 * blend)
    z = 1 - blend * (1 - .45 * np.tanh(vertical / 2) - tilt_bias)
    horizontal = np.sqrt(np.maximum(1 - z*z, 0))
    return np.stack((horizontal * np.cos(azimuth), horizontal * np.sin(azimuth), z), axis=-1)


def planar_noise(size, seed):
    """Map two smooth random fields onto the sphere with a north perimeter."""
    axis = np.linspace(0., 1., size)
    x, y = np.meshgrid(axis, axis)
    rng = np.random.default_rng(seed)
    plane = np.zeros((size, size, 2))
    power = 0.
    for i in range(1, 6):
        for j in range(1, 6):
            wave = np.sin(i * np.pi * x) * np.sin(j * np.pi * y)
            coefficient = rng.normal(size=2) * np.exp(-(i*i + j*j) / 32)
            plane += wave[..., None] * coefficient
            power += float(coefficient @ coefficient) / 4
    plane *= 1.5 / np.sqrt(power)
    plane[[0, -1], :, :] = 0
    plane[:, [0, -1], :] = 0
    radius_sq = np.sum(plane**2, axis=-1)
    return np.concatenate((2 * plane, (1 - radius_sq)[..., None]), axis=-1) / (1 + radius_sq[..., None])


def localized(field, initial=False, *, labels_out=None, previous_labels=None, spacing=None):
    charge, ambiguous = charge_map(field)
    h = 1 / (len(field) - 1) if spacing is None else spacing
    half_cell = (np.arange(len(charge)) + .5) * h
    x, y = np.meshgrid(half_cell, half_cell)
    components, count = label(field[..., 2] < 0)
    if labels_out is not None:
        labels_out[:] = components
    sizes = np.bincount(components.ravel(), minlength=count + 1)
    ids = np.flatnonzero(sizes[1:] >= np.pi * 3**2) + 1
    centers = center_of_mass(1 - field[..., 2], components, ids)
    cores = []
    for component, (row, col) in zip(ids, centers):
        distance = (x - col*h)**2 + (y - row*h)**2
        q = float(charge[distance <= .09**2].sum())
        core = dict(x=col*h, y=row*h, charge=q, radius_cells=float(np.sqrt(sizes[component]/np.pi)))
        if labels_out is not None:
            mask = components == component
            rows, cols = np.nonzero(mask)
            core.update(component=int(component),
                        span=h * float(np.hypot(np.ptp(rows), np.ptp(cols))),
                        min_z=float(field[..., 2][mask].min()),
                        parents=[] if previous_labels is None else
                        [int(i) for i in np.unique(previous_labels[mask]) if i])
        cores.append(core)
    result = dict(charge=float(charge.sum()), ambiguous_triangles=ambiguous, cores=cores)
    if initial:
        axis = np.arange(-math.ceil(.09/h), math.ceil(.09/h) + 1) * h
        disk = axis[:, None]**2 + axis[None, :]**2 <= .09**2
        result['max_disk_charge'] = float(np.max(np.abs(convolve(charge, disk.astype(float), mode='constant'))))
    return result


def trial(size, seed, duration, penalty, easy_axis, samples, *, quench_sample=0,
          initial_field=None, track_walls=False):
    h = 1 / (size - 1)
    steepness, axis_weight = penalty / h**2, easy_axis * h**2
    field = disorder(size, seed) if initial_field is None else initial_field.copy()
    records = []
    previous_labels = None
    for sample in range(samples + 1):
        active = sample >= quench_sample
        gradient = steepness if active else 0.
        axis = axis_weight if active else 0.
        steps = math.ceil(duration / samples / (.2*h*h / (1 + 12*gradient + axis)))
        dt = duration / (samples * steps)
        labels = np.empty(field.shape[:2], dtype=np.int32) if track_walls else None
        reading = localized(field, initial=sample == 0, labels_out=labels,
                            previous_labels=previous_labels)
        previous_labels = labels
        reading.update(time=sample*duration/samples, energy=measure(field, gradient, axis)['energy'], dt=dt)
        records.append(reading)
        if sample < samples:
            for _ in range(steps):
                step(field, dt / h**2, gradient, axis)
    return dict(size=size, seed=seed, penalty=penalty, easy_axis=easy_axis, dt=dt,
                quench_time=quench_sample*duration/samples, records=records)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--size', type=int, nargs='+', default=[65, 97])
    parser.add_argument('--seed', type=int, nargs='+', default=[11, 22, 33])
    parser.add_argument('--duration', type=float, default=.08)
    parser.add_argument('--samples', type=int, default=16)
    parser.add_argument('--easy-axis', type=float, default=30.)
    parser.add_argument('--quench-sample', type=int, default=0,
                        help='Sample at which the stabilization rules switch on')
    parser.add_argument('--track-walls', action='store_true', help='Record component ancestry at each sample')
    parser.add_argument('--planar-noise', action='store_true', help='Use smooth stereographic disorder')
    parser.add_argument('--tilt-bias', type=float, default=0., help='Uniform interior tilt offset for angular disorder')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    if (any(n < 33 for n in args.size) or min(args.seed) < 0
            or not math.isfinite(args.duration) or args.duration <= 0 or args.samples < 1
            or not math.isfinite(args.easy_axis) or args.easy_axis < 0):
        parser.error('Use sizes of at least 33, nonnegative seeds and easy-axis strength, and positive duration and samples.')
    if not 0 <= args.quench_sample < args.samples:
        parser.error('Quench sample must be between zero and the last update interval.')
    if not -.5 <= args.tilt_bias <= .5 or (args.planar_noise and args.tilt_bias):
        parser.error('Tilt bias must be within ±0.5 and used with angular disorder.')
    results = [trial(n, seed, args.duration, penalty, axis, args.samples,
                     quench_sample=args.quench_sample if penalty else 0, track_walls=args.track_walls,
                     initial_field=planar_noise(n, seed) if args.planar_noise else disorder(n, seed, args.tilt_bias))
               for n in args.size for seed in args.seed
               for penalty, axis in ((.0002, args.easy_axis), (0., 0.))]
    report = json.dumps(results, indent=2, allow_nan=False) + '\n'
    if args.output:
        args.output.write_text(report, encoding='utf-8')
    else:
        print(report, end='')


if __name__ == '__main__':
    main()
