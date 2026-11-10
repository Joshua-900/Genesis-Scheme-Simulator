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
from src.genesis_v3.wall_handoff import opposite_pair
from scipy.ndimage import convolve

size=161
h=1/(size-1)
directory=Path('results/genesis_v3_fixed_rule')
archived=json.loads((directory/'refined_cardinal_extended_161_405.json').read_text())
handoff=next(r for r in archived['records'] if 'wall_ancestors' in r)
archive_pair=opposite_pair(handoff)
assert archive_pair is not None


checkpoint=np.load(directory/'refined_cardinal_pair_checkpoint_161_405.npz')
field=checkpoint['field']
time=float(checkpoint['time'])
dt=float(checkpoint['dt'])
coords=(np.arange(len(field)-1)+.5)*h
x,y=np.meshgrid(coords,coords)
start=np.array([[c['x'],c['y']] for c in archive_pair])
diameter=2*h*max(c['radius_cells'] for c in archive_pair)
spacing=np.linalg.norm(start[0]-start[1])
midpoint=start.mean(axis=0)
positions=[start.copy(),start.copy()]
stride=round(archived['records'][1]['time']/dt)//8
records=[]
outcome='time_limit'
for k in range(0,round((.14-time)/dt)+1,stride):
    if k:
        for _ in range(stride):
            sim.precess(field,dt/h**2,.00025/h**2,225*h**2,damping=0.)
    density,ambiguous=charge_map(field)
    net=float(density.sum())
    if ambiguous or abs(net)>.01:
        outcome='neutrality_or_charge_measurement_limit'
        break
    motion=[]
    if k:
        for centers,sigma in zip(positions,(.01875,.025)):
            prior=centers.copy()
            for j,sign in enumerate((-1,1)):
                d=(x-prior[j,0])**2+(y-prior[j,1])**2
                weight=np.maximum(sign*density,0)*np.exp(-d/(2*sigma**2))*(d<=.055**2)
                centers[j]=[(weight*x).sum()/weight.sum(),(weight*y).sum()/weight.sum()]
            motion.append(float(np.max(np.linalg.norm(centers-prior,axis=1))))
    metrics=[]
    for centers in positions:
        d=[(x-cx)**2+(y-cy)**2 for cx,cy in centers]
        charges=[float(density[(d[j]<=.09**2)&(d[j]<d[1-j])].sum()) for j in range(2)]
        metrics.append(dict(centers=centers.tolist(),charges=charges,
                            travel=float(np.linalg.norm(centers.mean(axis=0)-midpoint)/diameter),
                            separation=float(np.linalg.norm(centers[0]-centers[1])/spacing-1)))
    diff=float(np.max(np.linalg.norm(positions[0]-positions[1],axis=1)))
    records.append(dict(time=time+k*dt,net_charge=net,estimates=metrics,disagreement=diff,motion=motion))
    if diff>.025 or any(m>=.022 for m in motion) or any(min(-m['charges'][0],m['charges'][1])<.7 for m in metrics):
        outcome='charge_tracking_limit'
        break
    if any(min(p.min(),((len(field)-1)*h-p).min())<.09 for p in positions):
        outcome='boundary_limit'
        break
    if all(m['separation']>.15 for m in metrics) or all(m['separation']<-.15 for m in metrics):
        outcome='separation_gate_failed'
        break
    if all(m['travel']>=3 and abs(m['separation'])<=.15 for m in metrics):
        outcome='travel_gate_candidate'
        break
    if k and k//stride%8==0:
        print(records[-1],flush=True)
# Check the stopping sample for a qualifying disk just outside either estimated center.
off=np.arange(-int(np.ceil(.09/h)),int(np.ceil(.09/h))+1)*h
kernel=(off[:,None]**2+off[None,:]**2<=.09**2).astype(float)
disk_charge=convolve(density,kernel,mode='constant')
near=np.logical_or.reduce([(x-p[0,0])**2+(y-p[0,1])**2<=.03**2 for p in positions])
row,col=np.unravel_index(np.argmin(np.where(near,disk_charge,np.inf)),disk_charge.shape)
nearby=dict(radius=.03,center=[float(x[row,col]),float(y[row,col])],charge=float(disk_charge[row,col]))
print('endpoint nearby disk',nearby,flush=True)
result=dict(nearby_negative_disk=nearby,size=size,seed=405,formation_time=time,dt=dt,stride=stride,original_diameter=diameter,
            original_spacing=spacing,outcome=outcome,records=records)
(directory/'refined_cardinal_charge_centroid_161_405.json').write_text(
    json.dumps(result,indent=2,allow_nan=False)+'\n',encoding='utf-8')
print(outcome,records[-1],flush=True)

