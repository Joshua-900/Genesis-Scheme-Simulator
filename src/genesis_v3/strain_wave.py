"""Test reciprocal wave-mediated interactions between two prepared V3 knots."""

import argparse
import json
import math
from pathlib import Path

import numpy as np
from scipy.fft import dstn, idstn

from .model import charge_map, effective_field, measure
from .rotation import kick, relaxed_knot
from .transfer import localized_knot

INTERIOR = np.s_[1:-1, 1:-1]
SPEED, FREQUENCY, COUPLING = 35., 100., 600.


def strain_terms(size, gradient, axis, *, spacing=None):
    h = 1/(size-1) if spacing is None else spacing
    modes = 4*np.sin(np.pi*np.arange(1, size-1)/(2*(size-1)))**2
    stiffness = FREQUENCY**2+(SPEED/h)**2*(modes[:, None]+modes[None, :])

    def static(field):
        u = np.zeros((size, size))
        source = 1-field[INTERIOR][..., 2]**2
        u[INTERIOR] = idstn(COUPLING*dstn(source, type=1)/stiffness, type=1)
        return u

    def orientation_rate(field, u=None):
        local = field[INTERIOR]
        effective = effective_field(field, gradient, axis)
        if u is not None:
            effective[..., 2] -= 2*h*h*COUPLING*u[INTERIOR]*local[..., 2]
        return np.cross(local, effective)/h**2

    def rate(value, mode):
        field = value[..., :3]
        u = static(field) if mode == 'instant' else value[..., 3]
        derivative = np.zeros_like(value[INTERIOR])
        derivative[..., :3] = orientation_rate(field, None if mode == 'off' else u)
        if mode == 'wave':
            local = u[INTERIOR]
            laplacian = u[:-2, 1:-1]+u[2:, 1:-1]+u[1:-1, :-2]+u[1:-1, 2:]-4*local
            derivative[..., 3] = value[INTERIOR][..., 4]
            source = 1-field[INTERIOR][..., 2]**2
            derivative[..., 4] = (SPEED/h)**2*laplacian-FREQUENCY**2*local+COUPLING*source
        return derivative

    return static, orientation_rate, rate


