"""Compare Genesis starting fields with a rigidly traveling, precessing profile."""
import json
from pathlib import Path

import numpy as np

from src.genesis_v3.formation import localized
from src.genesis_v3.model import effective_field
from src.genesis_v3.pair_swap import pad_north
from src.genesis_v3.wall_handoff import opposite_pair, prepare

ROOT=Path('results/genesis_v3_fixed_rule')

def score(field,h,gradient,axis):
    pair=opposite_pair(localized(field,spacing=h),field=field,spacing=h)
    assert pair is not None
    points=np.array([[c['x'],c['y']] for c in pair])
    coord=np.arange(1,len(field)-1)*h
    x,y=np.meshgrid(coord,coord)
    pos=np.stack((x,y),axis=-1)
    a,b=points
    line=b-a
    fraction=np.clip((pos-a)@line/(line@line),0,1)
    distance=np.linalg.norm(pos-a-fraction[...,None]*line,axis=-1)
    n=field[1:-1,1:-1]
    tangent=np.cross(n,effective_field(field,gradient,axis))/h**2
    dx=(field[1:-1,2:]-field[1:-1,:-2])/(2*h)
    dy=(field[2:,1:-1]-field[:-2,1:-1])/(2*h)
    # The finite differences are projected into the local tangent plane.
    dx-=n*np.sum(n*dx,axis=-1,keepdims=True)
    dy-=n*np.sum(n*dy,axis=-1,keepdims=True)
    phase=np.cross([0,0,1],n)
    selected=distance<=.14
    design=np.stack([-dx[selected].ravel(),-dy[selected].ravel(),phase[selected].ravel()],axis=1)
    actual=tangent[selected].ravel()
    fit=np.linalg.lstsq(design,actual,rcond=None)[0]
    return dict(residual=float(np.linalg.norm(actual-design@fit)/np.linalg.norm(actual)),
                velocity=fit[:2].tolist(),phase_rate=float(fit[2]),points=points.tolist())

def main():
    report={}
    for size in (113,129):
        h=1/(size-1)
        field,_,gradient,axis=prepare(size,405,mature=True)
        with np.load(ROOT/f'damping_handoff_{size}.npz') as f:
            contracting=f['field']
        report[str(size)]={}
        for name,state in [('staged',field),('contracting',contracting)]:
            result=score(pad_north(state,(size-1)//8),h,gradient,axis)
            report[str(size)][name]=result
            print(size,name,result,flush=True)
    (ROOT/'traveling_profile_comparison.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')

if __name__=='__main__':
    main()
