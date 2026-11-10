"""Test free travel of the actual knots produced by wall breakup."""

import argparse
import itertools
import json
import math
from pathlib import Path

import numpy as np
from scipy.ndimage import map_coordinates

from .formation import disorder, localized
from .model import charge_map, effective_field, step
from .rotation import precess


def opposite_pair(reading, *, field=None, spacing=None):
    if reading['ambiguous_triangles'] or abs(reading['charge']) > .01:
        return None
    candidates = []
    for a, b in itertools.combinations(reading['cores'], 2):
        if a['charge'] > b['charge']:
            a, b = b, a
        distance = math.hypot(a['x'] - b['x'], a['y'] - b['y'])
        if a['charge'] <= -.7 and b['charge'] >= .7 and distance > .18:
            candidates.append((min(-a['charge'], b['charge']), a, b))
    if candidates:
        return max(candidates, key=lambda candidate: candidate[0])[1:]
    if field is not None and len(reading['cores']) == 2:
        first, second = reading['cores']
        if math.hypot(first['x']-second['x'], first['y']-second['y']) <= .18:
            density, _ = charge_map(field)
            axis = (np.arange(len(density))+.5)*spacing
            x, y = np.meshgrid(axis, axis)
            distances = [(x-core['x'])**2 + (y-core['y'])**2 for core in (first, second)]
            for i, core in enumerate((first, second)):
                mask = (distances[i] <= .09**2) & (distances[i] < distances[1-i])
                core['charge'] = float(density[mask].sum())
            reading['partitioned_disks'] = True
            a, b = sorted((first, second), key=lambda core: core['charge'])
            if a['charge'] <= -.7 and b['charge'] >= .7:
                return a, b
    return None


def prepare(size, seed, mature=False, *, minimum_sample=None):
    settings = {22: (0., 10, 150.), 405: (-.12, 3, 225.)}
    bias, switch, easy_axis = settings[seed]
    h = 1 / (size - 1)
    field = disorder(size, seed, bias)
    steepness, axis_weight = .0002 / h**2, easy_axis * h**2
    first_sample = {22: 17, 405: 7}[seed] if mature else switch
    if minimum_sample is not None:
        first_sample = max(first_sample, minimum_sample)
    for sample in range(25):
        if sample >= first_sample and opposite_pair(localized(field)) is not None:
            return field, sample*.005, steepness, axis_weight
        gradient = steepness if sample >= switch else 0.
        axis = axis_weight if sample >= switch else 0.
        steps = math.ceil(.005 / (.2*h*h / (1 + 12*gradient + axis)))
        for _ in range(steps):
            step(field, .005/(steps*h*h), gradient, axis)
    raise ValueError(f'No resolved pair formed for seed {seed} at size {size}.')


def resample_handoff(field, size):
    if len(field) == size:
        return field.copy()
    axis = np.linspace(0, len(field)-1, size)
    row, col = np.meshgrid(axis, axis, indexing='ij')
    result = np.stack([map_coordinates(field[..., i], (row, col), order=3, mode='nearest')
                       for i in range(3)], axis=-1)
    result /= np.linalg.norm(result, axis=-1, keepdims=True)
    result[[0, -1]] = (0, 0, 1)
    result[:, [0, -1]] = (0, 0, 1)
    return result


