import ctypes
from concurrent.futures import ThreadPoolExecutor
import json
import math
from pathlib import Path

import numpy as np

from src.genesis_v3 import rotation
from src.genesis_v3.formation import disorder, localized
from src.genesis_v3.model import charge_map, measure

tick = ctypes.CDLL(str(Path('work/fixed_rule_accel/diagonal_step.dll').resolve())).tick
tick.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_int] + [ctypes.c_double]*5
tick.restype = None
modes = {'original': (.0002, 0.), 'cardinal': (.00025, 0.), 'diagonal': (.0002, .0000125)}
interval = .000125
factor = .005

def reference(field, gradient, axis):
    result = effective(field, gradient, axis)
    center = field[1:-1,1:-1]
    for neighbor in (field[:-2,:-2],field[:-2,2:],field[2:,:-2],field[2:,2:]):
        diff = neighbor-center
        result += diagonal * np.sum(diff*diff,axis=-1,keepdims=True)*diff
    return result

effective = rotation.effective_field
diagonal = .0000125*64**2
a = disorder(65,405,-.12)
b = a.copy()
buffer = np.zeros(5*b.size)
rotation.effective_field = reference
for _ in range(1000):
    rotation.precess(a,factor,.0002*64**2,225/64**2)
    tick(b.ctypes.data,buffer.ctypes.data,len(b),factor,.0002*64**2,225/64**2,0.,diagonal)
rotation.effective_field = effective
error = float(np.max(np.abs(a-b)))
assert error < 1e-10, error
print('compiled vs NumPy',error,flush=True)

def run(job):
    size,mode=job
    h=1/(size-1)
    pad=(size-1)//8
    field=np.zeros((size+2*pad,size+2*pad,3))
    field[...,2]=1
    field[pad:-pad,pad:-pad]=disorder(size,405,-.12)
    buffer=np.zeros(5*field.size)
    gradient,diag=np.array(modes[mode])/h**2
    axis=225*h**2
    steps=math.ceil(interval/(factor*h*h))
    dt=interval/steps
    records=[]
    for i in range(81):
        q,ambiguous=charge_map(field)
        alternative=-float(charge_map(field[:,::-1,:])[0].sum())
        wall=[]
        if i%4==0:
            reading=localized(field,labels_out=np.empty(field.shape[:2],dtype=np.int32),spacing=h)
            wall=[c for c in reading['cores'] if c['span']>=.23 and c['min_z']<=-.75]
        energy=measure(field,gradient,axis)['energy']
        for u,v in ((field[:-1,:-1],field[1:,1:]),(field[:-1,1:],field[1:,:-1])):
            energy+=.25*diag*float(np.sum(np.sum((u-v)**2,axis=-1)**2))
        records.append(dict(time=i*interval,charge=float(q.sum()),alternate_charge=alternative,
                            ambiguous_triangles=ambiguous,wall_regions=wall,energy=energy))
        if i<80:
            for _ in range(steps):
                tick(field.ctypes.data,buffer.ctypes.data,len(field),dt/h**2,gradient,axis,0.,diag)
    report=dict(size=size,mode=mode,seed=405,dt=dt,step_factor=factor,padding=pad,
                cardinal_penalty=modes[mode][0],diagonal_penalty=modes[mode][1],
                compiled_reference_error=error,records=records)
    path=Path(f'results/genesis_v3_fixed_rule/diagonal_screen_{size}_{mode}.json')
    path.write_text(json.dumps(report,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    first=lambda key: next((r['time'] for r in records if abs(r[key])>.01),None)
    print(size,mode,first('charge'),first('alternate_charge'),records[-1]['charge'],
          sum(bool(r['wall_regions']) for r in records),flush=True)

with ThreadPoolExecutor(3) as pool:
    list(pool.map(run,[(size,mode) for size in (113,129) for mode in modes]))
