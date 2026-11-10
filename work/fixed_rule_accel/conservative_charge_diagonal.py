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

def alternate(size):
    h=1/(size-1)
    pad=(size-1)//8
    field=np.zeros((size+2*pad,size+2*pad,3))
    field[...,2]=1
    field[pad:-pad,pad:-pad]=sim.disorder(size,405,-.12)
    count=math.ceil(.000125/(.005*h*h))
    dt=.000125/count
    flip_charge=lambda f: -float(charge_map(f[:,::-1,:])[0].sum())
    samples=[]
    for k in range(13*count+1):
        if k%count==0:
            samples.append(dict(time=k*dt,standard=float(charge_map(field)[0].sum()),alternate=flip_charge(field)))
        if k<13*count:
            precess(field,dt/h**2,.0002/h**2,225*h**2,damping=0.)
    print(size,[(r['time'],round(r['standard']),round(r['alternate'])) for r in samples[-4:]],flush=True)
    return dict(size=size,dt=dt,samples=samples)
with ThreadPoolExecutor(2) as pool:
    results=list(pool.map(alternate,(113,129)))
Path('results/genesis_v3_fixed_rule/conservative_charge_diagonal_405.json').write_text(
    json.dumps(results,indent=2,allow_nan=False)+'\n',encoding='utf-8')
