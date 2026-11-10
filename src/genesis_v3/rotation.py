"""Probe classical rotational response of a V3 knot."""

import argparse
import json
import math
from pathlib import Path

import numpy as np

from .model import effective_field, fixture, measure, step


def precess(field, factor, steepness, axis_weight, transport=None, *, axial_field=None,
            damping=0., rotation=1.):
    """RK4 Landau–Lifshitz evolution with a fixed north boundary."""
    interior = np.s_[1:-1, 1:-1]
    center = field[interior]
    stage = field.copy()

    def rate(state):
        local = state[interior]
        effective = effective_field(state, steepness, axis_weight)
        if axial_field is not None:
            effective[..., 2] += axial_field
        torque = np.cross(local, effective)
        change = rotation * torque if rotation != 1 else torque
        if damping:
            change = change + damping * np.cross(torque, local)
        if transport is not None:
            slope = state[2:, 1:-1] - state[:-2, 1:-1]
            radial = np.einsum('...i,...i->...', slope, local)[..., None]
            change -= transport * (slope - radial * local)
        return change

    k1 = rate(field)
    stage[interior] = center + .5 * factor * k1
    k2 = rate(stage)
    stage[interior] = center + .5 * factor * k2
    k3 = rate(stage)
    stage[interior] = center + factor * k3
    k4 = rate(stage)
    center += (factor / 6) * (k1 + 2*k2 + 2*k3 + k4)
    if damping:
        center /= np.linalg.norm(center, axis=-1, keepdims=True)


def kick(field, strength, envelope=1.):
    """Change axial moment with a localized polar-angle impulse."""
    z = np.clip(field[..., 2], -1., 1.)
    polar = np.arctan2(np.hypot(field[..., 0], field[..., 1]), z)
    phase = np.arctan2(field[..., 1], field[..., 0])
    polar += strength * envelope * np.sin(polar)
    return np.stack((np.sin(polar) * np.cos(phase), np.sin(polar) * np.sin(phase),
                     np.cos(polar)), axis=-1)


def relaxed_knot(size, easy_axis=30.):
    h = 1 / (size - 1)
    steepness, axis_weight = .0002 / h**2, easy_axis * h**2
    relaxed = fixture(size, 'charged', .25)
    relax_factor = .06
    for _ in range(math.ceil(.12 / (h*h * relax_factor))):
        step(relaxed, relax_factor, steepness, axis_weight)
    return relaxed, steepness, axis_weight


def run(size, duration, factor):
    h = 1 / (size - 1)
    relaxed, steepness, axis_weight = relaxed_knot(size)
    uncharged = relaxed.copy()
    uncharged[..., 0] = np.hypot(relaxed[..., 0], relaxed[..., 1])
    uncharged[..., 1] = 0
    axis = np.linspace(-.5, .5, size)
    disk = axis[:, None]**2 + axis[None, :]**2 < .15**2
    runs = {}
    samples = 20
    steps = math.ceil(duration / (samples * h*h * factor))
    dt = duration / (samples * steps)
    for name, initial, impulse in (('rest', relaxed, 0.), ('positive', relaxed, .25),
                                   ('negative', relaxed, -.25), ('zero_charge', uncharged, .25)):
        field = kick(initial, impulse) if impulse else initial.copy()
        ref = field[..., 0][disk] + 1j * field[..., 1][disk]
        records = []
        for sample in range(samples + 1):
            reading = measure(field, steepness, axis_weight)
            xy = field[..., 0][disk] + 1j * field[..., 1][disk]
            moment = (1 - field[..., 2]) * h*h
            overlap = np.vdot(ref, xy) / (np.linalg.norm(ref) * np.linalg.norm(xy))
            reading.update(time=sample*duration/samples, phase=float(np.angle(overlap)),
                           coherence=float(abs(overlap)), axial_deficit=float(moment.sum()),
                           axial_inside=float(moment[disk].sum()),
                           max_norm_error=float(np.max(np.abs(np.linalg.norm(field, axis=-1) - 1))))
            records.append(reading)
            if sample < samples:
                for _ in range(steps):
                    precess(field, dt / h**2, steepness, axis_weight)
        phases = np.unwrap([record['phase'] for record in records])
        for record, phase in zip(records, phases):
            record['phase'] = float(phase)
        runs[name] = records
    return dict(size=size, duration=duration, dt=dt, runs=runs)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--size', type=int, nargs='+', default=[97, 113])
    parser.add_argument('--duration', type=float, default=.025)
    parser.add_argument('--factor', type=float, default=.10)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    if (any(size < 33 or size % 2 == 0 for size in args.size)
            or not math.isfinite(args.duration) or args.duration <= 0
            or not 0 < args.factor <= .1):
        parser.error('Use odd sizes of at least 33, positive duration, and 0 < factor <= .1.')
    output = json.dumps([run(size, args.duration, args.factor) for size in args.size],
                        indent=2, allow_nan=False) + '\n'
    if args.output:
        args.output.write_text(output, encoding='utf-8')
    else:
        print(output, end='')


if __name__ == '__main__':
    main()
