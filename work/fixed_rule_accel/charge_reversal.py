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
    # Use a fixed reflection plane and choose its azimuth by initial energy only.
    candidates=[]
    for azimuth in np.arange(24)*np.pi/24:
        normal=np.array([-np.sin(azimuth),np.cos(azimuth),0.])
        reflected=initial-2*(initial@normal)[...,None]*normal
        mixed=(1-blend[...,None])*reflected+blend[...,None]*initial
        norm=np.linalg.norm(mixed,axis=-1)
        if norm.min()<.1:
            continue
        mixed/=norm[...,None]
        mixed[blend==1]=initial[blend==1]
        reading=localized(mixed)
        swapped=opposite_pair(reading,field=mixed,spacing=h)
        if swapped is None:
            continue
        reversed_positions=np.array([[c['x'],c['y']] for c in swapped])[::-1]
        if np.max(np.linalg.norm(reversed_positions-positions,axis=1))>h:
            continue
        energy=measure(mixed,gradient,axis)['energy']
        candidates.append((energy,float(azimuth),float(norm.min()),mixed))
    assert candidates, f'No admissible local reversal for {size}'
    energy,azimuth,min_norm,reversed_field=min(candidates,key=lambda c:c[0])
    print(size,'reversal',len(candidates),azimuth,'energy ratio',energy/measure(initial,gradient,axis)['energy'],flush=True)
    results={}
    for label,source in (('native',initial),('reversed',reversed_field)):
        for exterior in ('native','quiet'):
            field=source.copy()
            if exterior=='quiet':
                polar=np.arctan2(np.hypot(field[...,0],field[...,1]),field[...,2])*(1-blend)
                phase=np.arctan2(field[...,1],field[...,0])
                mask=blend>0
                quiet=np.stack((np.sin(polar)*np.cos(phase),np.sin(polar)*np.sin(phase),np.cos(polar)),axis=-1)
                field[mask]=quiet[mask]
            records,dt=pair_swap.evolve(field,h,gradient,axis,.04)
            results[f'{label}_{exterior}']=records
    report=dict(size=size,dt=dt,reflection_angle=azimuth,minimum_blend_norm=min_norm,
                qualified_reflections=len(candidates),reversed_energy=energy,runs=results)
    (root/f'charge_reversal_{size}.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(size,[(k,len(v),v[-1].get('separation')) for k,v in results.items()],flush=True)

with ThreadPoolExecutor(2) as pool:
    list(pool.map(run,(113,129)))
