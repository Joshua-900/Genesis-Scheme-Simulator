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


from src.genesis_v3 import pair_swap
from src.genesis_v3.formation import localized
from src.genesis_v3.model import measure
from src.genesis_v3.wall_handoff import opposite_pair

pair_swap.precess=lambda field,dt,gradient,axis: precess(field,dt,gradient,axis,damping=0.)
root=Path('results/genesis_v3_fixed_rule')

def run(size):
    h=1/(size-1)
    gradient,axis=.0002/h**2,225*h**2
    with np.load(root/f'damping_handoff_{size}.npz') as saved:
        initial=saved['field']
    pair=opposite_pair(localized(initial))
    positions=np.array([[c['x'],c['y']] for c in pair])
    x,y=np.meshgrid(np.linspace(0,1,size),np.linspace(0,1,size))
    points=np.stack((x,y),axis=-1)
    segment=positions[1]-positions[0]
    fraction=np.clip((points-positions[0])@segment/(segment@segment),0,1)
    radius=np.linalg.norm(points-positions[0]-fraction[...,None]*segment,axis=-1)
    taper=np.clip((radius-.10)/.055,0,1)
    blend=taper**2*(3-2*taper)
    reports={}
    for degrees in (0,90,180,270,-90):
        field=initial.copy()
        angle=np.deg2rad(degrees)*(1-blend)
        c,s=np.cos(angle),np.sin(angle)
        field[...,0]=c*initial[...,0]-s*initial[...,1]
        field[...,1]=s*initial[...,0]+c*initial[...,1]
        records,dt=pair_swap.evolve(field,h,gradient,axis,.04)
        distances=[r['separation']/records[0]['separation']-1 for r in records if 'separation' in r]
        first=opposite_pair(records[0])
        assert first is not None
        start=np.array([[v['x'],v['y']] for v in first])
        assert np.max(np.abs(start-positions))<1e-12
        diameter=2*h*max(v['radius_cells'] for v in first)
        midpoint=np.array([r['midpoint'] for r in records if 'midpoint' in r])
        travel=float(np.linalg.norm(midpoint[-1]-midpoint[0])/diameter)
        edge=min(min(v['x'],v['y'],1-v['x'],1-v['y']) for r in records for v in r['cores'] if abs(v['charge'])>=.7)
        ok=len(distances)==17 and max(map(abs,distances))<=.15 and edge>=.09
        reports[str(degrees)]=dict(qualified=bool(ok),travel=travel,edge=edge,spacing=distances,records=records)
        print(size,degrees,ok,travel,distances[-1],max(map(abs,distances)),edge,flush=True)
    (root/f'phase_alignment_{size}.json').write_text(json.dumps(dict(size=size,dt=dt,runs=reports),indent=2)+'\n',encoding='utf-8')
with ThreadPoolExecutor(2) as pool:
    list(pool.map(run,(113,129)))

