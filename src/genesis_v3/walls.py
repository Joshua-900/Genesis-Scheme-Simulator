"""Test whether a twisted extended wall yields detached charged cores."""

import argparse
import json
from pathlib import Path

import numpy as np

from .formation import trial


def stripe(size, turns, half_length=.26, radius=.10, *, stagger=0.):
    axis = np.linspace(-.5, .5, size)
    x, y = np.meshgrid(axis, axis)
    distance = np.hypot(x, np.maximum(np.abs(y) - half_length, 0))
    local_radius = radius
    if stagger:
        local_radius = radius * (1 - .35 * np.exp(-(y / .09)**2))
    edge = np.clip((distance - .55 * local_radius) / (.9 * local_radius), 0, 1)
    polar = np.pi * (1 - edge**2 * (3 - 2 * edge))
    phase = turns * np.pi * np.clip(y / half_length, -1, 1)
    if stagger:
        side = .5 * (1 + np.tanh(x / .035))
        phase = turns * np.pi * ((1 - side) * np.tanh((y + stagger) / .12)
                                 + side * np.tanh((y - stagger) / .12))
    return np.stack((np.sin(polar) * np.cos(phase), np.sin(polar) * np.sin(phase),
                     np.cos(polar)), axis=-1)


def necked_wall(size, winding):
    """One connected wall with opposite turns spread around its lobes."""
    axis = np.linspace(-.5, .5, size)
    x, y = np.meshgrid(axis, axis)
    offset = .20
    upper = np.hypot(x, y - offset)
    lower = np.hypot(x, y + offset)
    bridge = np.hypot(x, np.maximum(np.abs(y) - offset, 0))
    lobe_edge = (np.minimum(upper, lower) - .095) / .14
    bridge_edge = (bridge - .012) / .032
    edge = np.clip(np.minimum(lobe_edge, bridge_edge), 0, 1)
    polar = np.pi * (1 - edge**2 * (3 - 2 * edge))
    phase = winding * (np.arctan2(y - offset, x) - np.arctan2(y + offset, x))
    return np.stack((np.sin(polar) * np.cos(phase), np.sin(polar) * np.sin(phase),
                     np.cos(polar)), axis=-1)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--size', type=int, nargs='+', default=[65, 97])
    parser.add_argument('--turns', type=float, nargs='+', default=[0, 1, 2])
    parser.add_argument('--output', type=Path)
    parser.add_argument('--stagger', type=float, default=0., help='Offset the twist on the two flanks')
    parser.add_argument('--necked', action='store_true', help='Use the connected two-lobe wall, with integer winding')
    args = parser.parse_args()
    if min(args.size) < 33 or not all(np.isfinite(args.turns)) or not np.isfinite(args.stagger):
        parser.error('Use sizes of at least 33 and finite turns.')
    if args.necked and any(not turns.is_integer() for turns in map(float, args.turns)):
        parser.error('The necked wall requires integer winding.')
    results = []
    for size in args.size:
        for turns in args.turns:
            field = necked_wall(size, turns) if args.necked else stripe(size, turns, stagger=args.stagger)
            result = trial(size, None, .10, .0002, 150, 20, initial_field=field)
            results.append(dict(turns=turns, stagger=args.stagger, necked=args.necked, **result))
    output = json.dumps(results, indent=2, allow_nan=False) + '\n'
    if args.output:
        args.output.write_text(output, encoding='utf-8')
    else:
        print(output, end='')


if __name__ == '__main__':
    main()
