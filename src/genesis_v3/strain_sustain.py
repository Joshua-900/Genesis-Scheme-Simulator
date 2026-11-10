"""Test whether reciprocal strain sustains an otherwise contracting V3 pair."""

import argparse
import json
import math
from pathlib import Path

import numpy as np

from .formation import localized
from .strain_wave import COUPLING, FREQUENCY, INTERIOR, SPEED, strain_terms
from .wall_handoff import opposite_pair


def run(checkpoint, factor=.04):
    with np.load(checkpoint) as saved:
        initial = saved['field']
        formation_time = float(saved['time'])
    size = len(initial)
    h = 1/(size-1)
    static, _, rate = strain_terms(size, .0002/h**2, 225*h**2)
    equilibrium = static(initial)
    interval = .0025
    steps = math.ceil(interval/(factor*h*h))
    dt = interval/steps
    branches = {}

    for mode in ('off', 'instant', 'wave'):
        state = np.zeros((*initial.shape[:2], 5))
        state[..., :3] = initial
        if mode == 'wave':
            state[..., 3] = equilibrium
        center = state[INTERIOR]
        stage = state.copy()
        field = state[..., :3]
        previous = None
        records = []
        outcome = 'time_limit'
        for sample in range(121):
            labels = np.empty(field.shape[:2], dtype=np.int32)
            reading = localized(field, labels_out=labels, previous_labels=previous, spacing=h)
            previous = labels
            reading['time'] = sample*interval
            records.append(reading)
            pair = opposite_pair(reading, field=field, spacing=h)
            if pair is None or (sample and any(
                    parent not in core['parents'] for parent, core in zip(parent_ids, pair))):
                outcome = 'tracking_limit'
                break
            parent_ids = tuple(core['component'] for core in pair)
            positions = np.array([[core['x'], core['y']] for core in pair])
            spacing = np.linalg.norm(positions[0]-positions[1])
            midpoint = positions.mean(axis=0)
            if not sample:
                initial_spacing, initial_midpoint = spacing, midpoint
                diameter = 2*h*max(core['radius_cells'] for core in pair)
            travel = float(np.linalg.norm(midpoint-initial_midpoint)/diameter)
            spacing_change = float(spacing/initial_spacing-1)
            reading.update(travel_diameters=travel, separation_change=spacing_change)
            if min(positions.min(), (1-positions).min()) < .09:
                outcome = 'boundary_limit'
                break
            if abs(spacing_change) > .15:
                outcome = 'separation_gate_failed'
                break
            if travel >= 3:
                outcome = 'travel_gate_passed'
                break
            if sample == 120:
                break
            for _ in range(steps):
                k1 = rate(state, mode)
                stage[INTERIOR] = center+dt/2*k1
                k2 = rate(stage, mode)
                stage[INTERIOR] = center+dt/2*k2
                k3 = rate(stage, mode)
                stage[INTERIOR] = center+dt*k3
                k4 = rate(stage, mode)
                center += dt/6*(k1+2*k2+2*k3+k4)
        branches[mode] = dict(outcome=outcome, records=records)
    return dict(size=size, formation_time=formation_time, dt=dt, interval=interval,
                speed=SPEED, frequency=FREQUENCY, coupling=COUPLING, branches=branches)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--checkpoint', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--step-factor', type=float, default=.04)
    args = parser.parse_args()
    if not 0 < args.step_factor <= .04:
        parser.error('Use a step factor in (0, 0.04].')
    report = run(args.checkpoint, args.step_factor)
    args.output.write_text(json.dumps(report, indent=2, allow_nan=False)+'\n', encoding='utf-8')


if __name__ == '__main__':
    main()
