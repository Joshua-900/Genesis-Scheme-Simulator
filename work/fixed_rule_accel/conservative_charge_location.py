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


from src.genesis_v3.model import charge_map
import math

def triangles(field):
    a,b=field[:-1,:-1],field[:-1,1:]
    c,d=field[1:,1:],field[1:,:-1]
    return [(a,b,c),(a,c,d)]

def geometry(vertices):
    u,v,w=vertices
    dots=np.array([u@v,v@w,w@u])
    num=float(u@np.cross(v,w))
    den=float(1+dots.sum())
    return dict(numerator=num,denominator=den,charge=float(np.arctan2(num,den)/(2*np.pi)),
                edge_degrees=np.degrees(np.arccos(np.clip(dots,-1,1))).tolist(),
                z=vertices[:,2].tolist())

def locate(job):
    size,factor=job
    h=1/(size-1)
    pad=(size-1)//8
    field=np.zeros((size+2*pad,size+2*pad,3))
    field[...,2]=1
    field[pad:-pad,pad:-pad]=sim.disorder(size,405,-.12)
    gradient,axis=.0002/h**2,225*h**2
    count=math.ceil(.000125/(factor*h*h))
    dt=.000125/count
    for k in range(1,12*count+1):
        before=field.copy() if k>=10*count else None
        precess(field,dt/h**2,gradient,axis,damping=0.)
        if before is None:
            continue
        prev_charge=float(charge_map(before)[0].sum())
        post_charge=float(charge_map(field)[0].sum())
        if abs(post_charge-prev_charge)<.5:
            continue
        events=[]
        for i,(old,new) in enumerate(zip(triangles(before),triangles(field))):
            def arrays(vertices):
                u,v,w=vertices
                num=np.sum(u*np.cross(v,w),axis=-1)
                den=1+np.sum(u*v+v*w+w*u,axis=-1)
                return np.arctan2(num,den)/(2*np.pi)
            for row,col in np.argwhere(np.abs(arrays(new)-arrays(old))>.5):
                prev=geometry(np.array([v[row,col] for v in old]))
                curr=geometry(np.array([v[row,col] for v in new]))
                offsets=(((2/3,1/3),(1/3,2/3)))[i]
                x,y=(col+offsets[0]-pad)*h,(row+offsets[1]-pad)*h
                events.append(dict(triangle=i,row=int(row),column=int(col),x=x,y=y,
                                   distance_from_original_edge=min(x,y,1-x,1-y),
                                   before=prev,after=curr))
        result=dict(size=size,padding=pad,seed=405,factor=factor,dt=dt,time_before=(k-1)*dt,
                    time_after=k*dt,net_before=prev_charge,net_after=post_charge,events=events)
        print(json.dumps(result),flush=True)
        return result
    raise RuntimeError(f'No charge jump bracketed for {job}')

with ThreadPoolExecutor(2) as pool:
    results=list(pool.map(locate,[(113,.005),(129,.005),(113,.0025),(129,.0025)]))
Path('results/genesis_v3_fixed_rule/conservative_charge_location_405.json').write_text(
    json.dumps(results,indent=2,allow_nan=False)+'\n',encoding='utf-8')
