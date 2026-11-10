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

def capture(field,time,dt):
    assert time==handoff['time'] and dt==archived['dt']
    np.savez_compressed(directory/'refined_cardinal_pair_checkpoint_161_405.npz',field=field,time=time,dt=dt)
    print('formation checkpoint reproduced',time,flush=True)
    coords=(np.arange(len(field)-1)+.5)*h
    x,y=np.meshgrid(coords,coords)
    start=np.array([[c['x'],c['y']] for c in archive_pair])
    positions=start.copy()
    diameter=2*h*max(c['radius_cells'] for c in archive_pair)
    spacing=np.linalg.norm(start[0]-start[1])
    midpoint=start.mean(axis=0)
    radius=.09
    width=(len(field)-1)*h
    records=[]
    outcome='time_limit'
    count=round((archived['records'][1]['time'])/dt)
    stride=max(1,count//8)
    total_steps=round((.14-time)/dt)
    for k in range(0,total_steps+1,stride):
        if k:
            for _ in range(stride):
                sim.precess(field,dt/h**2,.00025/h**2,225*h**2,damping=0.)
        density,ambiguous=charge_map(field)
        net=float(density.sum())
        if ambiguous or abs(net)>.01:
            outcome='neutrality_or_charge_measurement_limit'
            break
        alternate=positions.copy()
        prior=positions.copy()
        if k:
            for j,sign in enumerate((-1,1)):
                neighborhood=(x-prior[j,0])**2+(y-prior[j,1])**2<=.025**2
                # Locate the local signed peak after smoothing over two physical scales.
                for cells,centers in ((3,positions),(5,alternate)):
                    off=np.arange(-cells,cells+1)
                    kernel=(off[:,None]**2+off[None,:]**2<=cells**2).astype(float)
                    score=convolve(sign*density,kernel,mode='constant')
                    row,col=np.unravel_index(np.argmax(np.where(neighborhood,score,-np.inf)),score.shape)
                    centers[j]=x[row,col],y[row,col]
        dist=[(x-cx)**2+(y-cy)**2 for cx,cy in positions]
        charges=[float(density[(dist[j]<=radius**2)&(dist[j]<dist[1-j])].sum()) for j in range(2)]
        travel=float(np.linalg.norm(positions.mean(axis=0)-midpoint)/diameter)
        separation=float(np.linalg.norm(positions[0]-positions[1])/spacing-1)
        disagreement=float(np.max(np.linalg.norm(positions-alternate,axis=1)))
        movement=float(np.max(np.linalg.norm(positions-prior,axis=1)))
        records.append(dict(time=time+k*dt,net_charge=net,charges=charges,centers=positions.tolist(),
                            alternate_centers=alternate.tolist(),disagreement=disagreement,
                            movement=movement,travel_diameters=travel,separation_change=separation))
        if movement>=.022 or disagreement>.025 or min(-charges[0],charges[1])<.7:
            outcome='charge_tracking_limit'
            break
        if min(positions.min(),(width-positions).min())<.09:
            outcome='boundary_limit'
            break
        if abs(separation)>.15:
            # A charge-derived center must agree across both smoothing scales.
            alt_sep=float(np.linalg.norm(alternate[0]-alternate[1])/spacing-1)
            if abs(alt_sep)>.15 and np.sign(alt_sep)==np.sign(separation):
                outcome='separation_gate_failed'
                break
        if travel>=3 and np.linalg.norm(alternate.mean(axis=0)-midpoint)/diameter>=3:
            if abs(separation)<=.15 and abs(np.linalg.norm(alternate[0]-alternate[1])/spacing-1)<=.15:
                outcome='travel_gate_passed'
                break
    result=dict(size=size,seed=405,formation_time=time,dt=dt,stride=stride,
                original_diameter=diameter,original_spacing=spacing,outcome=outcome,records=records)
    (directory/'refined_cardinal_charge_track_161_405.json').write_text(
        json.dumps(result,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    print(outcome,records[-1],flush=True)

run=sim.run(size,405,0.,225.,.14,bias=-.12,factor=.01,mature_charge=.9,
            padding=(size-1)//8,energy_regions=True,cardinal_penalty=.00025,
            require_neutrality=True,capture=capture)
assert json.loads(json.dumps(run['records']))==archived['records']
