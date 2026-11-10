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


def run(size):
    path=Path(f'results/genesis_v3_fixed_rule/diagonal_screen_{size}_cardinal.json')
    screen=json.loads(path.read_text())
    samples=screen['records']
    assert any(r['wall_regions'] for r in samples)
    assert all(max(abs(r['charge']),abs(r['alternate_charge']))<=.01 for r in samples)
    r=sim.run(size,405,0.,225.,.14,bias=-.12,factor=.01,mature_charge=.9,
              padding=(size-1)//8,energy_regions=True,cardinal_penalty=.00025,
              require_neutrality=True)
    r['compiled_step_check_max_error']=error
    p=Path(f'results/genesis_v3_fixed_rule/refined_cardinal_extended_{size}_405.json')
    p.write_text(json.dumps(r,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    print(size,r['outcome'],r['records'][-1]['time'],flush=True)
with ThreadPoolExecutor(2) as pool:
    list(pool.map(run,(161,193)))
