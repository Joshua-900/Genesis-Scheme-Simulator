import ctypes
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import numpy as np
from src.genesis_v3 import fixed_rule as sim

tick = ctypes.CDLL(str(Path('work/fixed_rule_accel/step.dll').resolve())).tick
tick.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_int] + [ctypes.c_double]*4
tick.restype = None

def worker(size, factor, duration):
    def step(field, dt, gradient, axis, *, damping):
        if field.shape != step.shape:
            step.shape = field.shape
            step.buffer = np.zeros(5*field.size)
        tick(field.ctypes.data, step.buffer.ctypes.data, len(field), dt, gradient, axis, damping)
    step.shape = None
    return step

native = sim.precess
accel = worker(65, .04, .14)
a = sim.disorder(65,405,-.12)
b = a.copy()
for _ in range(1000):
    native(a,.02,.0002*64**2,225/64**2)
    accel(b,.02,.0002*64**2,225/64**2,damping=0.)
error = float(np.max(np.abs(a-b)))
print('1000 steps max error',error, flush=True)
assert error < 1e-9
import threading
cache = threading.local()
def precess(*args, **kwargs):
    if not hasattr(cache,'step'):
        cache.step = worker(None,None,None)
    cache.step(*args, **kwargs)
sim.precess = precess

import math
from src.genesis_v3.formation import localized
from src.genesis_v3.pair_swap import pad_north
from src.genesis_v3.wall_handoff import opposite_pair, prepare

root=Path('results/genesis_v3_fixed_rule')
damping=.25
size=113
h=1/(size-1)
interval=.0025
steps=math.ceil(interval/(.08*h*h/(1+damping)))
dt=interval/steps

def run(seed):
    if seed==22:
        with np.load(Path('results/genesis_v3_wall_handoff')/f'seed22_handoff_{size}.npz') as saved:
            source=saved['field']
            gradient=float(saved['steepness'])
            axis=float(saved['axis_weight'])
    else:
        source,_,gradient,axis=prepare(size,seed,mature=True)
    field=pad_north(source,14)
    records=[]
    previous,parents=None,None
    outcome='time_limit'
    for i in range(241):
        labels=np.empty(field.shape[:2],dtype=np.int32)
        reading=localized(field,labels_out=labels,previous_labels=previous,spacing=h)
        previous=labels
        reading['time']=i*interval
        records.append(reading)
        pair=opposite_pair(reading,field=field,spacing=h)
        if pair is None or (parents is not None and any(p not in c['parents'] for p,c in zip(parents,pair))):
            outcome='tracking_limit'
            break
        parents=tuple(c['component'] for c in pair)
        points=np.array([[c['x'],c['y']] for c in pair])
        midpoint=points.mean(axis=0)
        spacing=np.linalg.norm(points[1]-points[0])
        if i==0:
            first_spacing,origin=spacing,midpoint
            diameter=2*h*max(c['radius_cells'] for c in pair)
        change=float(spacing/first_spacing-1)
        travel=float(np.linalg.norm(midpoint-origin)/diameter)
        edge=float(min(points.min(),(1.25-points).min()))
        reading.update(separation_change=change,travel_diameters=travel,edge=edge)
        if edge<.09:
            outcome='boundary_limit'
            break
        if abs(change)>.15:
            outcome='spacing_failure'
            break
        if travel>=3:
            outcome='travel'
            break
        if i<240:
            for _ in range(steps):
                precess(field,dt/h**2,gradient,axis,damping=damping)
    result=dict(seed=seed,size=size,dt=dt,damping=damping,outcome=outcome,records=records)
    (root/f'weak_damping_sustain_{seed}.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    z=records[-1]
    print(seed,outcome,z['time'],z.get('travel_diameters'),z.get('separation_change'),flush=True)
    return outcome
with ThreadPoolExecutor(2) as pool:
    outcomes=list(pool.map(run,(22,405)))
if all(value=='travel' for value in outcomes):
    for seed,bias,axis in ((22,0.,150.),(405,-.12,225.)):
        result=sim.run(size,seed,damping,axis,.14,bias=bias,mature_charge=.9,padding=14,
                       require_neutrality=True)
        (root/f'weak_damping_formation_{seed}.json').write_text(json.dumps(result,indent=2)+'\n')
        print(seed,'formation',result['outcome'],result['records'][-1]['time'],flush=True)
