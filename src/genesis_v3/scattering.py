"""Compare driven V3 flybys against the same knots traveling alone."""

import argparse
import json
import math
from pathlib import Path

import numpy as np

from .model import charge_map
from .rotation import kick, precess, relaxed_knot
from .transfer import localized_knot


def read(field, axis, h):
    charge, ambiguous = charge_map(field)
    mid = (axis[1:] + axis[:-1]) / 2
    x, y = np.meshgrid(mid, mid)
    sx, sy = np.meshgrid(axis, axis)
    regions = {}
    for name, sign in (('left', -1), ('right', 1)):
        side = sign*x > 0
        q = float(charge[side].sum())
        if abs(q) < .5 or ambiguous:
            regions[name] = None
            continue
        cx = float(np.sum(x[side]*charge[side])/q)
        cy = float(np.sum(y[side]*charge[side])/q)
        disk = (sx-cx)**2 + (sy-cy)**2 < .10**2
        moment = float(h*h*np.sum(1-field[..., 2][disk]))
        direction = np.arctan2(sy[disk]-cy, sx[disk]-cx)
        transverse = field[..., 0][disk] + 1j*field[..., 1][disk]
        phase = np.angle(np.sum(transverse*np.exp(-1j*direction)))
        core = (field[..., 2] < 0) & (sign*sx > 0)
        core_radius = h * float(np.sqrt(np.count_nonzero(core)/np.pi))
        regions[name] = dict(charge=q, x=cx, y=cy, moment=moment, phase=float(phase),
                             core_radius=core_radius)
    return dict(regions=regions, ambiguous_triangles=ambiguous,
                total_moment=float(h*h*np.sum(1-field[..., 2])),
                max_norm_error=float(np.max(np.abs(np.linalg.norm(field, axis=-1)-1))))


def setup(size):
    h = 1 / (size - 1)
    axis = np.linspace(-.5, .5, size)
    x, y = np.meshgrid(axis, axis)
    relaxed, steepness, axis_weight = relaxed_knot(size)
    knot = localized_knot(relaxed, np.hypot(x, y))
    dx, dy = round(.137/h), round(.085/h)
    left = np.roll(knot, (-dy, -dx), axis=(0, 1))
    right = np.roll(knot, (dy, dx), axis=(0, 1))
    right_support = (x-dx*h)**2 + (y-dy*h)**2 < .125**2
    # The prescribed flow is along y, with opposite directions on either side.
    transport = (-5 * np.tanh(x[1:-1, 1:-1]/.04) * h/2)[..., None]
    return axis, h, left, right, right_support, steepness, axis_weight, transport, dx, dy


def run(size, duration=.045, factor=.1):
    axis, h, left, right, right_support, steepness, axis_weight, transport, dx, dy = setup(size)
    steps = math.ceil(duration / (30*h*h*factor))
    dt = duration / (30*steps)
    runs = {}
    for phase in (0, math.pi):
        rotated = right.copy()
        if phase:
            rotated[..., :2] *= -1
        for impulse in (0., .25, -.25):
            field = kick(left, impulse) if impulse else left.copy()
            field[right_support] = rotated[right_support]
            runs[f'pair_{round(phase)}_{impulse}'] = evolve(
                field, axis, h, dt, steps, steepness, axis_weight, transport)
    for impulse in (0., .25, -.25):
        field = kick(left, impulse) if impulse else left.copy()
        runs[f'left_{impulse}'] = evolve(field, axis, h, dt, steps, steepness, axis_weight, transport)
    runs['right'] = evolve(right.copy(), axis, h, dt, steps, steepness, axis_weight, transport)
    return dict(size=size, duration=duration, dt=dt, flow_speed=5,
                start_offset=[dx*h, dy*h], runs=runs)


def evolve(field, axis, h, dt, steps, steepness, axis_weight, transport, samples=30):
    records = []
    for sample in range(samples + 1):
        result = read(field, axis, h)
        result['time'] = sample*steps*dt
        records.append(result)
        if sample < samples:
            for _ in range(steps):
                precess(field, dt/h**2, steepness, axis_weight, transport)
    return records


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--size', type=int, nargs='+', default=[97, 113])
    parser.add_argument('--duration', type=float, default=.045)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    if (any(n < 65 or n % 2 == 0 for n in args.size)
            or not math.isfinite(args.duration) or not 0 < args.duration <= .06):
        parser.error('Use odd sizes of at least 65 and 0 < duration <= 0.06.')
    report = json.dumps([run(n, args.duration) for n in args.size], indent=2, allow_nan=False) + '\n'
    if args.output:
        args.output.write_text(report, encoding='utf-8')
    else:
        print(report, end='')


if __name__ == '__main__':
    main()
