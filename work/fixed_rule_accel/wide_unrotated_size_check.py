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

from scipy.ndimage import label
from src.genesis_v3.model import charge_map

p=Path('results/genesis_v3_fixed_rule')
size=113
h=1/(size-1)
archive=json.loads((p/f'wide_unrotated_travel_{size}.json').read_text())['branches']['0']['records']
with np.load(p/f'wide_unrotated_endpoint_{size}.npz') as saved:
    field=saved['field']
    dt=float(saved['dt'])
    time=float(saved['time'])
start=np.array([[c['x'],c['y']] for c in sorted(archive[0]['cores'],key=lambda c:c['charge']) if abs(c['charge'])>=.7])
last=np.array([[c['x'],c['y']] for c in sorted(archive[-2]['cores'],key=lambda c:c['charge']) if abs(c['charge'])>=.7])
initial_spacing=np.linalg.norm(start[1]-start[0])
diameter=2*h*max(c['radius_cells'] for c in archive[0]['cores'] if abs(c['charge'])>=.7)
x,y=np.meshgrid((np.arange(len(field)-1)+.5)*h,(np.arange(len(field)-1)+.5)*h)
xx,yy=np.meshgrid(np.arange(len(field))*h,np.arange(len(field))*h)
records=[]
for i in range(9):
    if i:
        for _ in range(round(.0025/dt)):
            precess(field,dt/h**2,.0002/h**2,225*h**2,damping=0.)
    labels,_=label(field[...,2]<0)
    sizes=np.bincount(labels.ravel())
    charge,ambiguous=charge_map(field)
    readings=[]
    for j,sign in enumerate((-1,1)):
        d=(xx-last[j,0])**2+(yy-last[j,1])**2
        index=np.unravel_index(np.argmin(np.where((labels>0)&(d<=.035**2),d,np.inf)),d.shape)
        component=labels[index]
        if not component or not np.isfinite(d[index]) or d[index]>.035**2:
            break
        mask=labels==component
        weight=(1-field[...,2])[mask]
        last[j]=[np.average(a[mask],weights=weight) for a in (xx,yy)]
        disk=(x-last[j,0])**2+(y-last[j,1])**2<=.09**2
        readings.append(dict(radius_cells=float(np.sqrt(sizes[component]/np.pi)),
                             charge=float(charge[disk].sum()),center=last[j].tolist()))
    if len(readings)!=2:
        break
    spacing=float(np.linalg.norm(last[1]-last[0])/initial_spacing-1)
    travel=float(np.linalg.norm(last.mean(axis=0)-start.mean(axis=0))/diameter)
    row=dict(time=time+i*.0025,cores=readings,spacing_change=spacing,travel_diameters=travel,
             ambiguous=ambiguous,net_charge=float(charge.sum()))
    records.append(row)
    print(row,flush=True)
    if abs(spacing)>.15 or ambiguous or abs(charge.sum())>.01 or min(-readings[0]['charge'],readings[1]['charge'])<.7:
        break
(p/'wide_unrotated_size_check_113.json').write_text(json.dumps(dict(records=records),indent=2)+'\n',encoding='utf-8')
