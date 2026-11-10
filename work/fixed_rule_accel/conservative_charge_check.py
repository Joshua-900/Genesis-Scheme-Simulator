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


from src.genesis_v3.model import charge_map, measure
import math

def early(size):
    h=1/(size-1)
    pad=(size-1)//8
    field=np.zeros((size+2*pad,size+2*pad,3))
    field[...,2]=1
    field[pad:-pad,pad:-pad]=sim.disorder(size,405,-.12)
    gradient,axis=.0002/h**2,225*h**2
    branches=[]
    for factor in (.02,.005):
        state=field.copy()
        interval=.000125
        count=math.ceil(interval/(factor*h*h))
        records=[]
        for sample in range(41):
            density,ambiguous=charge_map(state)
            records.append(dict(time=sample*interval,charge=float(density.sum()),
                                ambiguous_triangles=ambiguous,
                                energy=measure(state,gradient,axis)['energy']))
            if sample<40:
                for _ in range(count):
                    precess(state,interval/(count*h*h),gradient,axis,damping=0.)
        branches.append(dict(factor=factor,dt=interval/count,records=records))
        print(size,factor,next((r['time'] for r in records if abs(r['charge'])>.01),None),
              records[-1]['charge'],flush=True)
    out=Path(f'results/genesis_v3_fixed_rule/conservative_charge_check_{size}.json')
    out.write_text(json.dumps(dict(size=size,branches=branches),indent=2)+'\n',encoding='utf-8')
with ThreadPoolExecutor(2) as pool:
    list(pool.map(early,(113,129)))
