"""Measure the response of a second knot to a localized axial impulse."""

import argparse
import json
import math
from pathlib import Path

import numpy as np
from scipy.ndimage import center_of_mass, label

from .model import measure
from .rotation import kick, precess, relaxed_knot


def localized_knot(relaxed, radius):
    polar = np.arctan2(np.hypot(relaxed[..., 0], relaxed[..., 1]), relaxed[..., 2])
    phase = np.arctan2(relaxed[..., 1], relaxed[..., 0])
    window = np.clip((.125 - radius) / .035, 0, 1)
    polar *= window**2 * (3 - 2*window)
    return np.stack((np.sin(polar)*np.cos(phase), np.sin(polar)*np.sin(phase),
                     np.cos(polar)), axis=-1)


def read(field, reference, x, y, offset, h, steepness, axis_weight):
    reading = measure(field, steepness, axis_weight)
    components, count = label(field[..., 2] < 0)
    centers = center_of_mass(field[..., 2] < 0, components, range(1, count + 1))
    moment = (1 - field[..., 2]) * h*h
    regions = {}
    for name, sign in (('left', -1), ('right', 1)):
        candidates = [(row, col) for row, col in centers if sign * x[0, round(col)] > 0]
        cx = sign * offset
        cy = 0.
        if candidates:
            row, col = min(candidates, key=lambda point: abs(x[0, round(point[1])] - cx))
            cx, cy = col*h - .5, row*h - .5
        disk = (x - cx)**2 + (y - cy)**2 <= .10**2
        phase_disk = (x - sign*offset)**2 + y*y <= .10**2
        ref = reference[..., 0][phase_disk] + 1j*reference[..., 1][phase_disk]
        current = field[..., 0][phase_disk] + 1j*field[..., 1][phase_disk]
        overlap = np.vdot(ref, current)
        regions[name] = dict(moment=float(moment[disk].sum()),
                             fixed_moment=float(moment[phase_disk].sum()),
                             phase=float(np.angle(overlap)) if np.linalg.norm(ref) else None,
                             center=[cx, cy] if candidates else None)
    reading.update(total_moment=float(moment.sum()), regions=regions)
    return reading


def run(size, duration, factor, separation=.27, *, controls_only=False, delay=0.):
    h = 1 / (size - 1)
    axis = np.linspace(-.5, .5, size)
    x, y = np.meshgrid(axis, axis)
    relaxed, steepness, axis_weight = relaxed_knot(size)
    knot = localized_knot(relaxed, np.hypot(x, y))
    shift = round(separation / (2*h))
    offset = shift * h
    left, right = np.roll(knot, -shift, axis=1), np.roll(knot, shift, axis=1)
    support = (x - offset)**2 + y*y < .125**2
    samples = 28
    steps = math.ceil(duration / (samples*h*h*factor))
    dt = duration / (samples*steps)
    pair = left.copy()
    pair[support] = right[support]
    if delay:
        warmup_steps = math.ceil(delay / (h*h*factor))
        for field in (left, pair):
            for _ in range(warmup_steps):
                precess(field, delay / (warmup_steps*h*h), steepness, axis_weight)
    taper = np.clip((.125 - np.hypot(x + offset, y)) / .035, 0, 1)
    envelope = taper**2 * (3 - 2*taper) if delay else 1.
    runs = {}
    cases = (('rest', 0., True), ('positive', .25, True),
             ('negative', -.25, True), ('isolated', .25, False),
             ('isolated_rest', 0., False), ('isolated_negative', -.25, False))
    for name, strength, paired in cases[4:] if controls_only else cases:
        initial = pair if paired else left
        if delay:
            field = kick(initial, strength, envelope) if strength else initial.copy()
        else:
            field = kick(left, strength) if strength else left.copy()
        if paired and not delay:
            field[support] = right[support]
        reference = field.copy()
        records = []
        for sample in range(samples + 1):
            reading = read(field, reference, x, y, offset, h, steepness, axis_weight)
            reading['time'] = sample*duration/samples
            records.append(reading)
            if sample < samples:
                for _ in range(steps):
                    precess(field, dt/h**2, steepness, axis_weight)
        runs[name] = records
    return dict(size=size, duration=duration, dt=dt, separation=2*offset, delay=delay, runs=runs)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--size', type=int, nargs='+', default=[97, 113])
    parser.add_argument('--duration', type=float, default=.035)
    parser.add_argument('--factor', type=float, default=.10)
    parser.add_argument('--delay', type=float, default=0., help='Free evolution before the localized kick')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    if (any(size < 65 or size % 2 == 0 for size in args.size)
            or not math.isfinite(args.duration) or args.duration <= 0
            or not 0 < args.factor <= .1 or not math.isfinite(args.delay) or args.delay < 0):
        parser.error('Use odd sizes of at least 65, positive duration, 0 < factor <= .1, and nonnegative delay.')
    output = json.dumps([run(size, args.duration, args.factor, delay=args.delay) for size in args.size],
                        indent=2, allow_nan=False) + '\n'
    if args.output:
        args.output.write_text(output, encoding='utf-8')
    else:
        print(output, end='')


if __name__ == '__main__':
    main()
