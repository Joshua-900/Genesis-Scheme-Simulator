"""Branch the same mature wall-born field with and without relaxation."""

import argparse
import json
import math
from pathlib import Path

import numpy as np

from .fixed_rule import run
from .formation import localized
from .model import measure
from .rotation import precess
from .wall_handoff import opposite_pair


def compare(size, output):
    handoff = []
    run(size, 405, .75, 225, .14, bias=-.12, mature_charge=.9,
        capture=lambda field, time, dt: handoff.append((field, time, dt)))
    if len(handoff) != 1:
        raise ValueError(f'Expected one mature pair on the {size} grid.')
    initial, time, original_dt = handoff[0]
    np.savez_compressed(output/f'damping_handoff_{size}.npz', field=initial, time=time)
    h = 1/(size-1)
    gradient, axis = .0002/h**2, 225*h**2
    duration, samples = .04, 16
    steps = math.ceil(duration/(samples*original_dt))
    dt = duration/(samples*steps)
    branches = {}
    for damping in (.75, 0.):
        field = initial.copy()
        records, previous = [], None
        prior_ids = None
        for sample in range(samples+1):
            labels = np.empty(field.shape[:2], dtype=np.int32)
            reading = localized(field, labels_out=labels, previous_labels=previous)
            previous = labels
            reading.update(time=sample*duration/samples, energy=measure(field, gradient, axis)['energy'])
            records.append(reading)
            pair = opposite_pair(reading, field=field, spacing=h)
            if pair is None or (prior_ids is not None and any(
                    parent not in core['parents'] for parent, core in zip(prior_ids, pair))):
                reading['tracking_limit'] = True
                break
            prior_ids = tuple(core['component'] for core in pair)
            positions = np.array([[c['x'], c['y']] for c in pair])
            reading['separation'] = float(np.linalg.norm(positions[0]-positions[1]))
            reading['midpoint'] = positions.mean(axis=0).tolist()
            if sample < samples:
                for _ in range(steps):
                    precess(field, dt/h**2, gradient, axis, damping=damping)
        branches[str(damping)] = records
    report = dict(size=size, handoff_time=time, duration=duration, dt=dt, branches=branches)
    (output/f'damping_comparison_{size}.json').write_text(
        json.dumps(report, indent=2, allow_nan=False)+'\n', encoding='utf-8')
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--size', type=int, choices=(113, 129), required=True)
    args = parser.parse_args()
    output = Path('results/genesis_v3_fixed_rule')
    output.mkdir(parents=True, exist_ok=True)
    compare(args.size, output)


if __name__ == '__main__':
    main()
