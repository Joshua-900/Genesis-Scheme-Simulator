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
damping=.75
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
    (root/f'roughness_sustain_{seed}.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    z=records[-1]
    print(seed,outcome,z['time'],z.get('travel_diameters'),z.get('separation_change'),flush=True)
    return outcome
from src.genesis_v3.model import effective_field, measure
rough=ctypes.CDLL(str(Path('work/fixed_rule_accel/roughness_step.dll').resolve())).tick
rough.argtypes=tick.argtypes
rough.restype=None
base_step=precess
local_cache=threading.local()
def precess(field,dt,gradient,axis,*,damping):
    if not damping:
        return base_step(field,dt,gradient,axis,damping=0.)
    if getattr(local_cache,'shape',None)!=field.shape:
        local_cache.shape=field.shape
        local_cache.buffer=np.zeros(5*field.size)
    rough(field.ctypes.data,local_cache.buffer.ctypes.data,len(field),dt,gradient,axis,damping)

def roughness(field):
    center=field[1:-1,1:-1]
    delta=np.stack([field[:-2,1:-1]-center,field[2:,1:-1]-center,
                    field[1:-1,:-2]-center,field[1:-1,2:]-center])
    ratio=np.sqrt(np.sum(delta.sum(axis=0)**2,axis=-1)/(4*np.sum(delta**2,axis=(0,3))+1e-30))
    t=np.clip((ratio-.25)/.40,0,1)
    return .75*t*t*(3-2*t)

def reference(state,gradient,axis,factor):
    n=state[1:-1,1:-1]
    stage=state.copy()
    def rate(value):
        v=value[1:-1,1:-1]
        torque=np.cross(v,effective_field(value,gradient,axis))
        return torque+roughness(value)[...,None]*np.cross(torque,v)
    k1=rate(state)
    stage[1:-1,1:-1]=n+.5*factor*k1
    k2=rate(stage)
    stage[1:-1,1:-1]=n+.5*factor*k2
    k3=rate(stage)
    stage[1:-1,1:-1]=n+factor*k3
    k4=rate(stage)
    n+=factor/6*(k1+2*k2+2*k3+k4)
    n/=np.linalg.norm(n,axis=-1,keepdims=True)

check=sim.disorder(65,405,-.12)
test=check.copy()
for _ in range(100):
    reference(check,.0002*64**2,225/64**2,.02)
    precess(test,.02,.0002*64**2,225/64**2,damping=.75)
err=float(np.max(abs(check-test)))
assert err<1e-10
print('roughness compiled check',err,flush=True)

def disorder_test():
    size=113
    h=1/(size-1)
    gradient,axis=.0002/h**2,225*h**2
    initial=pad_north(sim.disorder(size,405,-.12),14)
    interval=.00025
    steps=math.ceil(interval/(.02*h*h))
    dt=interval/steps
    reports={}
    for mode,amplitude in [('off',0.),('roughness',.75)]:
        field=initial.copy()
        records=[]
        for i in range(41):
            labels=np.empty(field.shape[:2],dtype=np.int32)
            info=localized(field,labels_out=labels,spacing=h)
            weights=roughness(field)
            info.update(time=i*interval,energy=measure(field,gradient,axis)['energy'],
                        active_fraction=float(np.mean(weights>0)),mean_proposed_damping=float(weights.mean()))
            records.append(info)
            if i<40:
                for _ in range(steps):
                    precess(field,dt/h**2,gradient,axis,damping=amplitude)
        reports[mode]=records
    (root/'roughness_disorder_405.json').write_text(json.dumps(reports,indent=2)+'\n')
    for mode,r in reports.items():
        print('disorder',mode,r[0]['active_fraction'],r[-1]['charge'],
              r[-1]['energy']/r[0]['energy']-1,flush=True)

from scipy.ndimage import convolve
from src.genesis_v3.model import charge_map
for n in (113,129):
    h=1/(n-1)
    run=json.loads((root/f'roughness_formation_{n}.json').read_text())
    a=run['records']
    prev=a[-2]
    init=np.load(root/f'roughness_formation_checkpoint_{n}.npz')
    field=init['field']
    dt=float(init['dt'])
    for _ in range(round((a[-1]['time']-float(init['time']))/dt)):
        precess(field,dt/h**2,.0002/h**2,225*h**2,damping=.75)
    observed=localized(field,spacing=h)
    np.testing.assert_allclose(observed['charge'],a[-1]['charge'],rtol=0,atol=1e-11)
    eligible=[c for c in prev['cores'] if abs(c['charge'])>=.7]
    from itertools import combinations
    for c,d in combinations(eligible,2):
        if c['charge']*d['charge']>=0:
            continue
        form=next(r for r in a if 'wall_ancestors' in r)
        pair=opposite_pair(form)
        if pair is None:
            continue
        start=np.array([[z['x'],z['y']] for z in pair]).mean(axis=0)
        diameter=2*h*max(z['radius_cells'] for z in pair)
        mid=np.array([(c['x']+d['x'])/2,(c['y']+d['y'])/2])
        if abs(np.linalg.norm(mid-start)/diameter-prev['travel_diameters'])<1e-9:
            previous=sorted([c,d],key=lambda v:v['charge'])
            break
    else:
        raise ValueError('Missing previously tracked pair')
    q,ambiguous=charge_map(field)
    coords=(np.arange(len(q))+.5)*h
    x,y=np.meshgrid(coords,coords)
    off=np.arange(-int(np.ceil(.09/h)),int(np.ceil(.09/h))+1)*h
    disk=(off[:,None]**2+off[None,:]**2<=.09**2).astype(float)
    sm=convolve(q,disk,mode='constant')
    out=[]
    for c in previous:
        dist=(x-c['x'])**2+(y-c['y'])**2
        sign=np.sign(c['charge'])
        index=np.unravel_index(np.argmax(np.where(dist<=.035**2,sign*sm,-np.inf)),q.shape)
        out.append(dict(old_charge=c['charge'],fixed=float(q[dist<=.09**2].sum()),
                        best=float(sm[index]),center=[float(x[index]),float(y[index])]))
    print(n,out,flush=True)
    (root/f'roughness_formation_endpoint_{n}.json').write_text(json.dumps(
        dict(size=n,time=a[-1]['time'],search_radius=.035,disk_radius=.09,cores=out),indent=2)+'\n')
