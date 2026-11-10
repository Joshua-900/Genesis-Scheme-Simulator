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
from src.genesis_v3.pair_swap import pad_north
from src.genesis_v3.wall_handoff import opposite_pair, prepare
from scipy.ndimage import convolve

base=Path('results/genesis_v3_fixed_rule')
controls=Path('results/genesis_v3_wall_handoff')

def scan(field, archive, penalty, steps_per_sample, cap, floor=None):
    n=archive['size']
    h=1/(n-1)
    dt=archive['dt']
    coords=(np.arange(len(field)-1)+.5)*h
    x,y=np.meshgrid(coords,coords)
    offsets=np.arange(-int(np.ceil(.045/h)),int(np.ceil(.045/h))+1)*h
    kernel=(offsets[:,None]**2+offsets[None,:]**2<=.045**2).astype(float)
    first=next((r for r in archive['records'] if r.get('wall_ancestors')),archive['records'][0])
    initial=opposite_pair(first)
    assert initial is not None
    centers=np.array([[c['x'],c['y']] for c in initial])
    midpoint=centers.mean(axis=0)
    separation=np.linalg.norm(centers[0]-centers[1])
    diameter=2*h*max(c['radius_cells'] for c in initial)
    records=[]
    low_count=0
    outcome='time_limit'
    for i in range(cap+1):
        if i:
            for _ in range(steps_per_sample):
                sim.precess(field,dt/h**2,penalty/h**2,225*h**2,damping=0.)
        density,ambiguous=charge_map(field)
        net=float(density.sum())
        prior=centers.copy()
        if i:
            for j,sign in enumerate((-1,1)):
                dist=(x-prior[j,0])**2+(y-prior[j,1])**2
                score=convolve(sign*density,kernel,mode='constant')
                # Prefer a nearby center when competing disks contain similar charge.
                merit=score-.1*dist/.035**2
                row,col=np.unravel_index(np.argmax(np.where(dist<=.035**2,merit,-np.inf)),score.shape)
                centers[j]=x[row,col],y[row,col]
        travel=float(np.linalg.norm(centers.mean(axis=0)-midpoint)/diameter)
        spacing=float(np.linalg.norm(centers[0]-centers[1])/separation-1)
        stats=[]
        for j,sign in enumerate((-1,1)):
            d=(x-centers[j,0])**2+(y-centers[j,1])**2
            other=(x-centers[1-j,0])**2+(y-centers[1-j,1])**2
            signed=sign*density
            mass=np.maximum(signed,0)
            inner=d<=.045**2
            outer=(d<=.09**2)&(d<other)
            stats.append(dict(charge=float(signed[outer].sum()),
                              compactness=float(mass[inner&outer].sum()/mass[outer].sum()),
                              inner_charge=float(signed[inner&outer].sum())))
        motion=float(np.max(np.linalg.norm(centers-prior,axis=1)))
        records.append(dict(time=first['time']+i*steps_per_sample*dt,centers=centers.tolist(),
                            cores=stats,travel=travel,separation=spacing,motion=motion,net_charge=net))
        if ambiguous or abs(net)>.01 or motion>=.034:
            outcome='identity_limit'
            break
        if min(centers.min(),((len(field)-1)*h-centers).min())<.09:
            outcome='boundary_limit'
            break
        if floor is not None:
            low_count=low_count+1 if min(c['compactness'] for c in stats)<floor else 0
            if low_count>=2 and False:
                outcome='compactness_below_control'
                break
            if min(c['charge'] for c in stats)<.7:
                outcome='charge_limit'
                break
            if abs(spacing)>.15:
                outcome='separation_gate_failed'
                break
            if travel>=3:
                outcome='travel_candidate'
                break
    return dict(outcome=outcome,records=records,steps_per_sample=steps_per_sample)

floor=json.loads((base/'refined_compactness_control_113.json').read_text())['compactness_floor']
archive=json.loads((base/'refined_cardinal_extended_161_405.json').read_text())
with np.load(base/'refined_cardinal_pair_checkpoint_161_405.npz') as saved:
    field=saved['field']
stride=round(archive['records'][1]['time']/archive['dt'])//4
cap=int((.14-next(r['time'] for r in archive['records'] if r.get('wall_ancestors')))/(stride*archive['dt']))
result=scan(field,archive,.00025,stride,cap,floor)
result['compactness_floor']=floor
(base/'refined_compactness_merge_161.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print('candidate',len(result['records']),result['outcome'],result['records'][-1],flush=True)


