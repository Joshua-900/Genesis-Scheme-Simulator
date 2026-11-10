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
from scipy.ndimage import convolve

size=161
archive=json.loads(Path(f'results/genesis_v3_fixed_rule/refined_cardinal_extended_{size}_405.json').read_text())
prior=archive['records'][-2]
negative=min(prior['cores'],key=lambda c:c['charge'])
h=1/(size-1)
localize=sim.localized
readings=[]
calls=0
def inspect(field,*args,**kwargs):
    global calls
    result=localize(field,*args,**kwargs)
    if calls>=len(archive['records'])-3:
        density,_=charge_map(field)
        axis=(np.arange(len(density))+.5)*h
        x,y=np.meshgrid(axis,axis)
        distance=(x-negative['x'])**2+(y-negative['y'])**2
        radial=np.arange(-int(np.ceil(.09/h)),int(np.ceil(.09/h))+1)*h
        disk=radial[:,None]**2+radial[None,:]**2<=.09**2
        summed=convolve(density,disk.astype(float),mode='constant')
        near=distance<=.06**2
        index=np.unravel_index(np.argmin(np.where(near,summed,np.inf)),summed.shape)
        readings.append(dict(sample=calls,time=archive['records'][calls]['time'],
                             fixed_disk_charge=float(density[distance<=.09**2].sum()),
                             nearby_min_charge=float(summed[index]),nearby_min_center=[float(x[index]),float(y[index])]))
        print(readings[-1],flush=True)
    calls+=1
    return result

sim.localized=inspect
run=sim.run(size,405,0.,225.,.14,bias=-.12,factor=.01,mature_charge=.9,padding=(size-1)//8,
            energy_regions=True,cardinal_penalty=.00025,require_neutrality=True)
assert json.loads(json.dumps(run['records']))==archive['records'], 'Archived trajectory did not reproduce'
result=dict(size=size,seed=405,reference_center=[negative['x'],negative['y']],
            measurement_radius=.09,search_radius=.06,readings=readings)
Path('results/genesis_v3_fixed_rule/refined_cardinal_core_check_161_405.json').write_text(
    json.dumps(result,indent=2,allow_nan=False)+'\n',encoding='utf-8')

