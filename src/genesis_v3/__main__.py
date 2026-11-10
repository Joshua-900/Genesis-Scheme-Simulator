"""Run the Genesis V3 seeded persistence experiment and emit JSON."""

import argparse
import json
import math
from pathlib import Path

from .model import fixture, measure, step


def run(size, duration, factor, samples, penalty=0., *, anisotropy=0., width=1.,
        support_radius=.25, kinds=('charged', 'uncharged', 'planar', 'uniform'),
        pair_separation=None, pair_phase=0.):
    # J=1 and dt/h² is the step factor.
    # The quartic term scales as 1/h² per bond to keep its physical weight fixed.
    h = width / (size - 1)
    steepness = penalty / h**2
    axis_weight = anisotropy * h**2
    dt_max = factor * h**2 / (1 + 12 * steepness + axis_weight)
    steps_per_sample = math.ceil(duration / samples / dt_max)
    dt = duration / (samples * steps_per_sample)
    if pair_separation is None:
        fields = {kind: fixture(size, kind, support_radius, width) for kind in kinds}
    else:
        half = pair_separation / 2
        left = fixture(size, 'charged', support_radius, width, center_x=-half)
        fields = {'isolated': left}
        for name, winding in (('same_charge', 1), ('opposite_charge', -1)):
            right = fixture(size, 'charged', support_radius, width, center_x=half,
                            winding=winding, phase=pair_phase)
            pair = left.copy()
            mask = right[..., 2] < 1
            pair[mask] = right[mask]
            fields[name] = pair
    records = []
    for sample in range(samples + 1):
        records.append(dict(time=sample * duration / samples,
                            fields={kind: measure(field, steepness, axis_weight, width)
                                    for kind, field in fields.items()}))
        if sample < samples:
            for _ in range(steps_per_sample):
                for field in fields.values():
                    step(field, dt / h**2, steepness, axis_weight)
    return dict(size=size, duration=duration, dt=dt, exchange_strength=1,
                boundary='fixed up', support_radius=support_radius, minimum_core_radius_cells=3,
                width=width, sharp_gradient_penalty=penalty, easy_axis=anisotropy,
                pair_separation=pair_separation, pair_phase=pair_phase, records=records)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--size', type=int, nargs='+', default=[65, 129])
    parser.add_argument('--duration', type=float, default=.01)
    parser.add_argument('--factor', type=float, default=.2, help='Upper bound on dt/h²')
    parser.add_argument('--samples', type=int, default=10)
    parser.add_argument('--penalty', type=float, default=0., help='Quartic bond penalty in squared domain units')
    parser.add_argument('--output', type=Path)
    parser.add_argument('--easy-axis', type=float, default=0., help='Energy cost of tilt away from either pole')
    parser.add_argument('--width', type=float, default=1., help='Physical domain width')
    parser.add_argument('--support-radius', type=float, default=.25, help='Initial distortion support radius')
    parser.add_argument('--charged-only', action='store_true', help='Run only the charged fixture')
    parser.add_argument('--pair-separation', type=float, help='Compare isolated, same-charge and opposite-charge textures')
    parser.add_argument('--pair-phase', type=float, default=0., help='Rotate the right texture internally by radians')
    args = parser.parse_args()
    if (any(size < 33 or size % 2 == 0 for size in args.size)
            or not math.isfinite(args.duration) or args.duration <= 0
            or not 0 < args.factor <= .2 or args.samples < 1
            or not math.isfinite(args.penalty) or args.penalty < 0):
        parser.error('Use odd sizes of at least 33, positive duration and samples, '
                     '0 < factor <= .2, and a finite nonnegative penalty.')
    if (not math.isfinite(args.width) or not 0 < args.support_radius < args.width / 2
            or not math.isfinite(args.easy_axis) or args.easy_axis < 0):
        parser.error('Use a finite nonnegative easy-axis strength and a support radius inside the domain.')
    options = dict(anisotropy=args.easy_axis, width=args.width, support_radius=args.support_radius)
    if args.charged_only:
        options['kinds'] = ('charged',)
    if not math.isfinite(args.pair_phase):
        parser.error('Pair phase must be finite.')
    if args.pair_separation is not None:
        half = args.pair_separation / 2
        if not args.support_radius <= half < args.width / 2 - args.support_radius:
            parser.error('Pair supports must be disjoint and inside the domain.')
        options['pair_separation'] = args.pair_separation
        options['pair_phase'] = args.pair_phase
    report = json.dumps([run(size, args.duration, args.factor, args.samples, args.penalty, **options)
                         for size in args.size],
                        indent=2, allow_nan=False) + '\n'
    if args.output:
        args.output.write_text(report, encoding='utf-8')
    else:
        print(report, end='')


if __name__ == '__main__':
    main()
