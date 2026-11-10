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

from src.genesis_v3.traveling_profile import score
from src.genesis_v3.pair_swap import pad_north
from src.genesis_v3.formation import localized
from src.genesis_v3.wall_handoff import opposite_pair, prepare
import math
root=Path('results/genesis_v3_fixed_rule')
size=113
h=1/(size-1)
gradient,axis=.0002/h**2,225*h**2
threshold=(.2465663373647364+.9809760218822883)/2
settings={'mature_staged_5': 5}
fields={}
forecasts={}
for name,degrees in settings.items():
    field,formation_time,_,_=prepare(size,405,mature=True)
    assert formation_time==.035
    pair=opposite_pair(localized(field))
    a,b=np.array([[c['x'],c['y']] for c in pair])
    x,y=np.meshgrid(np.linspace(0,1,size),np.linspace(0,1,size))
    xy=np.stack((x,y),axis=-1)
    line=b-a
    fraction=np.clip((xy-a)@line/(line@line),0,1)
    radius=np.linalg.norm(xy-a-fraction[...,None]*line,axis=-1)
    taper=np.clip((.155-radius)/.055,0,1)
    angle=np.deg2rad(degrees)*taper*taper*(3-2*taper)
    transverse=(field[...,0]+1j*field[...,1])*np.exp(1j*angle)
    field[...,0],field[...,1]=transverse.real,transverse.imag
    field=pad_north(field,14)
    fields[name]=field
    prediction=score(field,h,gradient,axis)
    prediction['expected']='travel' if prediction['residual']<threshold else 'spacing_failure'
    forecasts[name]=prediction
(root/'traveling_profile_low_score_forecast.json').write_text(json.dumps(dict(threshold=threshold,cases=forecasts),indent=2)+'\n')
print('frozen forecasts',forecasts,flush=True)

def evolve(name):
    field=fields[name]
    interval=.0025
    steps=math.ceil(interval/(.08*h*h))
    dt=interval/steps
    records=[]
    previous,ids=None,None
    outcome='time_limit'
    for i in range(241):
        labels=np.empty(field.shape[:2],dtype=np.int32)
        reading=localized(field,labels_out=labels,previous_labels=previous,spacing=h)
        previous=labels
        reading['time']=i*interval
        records.append(reading)
        pair=opposite_pair(reading,field=field,spacing=h)
        if pair is None or (ids is not None and any(p not in c['parents'] for p,c in zip(ids,pair))):
            outcome='tracking_limit'
            break
        ids=tuple(c['component'] for c in pair)
        xy=np.array([[c['x'],c['y']] for c in pair])
        spacing=np.linalg.norm(xy[1]-xy[0])
        midpoint=xy.mean(axis=0)
        if i==0:
            initial_spacing=spacing
            origin=midpoint
            diameter=2*h*max(c['radius_cells'] for c in pair)
        travel=float(np.linalg.norm(midpoint-origin)/diameter)
        change=float(spacing/initial_spacing-1)
        reading.update(travel_diameters=travel,separation_change=change)
        if min(xy.min(),(1.25-xy).min())<.09:
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
                precess(field,dt/h**2,gradient,axis,damping=0.)
    last=records[-1]
    print(name,outcome,last['time'],last.get('travel_diameters'),last.get('separation_change'),flush=True)
    return dict(outcome=outcome,dt=dt,records=records)
with ThreadPoolExecutor(2) as pool:
    results=dict(zip(fields,pool.map(evolve,fields)))
(root/'traveling_profile_low_score_result.json').write_text(json.dumps(results,indent=2)+'\n')

