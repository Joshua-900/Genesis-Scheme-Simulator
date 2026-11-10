"""Compare conservative autonomous formation with and without strain feedback."""

import argparse
from functools import partial
import json
from pathlib import Path

import numpy as np

from .fixed_rule import run
from .strain_wave import INTERIOR, strain_terms


def advance(field, dt, gradient, axis, *, mode, spacing):
    static, _, rate = strain_terms(len(field), gradient, axis, spacing=spacing)
    state = np.zeros((*field.shape[:2], 5))
    state[..., :3] = field
    if mode == 'wave':
        state[..., 3] = static(field)
    stage = state.copy()
    center = state[INTERIOR]

    def step():
        k1 = rate(state, mode)
        stage[INTERIOR] = center+dt/2*k1
        k2 = rate(stage, mode)
        stage[INTERIOR] = center+dt/2*k2
        k3 = rate(stage, mode)
        stage[INTERIOR] = center+dt*k3
        k4 = rate(stage, mode)
        center[:] += dt/6*(k1+2*k2+2*k3+k4)
        field[INTERIOR] = center[..., :3]

    return step


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--size', type=int, choices=(113,129,161,193), required=True)
    parser.add_argument('--mode', choices=('off','instant','wave'), required=True)
    parser.add_argument('--duration', type=float, default=.025)
    parser.add_argument('--step-factor', type=float, default=.02)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if not 0 < args.duration <= .6 or not 0 < args.step_factor <= .02:
        parser.error('Use duration in (0, 0.6] and step factor in (0, 0.02].')
    integrator = None if args.mode == 'off' else partial(
        advance, mode=args.mode, spacing=1/(args.size-1))
    result = run(args.size, 405, 0., 225., args.duration, bias=-.12, factor=args.step_factor,
                 mature_charge=.9, padding=(args.size-1)//8, require_neutrality=True,
                 integrator=integrator, sample_interval=.0005)
    result['mode'] = args.mode
    args.output.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    print(args.size,args.mode,result['outcome'],result['records'][-1]['time'],flush=True)


if __name__ == '__main__':
    main()
