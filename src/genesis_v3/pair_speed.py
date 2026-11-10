"""Predict a held-out wall-born pair's speed from isolated-knot templates."""

import argparse
import json
import math
from pathlib import Path

import numpy as np
from scipy.ndimage import map_coordinates, spline_filter

from .formation import localized
from .model import measure
from .rotation import relaxed_knot
from .wall_handoff import opposite_pair, prepare, resample_handoff, run


def predict(size, prepared, *, subcell=False, template=None):
    field, _, steepness, axis_weight = prepared
    h = 1 / (size-1)
    a, b = opposite_pair(localized(field))
    x, y = np.meshgrid(np.linspace(0, 1, size), np.linspace(0, 1, size))
    direction = math.atan2(b['y']-a['y'], b['x']-a['x'])
    distance = math.hypot(b['x']-a['x'], b['y']-a['y'])
    phases = []
    for core, winding in ((a, 1), (b, -1)):
        dx, dy = x-core['x'], y-core['y']
        mask = dx*dx+dy*dy < .09**2
        xy = field[..., 0][mask] + 1j*field[..., 1][mask]
        phases.append(float(np.angle(np.sum(xy*np.exp(-1j*winding*np.arctan2(dy[mask], dx[mask]))))))
    relative = phases[1] - phases[0] - 2*direction
    if template is None:
        template, _, _ = relaxed_knot(size, axis_weight/h**2)
    def resolved_radius(state, center=None):
        # Integrate the negative region on a finer sampling lattice.
        axis = (np.arange(8*(size-1)) + .5)/8
        row, col = np.meshgrid(axis, axis, indexing='ij')
        negative = map_coordinates(state[..., 2], (row, col), order=3, mode='nearest') < 0
        if center is not None:
            cx, cy = center
            negative &= (col-cx/h)**2 + (row-cy/h)**2 < (.09/h)**2
        return float(np.sqrt(np.count_nonzero(negative)/np.pi)/8)

    radius = resolved_radius(template) if subcell else measure(template)['core_radius_cells']
    radii = [resolved_radius(field, (core['x'], core['y'])) if subcell else core['radius_cells']
             for core in (a, b)]
    coeff = [spline_filter(template[..., i], mode='nearest') for i in range(3)]
    rows, cols = np.indices((size, size), dtype=float) - (size-1)/2

    def shape(center, core_radius, winding, phase):
        scale = core_radius/radius
        midpoint = (size-1)/2
        coords = (rows/scale+midpoint, (cols-center/h)/scale+midpoint)
        n = np.stack([map_coordinates(c, coords, mode='nearest', prefilter=False)
                      for c in coeff], axis=-1)
        n /= np.linalg.norm(n, axis=-1, keepdims=True)
        z = n[..., 2]
        xy = (n[..., 0] + 1j*winding*n[..., 1])*np.exp(1j*phase)
        return np.where(z > -1+1e-12, xy/np.maximum(1+z, 1e-12), 1e6)

    def energy(w):
        norm = 1 + np.abs(w)**2
        n = np.stack((2*w.real/norm, 2*w.imag/norm, 2/norm-1), axis=-1)
        n[[0, -1]] = (0, 0, 1)
        n[:, [0, -1]] = (0, 0, 1)
        return measure(n, steepness, axis_weight)['energy']

    def interaction(d):
        left = shape(-d/2, radii[0], 1, 0)
        right = shape(d/2, radii[1], -1, relative)
        return energy(left+right)-energy(left)-energy(right)

    slope = (interaction(distance+h/4)-interaction(distance-h/4))/(h/2)
    transverse_speed = -slope/(4*np.pi)
    return dict(distance=distance, phase=relative, energy_slope=slope,
                core_radii=[r*h for r in radii], template_radius=radius*h,
                velocity=[-math.sin(direction)*transverse_speed, math.cos(direction)*transverse_speed])


def compare_grids(output):
    sizes = (97, 113)
    sources = {size: prepare(size, 405, minimum_sample=6) for size in sizes}
    axis_strength = sources[97][3] * (97-1)**2
    templates = {size: relaxed_knot(size, axis_strength)[0] for size in sizes}
    forecasts = []
    for source_size, source in sources.items():
        np.savez_compressed(output/f'seed405_handoff_{source_size}.npz',
                            field=source[0], time=source[1], steepness=source[2], axis_weight=source[3])
        field, time, steepness, axis_weight = source
        for size in sizes:
            ratio = (size-1)/(source_size-1)
            prepared = (resample_handoff(field, size), time, steepness*ratio**2, axis_weight/ratio**2)
            forecasts.append(dict(source_size=source_size, size=size,
                                  cell=predict(size, prepared, template=templates[size]),
                                  subcell=predict(size, prepared, subcell=True, template=templates[size])))
    (output/'heldout_cross_predictions.json').write_text(json.dumps(forecasts, indent=2)+'\n',
                                                       encoding='utf-8')
    for source_size, source in sources.items():
        size = next(n for n in sizes if n != source_size)
        result = run(size, 405, duration=.025, padding=(size-1)//8, prepared=source)
        (output/f'heldout_cross_{source_size}_{size}.json').write_text(
            json.dumps(result, indent=2)+'\n', encoding='utf-8')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--compare-grids', action='store_true')
    mode.add_argument('--validate-subcell', action='store_true',
                      help='Test the frozen subcell predictor at a new seed-22 handoff')
    mode.add_argument('--travel-validation', action='store_true',
                      help='Test the frozen predictor over a seed-405 travel window')
    args = parser.parse_args()
    output = Path('results/genesis_v3_wall_handoff')
    output.mkdir(parents=True, exist_ok=True)
    if args.compare_grids:
        compare_grids(output)
        return
    if args.travel_validation:
        for size in (97, 113):
            validate_travel(size, output)
        return
    seed, sample, prefix = (22, 18, 'subcell_validation') if args.validate_subcell else (405, 6, 'heldout')
    for size in (97, 113):
        prepared = prepare(size, seed, minimum_sample=sample)
        forecast = predict(size, prepared, subcell=args.validate_subcell)
        (output/f'{prefix}_prediction_{size}.json').write_text(json.dumps(forecast, indent=2)+'\n',
                                                              encoding='utf-8')
        result = run(size, seed, duration=.025, padding=(size-1)//8, prepared=prepared)
        (output/f'{prefix}_result_{size}.json').write_text(json.dumps(result, indent=2)+'\n',
                                                          encoding='utf-8')


def validate_travel(size, output):
    prepared = prepare(size, 405, mature=True)
    forecast = predict(size, prepared, subcell=True)
    (output/f'travel_validation_prediction_{size}.json').write_text(
        json.dumps(forecast, indent=2)+'\n', encoding='utf-8')
    result = run(size, 405, duration=.3, padding=(size-1)//8, travel_gate=True,
                 prepared=prepared, partition_overlap=True)
    (output/f'travel_validation_result_{size}.json').write_text(
        json.dumps(result, indent=2)+'\n', encoding='utf-8')
    return result


if __name__ == '__main__':
    main()