def run(size, duration=.018, factor=.08):
    h = 1/(size-1)
    speed, frequency, coupling = SPEED, FREQUENCY, COUPLING
    coordinates = np.linspace(-.5, .5, size)
    x, y = np.meshgrid(coordinates, coordinates)
    knot, gradient, axis = relaxed_knot(size)
    knot = localized_knot(knot, np.hypot(x, y))
    shift = round(.17/h)
    offset = shift*h
    pair = np.roll(knot, -shift, axis=1)
    right = np.roll(knot, shift, axis=1)
    receiver = (x-offset)**2+y*y <= .10**2
    right_support = (x-offset)**2+y*y < .125**2
    pair[right_support] = right[right_support]
    taper = np.clip((.125-np.hypot(x+offset, y))/.035, 0, 1)
    disturbed = kick(pair, .25, taper**2*(3-2*taper))
    static, orientation_rate, rate = strain_terms(size, gradient, axis)
    charge_x, charge_y = np.meshgrid(coordinates[:-1]+h/2, coordinates[:-1]+h/2)
    charge_disk = (charge_x-offset)**2+charge_y**2 <= .10**2
    phase_reference = pair[..., 0][receiver]+1j*pair[..., 1][receiver]
    samples = 36
    steps = math.ceil(duration/(samples*h*h*factor))
    dt = duration/(samples*steps)

    def source(field):
        return 1-field[INTERIOR][..., 2]**2

    def read(field, u, momentum, mode):
        phase = field[..., 0][receiver]+1j*field[..., 1][receiver]
        q, ambiguous = charge_map(field)
        local_q = q[charge_disk]
        total = local_q.sum()
        center = [float(np.dot(c[charge_disk], local_q)/total) for c in (charge_x, charge_y)]
        orientation_energy = measure(field, gradient, axis)['energy']
        wave_energy = .5*h*h*np.sum(momentum**2+frequency**2*u**2)
        wave_energy += .5*speed**2*sum(np.sum(np.diff(u, axis=i)**2) for i in (0, 1))
        interaction_energy = 0. if mode == 'off' else -h*h*coupling*np.sum(u[INTERIOR]*source(field))
        return dict(center=center, charge=float(total), ambiguous=ambiguous,
                    phase=float(np.angle(np.vdot(phase_reference, phase))),
                    receiver_strain=u[receiver].copy(), energy=float(orientation_energy+wave_energy+interaction_energy))

    def evolve(mode, initial, *, block_kick=False):
        state = np.zeros((size, size, 5))
        state[..., :3] = initial
        if mode == 'wave':
            state[..., 3] = static(pair)
        center = state[INTERIOR]
        stage = state.copy()
        blocked = disturbed.copy() if block_kick else None
        blocked_stage = blocked.copy() if block_kick else None

        records, blocked_records = [], []
        for sample in range(samples+1):
            field = state[..., :3]
            u = static(field) if mode == 'instant' else state[..., 3]
            records.append(read(field, u, state[..., 4], mode))
            if block_kick:
                blocked_records.append(read(blocked, u, state[..., 4], mode))
            if sample < samples:
                for _ in range(steps):
                    k1 = rate(state, mode)
                    if block_kick:
                        b1 = orientation_rate(blocked, state[..., 3])
                    stage[INTERIOR] = center+dt/2*k1
                    k2 = rate(stage, mode)
                    if block_kick:
                        blocked_stage[INTERIOR] = blocked[INTERIOR]+dt/2*b1
                        b2 = orientation_rate(blocked_stage, stage[..., 3])
                    stage[INTERIOR] = center+dt/2*k2
                    k3 = rate(stage, mode)
                    if block_kick:
                        blocked_stage[INTERIOR] = blocked[INTERIOR]+dt/2*b2
                        b3 = orientation_rate(blocked_stage, stage[..., 3])
                    stage[INTERIOR] = center+dt*k3
                    k4 = rate(stage, mode)
                    if block_kick:
                        blocked_stage[INTERIOR] = blocked[INTERIOR]+dt*b3
                        b4 = orientation_rate(blocked_stage, stage[..., 3])
                        blocked[INTERIOR] += dt/6*(b1+2*b2+2*b3+b4)
                    center += dt/6*(k1+2*k2+2*k3+k4)
        return records, blocked_records

    results = {}
    def compare(mode, rest, kicked):
        results[mode] = []
        for sample, (a, b) in enumerate(zip(rest, kicked)):
            delta = np.subtract(b['center'], a['center'])
            phase_delta = np.angle(np.exp(1j*(b['phase']-a['phase'])))
            strain = b['receiver_strain']-a['receiver_strain']
            results[mode].append(dict(time=sample*duration/samples,
                                      displacement=delta.tolist(), phase=float(phase_delta),
                                      strain_rms=float(np.sqrt(np.mean(strain**2))),
                                      charge=[a['charge'], b['charge']], ambiguity=[a['ambiguous'], b['ambiguous']],
                                      energy_drift=None if mode == 'blocked' else
                                      [a['energy']/rest[0]['energy']-1, b['energy']/kicked[0]['energy']-1]))
    for mode in ('off', 'instant', 'wave'):
        rest, blocked = evolve(mode, pair, block_kick=mode == 'wave')
        kicked, _ = evolve(mode, disturbed)
        compare(mode, rest, kicked)
        if blocked:
            compare('blocked', rest, blocked)
    return dict(size=size, dt=dt, separation=2*offset, speed=speed, frequency=frequency,
                coupling=coupling, results=results)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--size', type=int, default=65)
    parser.add_argument('--step-factor', type=float, default=.08)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.size < 65 or args.size % 2 == 0 or not 0 < args.step_factor <= .08:
        parser.error('Use an odd grid size of at least 65 and a step factor in (0, 0.08].')
    result = run(args.size, factor=args.step_factor)
    args.output.write_text(json.dumps(result, indent=2, allow_nan=False)+'\n', encoding='utf-8')


if __name__ == '__main__':
    main()
