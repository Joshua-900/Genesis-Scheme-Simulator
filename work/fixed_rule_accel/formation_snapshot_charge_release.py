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
from src.genesis_v3.wall_handoff import opposite_pair

def track(field,h,dt,axis,damping,centers,diameter,start_time,cap):
    coords=(np.arange(len(field)-1)+.5)*h
    x,y=np.meshgrid(coords,coords)
    initial=centers.copy()
    spacing=np.linalg.norm(initial[1]-initial[0])
    diameter=float(diameter)
    width=(len(field)-1)*h
    interval_steps=round(.001/dt)
    records=[]
    outcome='time_limit'
    kernels=[]
    for radius in (.055,.075,.09):
        off=np.arange(-int(np.ceil(radius/h)),int(np.ceil(radius/h))+1)*h
        kernels.append((off[:,None]**2+off[None,:]**2<=radius**2).astype(float))
    for i in range(int(cap/(interval_steps*dt))+1):
        if i:
            for _ in range(interval_steps):
                precess(field,dt/h**2,.0002/h**2,axis,damping=damping)
        q,ambiguous=charge_map(field)
        net=float(q.sum())
        if ambiguous or abs(net)>.01:
            outcome='charge_measurement_limit'
            break
        alternatives=centers.copy()
        moves=[]
        if i:
            for j,sign in enumerate((-1,1)):
                d=(x-centers[j,0])**2+(y-centers[j,1])**2
                for k,dst in enumerate((centers,alternatives)):
                    score=convolve(sign*q,kernels[k],mode='constant')-.15*d/.035**2
                    row,col=np.unravel_index(np.argmax(np.where(d<=.035**2,score,-np.inf)),d.shape)
                    dst[j]=x[row,col],y[row,col]
                    moves.append(float(np.sqrt(d[row,col])))
        q_disks=convolve(q,kernels[2],mode='constant')
        metrics=[]
        for points in (centers,alternatives):
            d=[(x-cx)**2+(y-cy)**2 for cx,cy in points]
            charges=[float(q[(d[j]<=.09**2)&(d[j]<d[1-j])].sum()) for j in range(2)]
            metrics.append(dict(centers=points.tolist(),charges=charges,
                                travel=float(np.linalg.norm(points.mean(axis=0)-initial.mean(axis=0))/diameter),
                                separation=float(np.linalg.norm(points[1]-points[0])/spacing-1)))
        disagreement=float(np.max(np.linalg.norm(centers-alternatives,axis=1)))
        if i:
            fit=metrics[0]['charges']
            nearby=[float(np.max(np.where((x-cx)**2+(y-cy)**2<=.035**2,sign*q_disks,-np.inf)))
                    for (cx,cy),sign in zip(centers,(-1,1))]
        else:
            nearby=[-metrics[0]['charges'][0],metrics[0]['charges'][1]]
        records.append(dict(time=start_time+i*interval_steps*dt,net_charge=net,estimates=metrics,
                            displacement_between_estimates=disagreement,moves=moves,nearby_charge=nearby))
        if disagreement>.035 or any(v>=.034 for v in moves):
            outcome='identity_limit'
            break
        if any(min(-m['charges'][0],m['charges'][1])<.7 for m in metrics):
            outcome='charge_tracking_limit'
            break
        if min(centers.min(),(width-centers).min(),alternatives.min(),(width-alternatives).min())<.09:
            outcome='boundary_limit'
            break
        changes=[m['separation'] for m in metrics]
        if min(changes)>.15 or max(changes)<-.15:
            outcome='spacing_failure'
            break
        if all(m['travel']>=3 and abs(m['separation'])<=.15 for m in metrics):
            outcome='travel_candidate'
            break
    return dict(outcome=outcome,records=records,dt=dt,interval=interval_steps*dt)

import math

def compare(n):
    h=1/(n-1)
    archive=json.loads((root/f'roughness_formation_{n}.json').read_text())
    center=next(i for i,r in enumerate(archive['records']) if 'wall_ancestors' in r)
    interval=archive['records'][1]['time']
    dt=archive['dt']
    gradient,axis=.0002/h**2,225*h*h
    field=pad_north(sim.disorder(n,405,-.12),(n-1)//8)
    results={}
    for i in range(center+3):
        if i>=center-2:
            pair=opposite_pair(localized(field,spacing=h),field=field,spacing=h)
            if pair is not None:
                points=np.array([[c['x'],c['y']] for c in pair])
                diameter=2*h*max(c['radius_cells'] for c in pair)
                result=track(field.copy(),h,dt,axis,0.,points,diameter,i*interval,.013)
                last=result['records'][-1]
                line=points[1]-points[0]
                line/=np.linalg.norm(line)
                side=np.array([line[1],-line[0]])
                elapsed=last['time']-i*interval
                result['transverse']=[((np.array(m['centers'])-points)@side/max(elapsed,1e-30)).tolist()
                                      for m in last['estimates']]
                results[f'{i*interval:.6f}']=result
                print(n,i*interval,result['outcome'],elapsed,result['transverse'],last['nearby_charge'],flush=True)
            else:
                results[f'{i*interval:.6f}']=dict(outcome='no_resolved_pair')
        if i<center+2:
            for _ in range(round(interval/dt)):
                precess(field,dt/h**2,gradient,axis,damping=.75)
    return results
with ThreadPoolExecutor(2) as pool:
    report=dict(zip((113,129),pool.map(compare,(113,129))))
(root/'formation_snapshot_charge_release.json').write_text(json.dumps(report,indent=2)+'\n')
