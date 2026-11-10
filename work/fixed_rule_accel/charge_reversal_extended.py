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


from src.genesis_v3 import pair_swap
from src.genesis_v3.formation import localized
from src.genesis_v3.model import measure
from src.genesis_v3.wall_handoff import opposite_pair

pair_swap.precess=lambda field,dt,gradient,axis: precess(field,dt,gradient,axis,damping=0.)
root=Path('results/genesis_v3_fixed_rule')

def run(size):
    h=1/(size-1)
    gradient,axis=.0002/h**2,225*h**2
    with np.load(root/f'damping_handoff_{size}.npz') as saved:
        initial=saved['field']
    pair=opposite_pair(localized(initial))
    positions=np.array([[c['x'],c['y']] for c in pair])
    x,y=np.meshgrid(np.linspace(0,1,size),np.linspace(0,1,size))
    points=np.stack((x,y),axis=-1)
    segment=positions[1]-positions[0]
    fraction=np.clip((points-positions[0])@segment/(segment@segment),0,1)
    radius=np.linalg.norm(points-positions[0]-fraction[...,None]*segment,axis=-1)
    taper=np.clip((radius-.10)/.055,0,1)
    blend=taper**2*(3-2*taper)
    # Use a fixed reflection plane and choose its azimuth by initial energy only.
    candidates=[]
    for azimuth in np.arange(24)*np.pi/24:
        normal=np.array([-np.sin(azimuth),np.cos(azimuth),0.])
        reflected=initial-2*(initial@normal)[...,None]*normal
        mixed=(1-blend[...,None])*reflected+blend[...,None]*initial
        norm=np.linalg.norm(mixed,axis=-1)
        if norm.min()<.1:
            continue
        mixed/=norm[...,None]
        mixed[blend==1]=initial[blend==1]
        reading=localized(mixed)
        swapped=opposite_pair(reading,field=mixed,spacing=h)
        if swapped is None:
            continue
        reversed_positions=np.array([[c['x'],c['y']] for c in swapped])[::-1]
        if np.max(np.linalg.norm(reversed_positions-positions,axis=1))>h:
            continue
        energy=measure(mixed,gradient,axis)['energy']
        candidates.append((energy,float(azimuth),float(norm.min()),mixed))
    assert candidates, f'No admissible local reversal for {size}'
    energy,azimuth,min_norm,reversed_field=min(candidates,key=lambda c:c[0])
    print(size,'reversal',len(candidates),azimuth,'energy ratio',energy/measure(initial,gradient,axis)['energy'],flush=True)
    archived=json.loads((root/f'charge_reversal_{size}.json').read_text())
    assert azimuth==archived['reflection_angle']
    interval=.0025
    dt=archived['dt']
    steps=round(interval/dt)
    field=reversed_field
    records=[]
    previous, ids=None,None
    outcome='time_limit'
    for sample in range(121):
        labels=np.empty(field.shape[:2],dtype=np.int32)
        reading=localized(field,labels_out=labels,previous_labels=previous,spacing=h)
        previous=labels
        reading['time']=sample*interval
        records.append(reading)
        pair=opposite_pair(reading,field=field,spacing=h)
        if pair is None or (ids is not None and any(parent not in c['parents'] for parent,c in zip(ids,pair))):
            outcome='tracking_limit'
            break
        ids=tuple(c['component'] for c in pair)
        points=np.array([[c['x'],c['y']] for c in pair])
        midpoint=points.mean(axis=0)
        spacing=np.linalg.norm(points[1]-points[0])
        if not sample:
            origin=midpoint
            initial_spacing=spacing
            diameter=2*h*max(c['radius_cells'] for c in pair)
        travel=float(np.linalg.norm(midpoint-origin)/diameter)
        spacing_change=float(spacing/initial_spacing-1)
        edge=float(min(points.min(),(1-points).min()))
        reading.update(separation=float(spacing),travel_diameters=travel,
                       separation_change=spacing_change,edge_distance=edge)
        if sample<=16:
            assert abs(spacing-archived['runs']['reversed_native'][sample]['separation'])<1e-10
        if edge<.09:
            outcome='boundary_limit'
            break
        if abs(spacing_change)>.15:
            outcome='separation_gate_failed'
            break
        if travel>=3:
            outcome='travel_gate_passed'
            break
        if sample<120:
            for _ in range(steps):
                precess(field,dt/h**2,gradient,axis,damping=0.)
    result=dict(size=size,dt=dt,interval=interval,reflection_angle=azimuth,diameter=diameter,
                outcome=outcome,records=records)
    (root/f'charge_reversal_extended_{size}.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    last=records[-1]
    print(size,outcome,last['time'],last.get('travel_diameters'),last.get('separation_change'),
          last.get('edge_distance'),flush=True)

with ThreadPoolExecutor(2) as pool:
    list(pool.map(run,(113,129)))

