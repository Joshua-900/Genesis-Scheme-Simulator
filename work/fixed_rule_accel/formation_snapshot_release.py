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

from src.genesis_v3.model import step
from src.genesis_v3.wall_handoff import opposite_pair
import math

def release(field,h,gradient,axis):
    initial=opposite_pair(localized(field,spacing=h),field=field,spacing=h)
    if initial is None:
        return dict(outcome='no_resolved_pair')
    origin=np.array([[c['x'],c['y']] for c in initial])
    d0=np.linalg.norm(origin[1]-origin[0])
    line=(origin[1]-origin[0])/d0
    side=np.array([line[1],-line[0]])
    interval=.0025
    steps=math.ceil(interval/(.08*h*h))
    dt=interval/steps
    ids,previous=None,None
    records=[]
    for i in range(6):
        labels=np.empty(field.shape[:2],dtype=np.int32)
        reading=localized(field,labels_out=labels,previous_labels=previous,spacing=h)
        previous=labels
        pair=opposite_pair(reading,field=field,spacing=h)
        if pair is None or (ids is not None and any(p not in c['parents'] for p,c in zip(ids,pair))):
            return dict(outcome='tracking_limit',records=records)
        ids=tuple(c['component'] for c in pair)
        points=np.array([[c['x'],c['y']] for c in pair])
        change=float(np.linalg.norm(points[1]-points[0])/d0-1)
        transverse=(points-origin)@side/(i*interval) if i else np.zeros(2)
        records.append(dict(time=i*interval,spacing_change=change,transverse=transverse.tolist(),
                            charges=[c['charge'] for c in pair],centers=points.tolist()))
        if i<5:
            for _ in range(steps):
                precess(field,dt/h**2,gradient,axis,damping=0.)
    return dict(outcome='tracked',records=records)

def staged(seed):
    n=113
    h=1/(n-1)
    bias,switch,easy,center={22:(0.,10,150.,17),405:(-.12,3,225.,7)}[seed]
    field=sim.disorder(n,seed,bias)
    gradient,axis=.0002/h**2,easy*h**2
    results={}
    for i in range(center+3):
        if i>=center-2:
            padded=pad_north(field,14)
            result=release(padded,h,gradient,axis)
            results[f'{i*.005:.6f}']=result
            print('staged',seed,i*.005,result['outcome'],flush=True)
        if i==center+2:
            break
        g,k=(gradient,axis) if i>=switch else (0.,0.)
        steps=math.ceil(.005/(.2*h*h/(1+12*g+k)))
        for _ in range(steps):
            step(field,.005/(steps*h*h),g,k)
    return results

def rough_starts(n):
    h=1/(n-1)
    r=json.loads((root/f'roughness_formation_{n}.json').read_text())
    center=next(i for i,z in enumerate(r['records']) if 'wall_ancestors' in z)
    interval=r['records'][1]['time']
    dt=r['dt']
    steps=round(interval/dt)
    gradient,axis=.0002/h**2,225*h*h
    field=pad_north(sim.disorder(n,405,-.12),(n-1)//8)
    results={}
    for i in range(center+3):
        if i>=center-2:
            if i==center:
                with np.load(root/f'roughness_formation_checkpoint_{n}.npz') as checkpoint:
                    np.testing.assert_allclose(field,checkpoint['field'],rtol=0,atol=1e-12)
            result=release(field.copy(),h,gradient,axis)
            results[f'{i*interval:.6f}']=result
            print('rough',n,i*interval,result['outcome'],flush=True)
        if i<center+2:
            for _ in range(steps):
                precess(field,dt/h**2,gradient,axis,damping=.75)
    return results

with ThreadPoolExecutor(4) as pool:
    jobs={'staged_22':pool.submit(staged,22),'staged_405':pool.submit(staged,405),
          'rough_113':pool.submit(rough_starts,113),'rough_129':pool.submit(rough_starts,129)}
    report={name:job.result() for name,job in jobs.items()}
(root/'formation_snapshot_release.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
