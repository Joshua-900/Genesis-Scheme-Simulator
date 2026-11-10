"""Compare conservative release with continued relaxation at the staged handoffs."""

import json
import math
from pathlib import Path

import numpy as np

from .fixed_rule import energy_density
from .formation import localized
from .model import step
from .pair_swap import pad_north
from .rotation import precess
from .traveling_profile import score
from .wall_handoff import opposite_pair, prepare


def run(seed, size=113):
    h = 1/(size-1)
    source = Path('results/genesis_v3_wall_handoff')/f'seed{seed}_handoff_{size}.npz'
    if seed == 22:
        with np.load(source) as saved:
            initial, time = saved['field'], float(saved['time'])
            gradient, axis = float(saved['steepness']), float(saved['axis_weight'])
    else:
        initial, time, gradient, axis = prepare(size, seed, mature=True)
    field0 = pad_north(initial, (size-1)//8)
    x,y = np.meshgrid(np.arange(len(field0))*h, np.arange(len(field0))*h)
    xy = np.stack((x,y), axis=-1)
    interval = .0025
    steps = math.ceil(interval/(.08*h*h))
    dt = interval/steps
    result = {}

    def tube(points, radius):
        vector = points[1]-points[0]
        fraction = np.clip((xy-points[0])@vector/(vector@vector), 0, 1)
        return np.linalg.norm(xy-points[0]-fraction[..., None]*vector, axis=-1) <= radius

    for mode in ('release', 'continue_relaxing'):
        field = field0.copy()
        previous, parents = None, None
        records = []
        for sample in range(17):
            labels = np.empty(field.shape[:2], dtype=np.int32)
            reading = localized(field, labels_out=labels, previous_labels=previous, spacing=h)
            previous = labels
            pair = opposite_pair(reading, field=field, spacing=h)
            if pair is None or (parents is not None and any(
                    parent not in c['parents'] for parent,c in zip(parents,pair))):
                break
            parents = tuple(c['component'] for c in pair)
            points = np.array([[c['x'],c['y']] for c in pair])
            density = energy_density(field, gradient, axis)
            inner, outer = tube(points,.10), tube(points,.22)
            if sample==0:
                fixed_inner, fixed_outer = inner,outer
            profile = score(field,h,gradient,axis)
            records.append(dict(time=sample*interval, centers=points.tolist(),
                                spacing=float(np.linalg.norm(points[0]-points[1])),
                                charges=[c['charge'] for c in pair], total=float(density.sum()),
                                core=float(density[inner].sum()),
                                surrounding=float(density[outer & ~inner].sum()),
                                exterior=float(density[~outer].sum()),
                                fixed_surrounding=float(density[fixed_outer & ~fixed_inner].sum()),
                                residual=profile['residual']))
            if sample==16:
                break
            for _ in range(steps):
                if mode=='release':
                    precess(field,dt/h**2,gradient,axis)
                else:
                    step(field,dt/h**2,gradient,axis)
        result[mode] = records
        print(seed,mode,len(records),records[-1],flush=True)
    return dict(seed=seed,size=size,handoff_time=time,dt=dt,branches=result)


if __name__=='__main__':
    import sys
    seed=int(sys.argv[1])
    result=run(seed)
    path=Path('results/genesis_v3_fixed_rule')/f'handoff_mechanism_{seed}.json'
    path.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n',encoding='utf-8')
