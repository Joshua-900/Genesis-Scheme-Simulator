"""Test wall formation and pair travel with constant damping and precession."""

import argparse
import json
import math
from pathlib import Path

import numpy as np

from .formation import disorder, localized
from .model import measure
from .rotation import precess
from .wall_handoff import opposite_pair


def energy_density(field, gradient, axis):
    density = .5*axis*np.sum(field[..., :2]**2, axis=-1)
    for left, right in ((np.s_[:-1, :], np.s_[1:, :]), (np.s_[:, :-1], np.s_[:, 1:])):
        squared = np.sum((field[right]-field[left])**2, axis=-1)
        half_bond = .25*squared + .125*gradient*squared**2
        density[left] += half_bond
        density[right] += half_bond
    return density


def run(size, seed, damping, easy_axis, duration, *, bias=0., factor=.08, mature_charge=.7,
        capture=None, padding=0, energy_regions=False, cardinal_penalty=.0002,
        require_neutrality=False, integrator=None, sample_interval=.005):
    h = 1 / (size-1)
    gradient, axis = cardinal_penalty/h**2, easy_axis*h**2
    field = disorder(size, seed, bias)
    if padding:
        expanded = np.zeros((size+2*padding, size+2*padding, 3))
        expanded[..., 2] = 1
        expanded[padding:-padding, padding:-padding] = field
        field = expanded
    width = (len(field)-1)*h
    if energy_regions:
        coordinates = np.arange(len(field))*h
        x, y = np.meshgrid(coordinates, coordinates)
        original = np.s_[padding:padding+size, padding:padding+size]
    samples = math.ceil(duration/sample_interval)
    interval = duration/samples
    steps = math.ceil(interval/(h*h*factor/(1+damping)))
    dt = interval/steps
    if integrator is None:
        def advance():
            precess(field, dt/h**2, gradient, axis, damping=damping)
    else:
        advance = integrator(field, dt, gradient, axis)
    records, lineage = [], {}
    previous = None
    tracked = None
    outcome = 'no_wall_born_pair'
    for sample in range(samples+1):
        labels = np.empty(field.shape[:2], dtype=np.int32)
        reading = localized(field, initial=sample == 0, labels_out=labels,
                            previous_labels=previous, spacing=h)
        previous = labels
        reading.update(time=sample*interval, energy=measure(field, gradient, axis, width)['energy'],
                       max_norm_error=float(np.max(np.abs(np.linalg.norm(field, axis=-1)-1))))
        if energy_regions:
            density = energy_density(field, gradient, axis)
            reading['padding_energy'] = float(density.sum()-density[original].sum())
        records.append(reading)
        if require_neutrality and (reading['ambiguous_triangles'] or abs(reading['charge']) > .01):
            outcome = 'neutrality_gate_failed'
            break
        next_lineage = {}
        for core in reading['cores']:
            component = core['component']
            ancestors = set().union(*(lineage.get(parent, set()) for parent in core['parents']))
            if sample and core['span'] >= .23 and core['min_z'] <= -.75:
                ancestors.add((sample, component))
            next_lineage[component] = ancestors
        lineage = next_lineage
        pair = opposite_pair(reading, field=field, spacing=h)
        if tracked is None and pair:
            a, b = pair
            shared = lineage[a['component']] & lineage[b['component']]
            if (shared and min(-a['charge'], b['charge']) >= mature_charge
                    and records[0]['max_disk_charge'] < .7 and abs(records[0]['charge']) < .01):
                positions = np.array([[core['x'], core['y']] for core in pair])
                tracked = (positions.mean(axis=0), np.linalg.norm(positions[0]-positions[1]),
                           2*h*max(a['radius_cells'], b['radius_cells']),
                           (a['component'], b['component']))
                reading['wall_ancestors'] = sorted(shared)
                outcome = 'time_limit'
                if capture is not None:
                    capture(field.copy(), reading['time'], dt)
        if tracked is not None:
            midpoint, spacing, diameter, parent_ids = tracked
            if energy_regions:
                # Hold the window fixed at the pair's formation site.
                region = (x-midpoint[0])**2 + (y-midpoint[1])**2 <= .22**2
                reading['formation_region_energy'] = float(density[region].sum())
            if pair is None or any(parent not in core['parents'] and 'wall_ancestors' not in reading
                                   for parent, core in zip(parent_ids, pair)):
                outcome = 'tracking_limit'
                break
            positions = np.array([[core['x'], core['y']] for core in pair])
            traveled = float(np.linalg.norm(positions.mean(axis=0)-midpoint)/diameter)
            separation_change = abs(float(np.linalg.norm(positions[0]-positions[1])/spacing)-1)
            reading.update(travel_diameters=traveled, separation_change=separation_change)
            tracked = midpoint, spacing, diameter, tuple(core['component'] for core in pair)
            if min(positions.min(), (width-positions).min()) < .09:
                outcome = 'boundary_limit'
                break
            if separation_change > .15:
                outcome = 'separation_gate_failed'
                break
            if traveled >= 3:
                outcome = 'travel_gate_passed'
                break
        if sample < samples:
            for _ in range(steps):
                advance()
    return dict(size=size, seed=seed, damping=damping, easy_axis=easy_axis, bias=bias,
                duration=duration, mature_charge=mature_charge, padding=padding, width=width,
                dt=dt, cardinal_penalty=cardinal_penalty, outcome=outcome, records=records)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--size', type=int, default=97)
    parser.add_argument('--seed', type=int, default=22)
    parser.add_argument('--damping', type=float, default=1.)
    parser.add_argument('--easy-axis', type=float, default=150.)
    parser.add_argument('--duration', type=float, default=.1)
    parser.add_argument('--bias', type=float, default=0.)
    parser.add_argument('--padding', type=int, default=0, help='North-aligned cells around the initial disorder')
    parser.add_argument('--step-factor', type=float, default=.08, help='Maximum dimensionless RK4 step before damping adjustment')
    parser.add_argument('--cardinal-penalty', type=float, default=.0002, help='Physical coefficient of the cardinal quartic bond energy')
    parser.add_argument('--require-neutrality', action='store_true', help='Stop at a sampled loss of neutrality')
    parser.add_argument('--energy-regions', action='store_true', help='Measure energy in the padding and at the formation site')
    parser.add_argument('--mature-charge', type=float, default=.7,
                        help='Minimum local charge magnitude before measuring travel')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    if (args.size < 65 or args.size % 2 == 0 or args.seed < 0 or not 0 < args.duration <= 1
            or not 0 <= args.damping <= 4 or not 0 <= args.easy_axis <= 300
            or not -.5 <= args.bias <= .5 or not .7 <= args.mature_charge <= 1 or args.padding < 0
            or not 0 < args.step_factor <= .08 or not math.isfinite(args.cardinal_penalty) or args.cardinal_penalty < 0):
        parser.error('Use an odd size ≥65, nonnegative seed and padding, duration in (0, 1], damping in [0, 4], '
                     'axis in [0, 300], bias in [−0.5, 0.5], mature charge in [0.7, 1], and step factor in (0, 0.08].')
    result = run(args.size, args.seed, args.damping, args.easy_axis, args.duration,
                 bias=args.bias, mature_charge=args.mature_charge, padding=args.padding,
                 factor=args.step_factor, energy_regions=args.energy_regions,
                 cardinal_penalty=args.cardinal_penalty, require_neutrality=args.require_neutrality)
    report = json.dumps(result, indent=2, allow_nan=False) + '\n'
    if args.output:
        args.output.write_text(report, encoding='utf-8')
    else:
        print(report, end='')


if __name__ == '__main__':
    main()