def run(size, seed, mature=False, *, duration=.075, padding=0, travel_gate=False,
        prepared=None, partition_overlap=False, damping=0.):
    source, handoff, steepness, axis_weight = prepare(size, seed, mature) if prepared is None else prepared
    field = resample_handoff(source, size)
    ratio = (size-1)/(len(source)-1)
    steepness *= ratio**2
    axis_weight /= ratio**2
    h = 1 / (size - 1)
    if padding:
        padded = np.zeros((size+2*padding, size+2*padding, 3))
        padded[..., 2] = 1
        padded[padding:-padding, padding:-padding] = field
        field = padded
    a, b = opposite_pair(localized(field, spacing=h))
    axis = (np.arange(len(field)-1) + .5)*h
    x, y = np.meshgrid(axis, axis)
    disks = [(x-core['x'])**2 + (y-core['y'])**2 <= .09**2 for core in (a, b)]

    def charge_centers(state):
        density, _ = charge_map(state)
        return np.array([[np.sum(coordinate[mask]*density[mask])/np.sum(density[mask])
                          for coordinate in (x, y)] for mask in disks])

    # Predict the initial tangent from the equation at the handoff alone.
    tangent = np.zeros_like(field)
    interior = field[1:-1, 1:-1]
    torque = np.cross(interior, effective_field(field, steepness, axis_weight))
    tangent[1:-1, 1:-1] = (torque + damping*np.cross(torque, interior))/h**2
    epsilon = 1e-7
    before, after = field-epsilon*tangent, field+epsilon*tangent
    before /= np.linalg.norm(before, axis=-1, keepdims=True)
    after /= np.linalg.norm(after, axis=-1, keepdims=True)
    predicted_velocity = (charge_centers(after)-charge_centers(before))/(2*epsilon)
    start = charge_centers(field)
    initial_extent = max(2*a['radius_cells']*h, 2*b['radius_cells']*h)
    initial_positions = np.array([[core['x'], core['y']] for core in (a, b)])
    midpoint = initial_positions.mean(axis=0)
    separation = float(np.linalg.norm(initial_positions[0]-initial_positions[1]))
    samples = math.ceil(duration/.0025)
    interval = duration/samples
    steps = math.ceil(interval/(.1*h*h))
    records = []
    outcome = 'time_limit'
    for sample in range(samples+1):
        reading = localized(field, spacing=h)
        pair = opposite_pair(reading, field=field if partition_overlap else None, spacing=h)
        time = sample*interval
        reading.update(time=time, predicted=(start+time*predicted_velocity).tolist())
        if time <= .01 and pair is not None:
            reading['fixed_disk_centers'] = charge_centers(field).tolist()
        records.append(reading)
        if pair is None:
            outcome = 'tracking_limit'
            break
        if travel_gate:
            positions = np.array([[core['x'], core['y']] for core in pair])
            distance = float(np.linalg.norm(positions.mean(axis=0)-midpoint))
            spacing_change = abs(float(np.linalg.norm(positions[0]-positions[1]))/separation-1)
            reading.update(travel_diameters=distance/initial_extent, separation_change=spacing_change)
            if min(positions.min(), (axis[-1]+h/2-positions).min()) < .09:
                outcome = 'boundary_limit'
                break
            if spacing_change > .15:
                outcome = 'separation_gate_failed'
                break
            if distance >= 3*initial_extent:
                outcome = 'travel_gate_passed'
                break
        if sample < samples:
            for _ in range(steps):
                precess(field, interval/(steps*h*h), steepness, axis_weight, damping=damping)
    return dict(size=size, source_size=len(source), seed=seed, handoff_time=handoff, dt=interval/steps,
                duration=duration, padding=padding, outcome=outcome,
                initial_extent=initial_extent, predicted_velocity=predicted_velocity.tolist(),
                records=records)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--size', type=int, nargs='+', default=[97, 113])
    parser.add_argument('--seed', type=int, nargs='+', choices=[22, 405], default=[22, 405])
    parser.add_argument('--output', type=Path)
    parser.add_argument('--mature', action='store_true', help='Wait for stronger localization before switching')
    parser.add_argument('--duration', type=float, default=.075)
    parser.add_argument('--padding', type=int, default=0, help='North-aligned cells added around the handoff field')
    parser.add_argument('--travel-gate', action='store_true', help='Stop on the travel or separation threshold')
    parser.add_argument('--damping', type=float, default=0., help='Constant relaxation after the handoff')
    parser.add_argument('--partition-overlap', action='store_true', help='Assign overlapping charge disks to the nearest core')
    parser.add_argument('--source-size', type=int, help='Form the pair on this grid before resampling')
    args = parser.parse_args()
    grids = args.size if args.source_size is None else [*args.size, args.source_size]
    if (any(n < 65 or n % 2 == 0 for n in grids) or args.padding < 0
            or not 0 < args.duration <= 1 or not 0 <= args.damping <= 4):
        parser.error('Use odd grid sizes of at least 65, nonnegative padding, duration in (0, 1], and damping in [0, 4].')
    prepared = ({seed: prepare(args.source_size, seed, args.mature) for seed in args.seed}
                if args.source_size is not None else {})
    report = json.dumps([run(n, seed, args.mature, duration=args.duration, padding=args.padding,
                             travel_gate=args.travel_gate, prepared=prepared.get(seed),
                             partition_overlap=args.partition_overlap, damping=args.damping)
                         for n in args.size for seed in args.seed],
                        indent=2, allow_nan=False) + '\n'
    if args.output:
        args.output.write_text(report, encoding='utf-8')
    else:
        print(report, end='')


if __name__ == '__main__':
    main()
