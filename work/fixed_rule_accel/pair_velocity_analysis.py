import itertools
import json
from pathlib import Path
import numpy as np

root = Path('results/genesis_v3_fixed_rule')
windows = ((0., .0025), (0., .01), (.01, .02), (.02, .04), (0., .04))

def points(record):
    candidates = [c for c in record['cores'] if abs(c['charge']) >= .7]
    for a, b in itertools.combinations(sorted(candidates,key=lambda c:c['charge']), 2):
        if not a['charge'] < 0 < b['charge']:
            continue
        xy = np.array([[c['x'],c['y']] for c in (a,b)])
        if np.allclose(xy.mean(axis=0),record['midpoint'],rtol=0,atol=1e-12) and np.isclose(
                np.linalg.norm(xy[1]-xy[0]),record['separation'],rtol=0,atol=1e-12):
            return xy
    raise ValueError(f"Could not reconstruct the pair at {record['time']}")

def analyze(records):
    positions = {round(s['time'],8):points(s) for s in records if 'midpoint' in s}
    initial = positions[0.]
    line = initial[1]-initial[0]
    line /= np.linalg.norm(line)
    forward = np.array([line[1],-line[0]])
    rows = []
    for start,end in windows:
        if start not in positions or end not in positions:
            continue
        a,b = positions[start],positions[end]
        velocity = (b-a)/(end-start)
        axial, transverse = velocity@line, velocity@forward
        approach = (np.linalg.norm(a[1]-a[0])-np.linalg.norm(b[1]-b[0]))/(end-start)
        rows.append(dict(start=start,end=end,velocity=velocity.tolist(),
                         inward=[float(axial[0]),float(-axial[1])],
                         forward=transverse.tolist(),midpoint_speed=float(np.linalg.norm(velocity.mean(axis=0))),
                         approach=float(approach)))
    return rows

report={}
for size in (113,129):
    src=json.loads((root/f'pair_swap_{size}_fixed_boundary.json').read_text())
    report[str(size)]={name:analyze(run['records']) for name,run in src['runs'].items()}
    for name,rows in report[str(size)].items():
        print(size,name)
        for r in rows:
            print(r['start'],r['end'], 'in',np.round(r['inward'],3),'forward',np.round(r['forward'],3),'approach',round(r['approach'],3))
halo={}
for size in (113,129):
    src=json.loads((root/f'halo_probe_{size}.json').read_text())
    halo[str(size)]={name:analyze(run) for name,run in src['runs'].items()}
    for name,rows in halo[str(size)].items():
        print(size,name,[(r['start'],r['end'],np.round(r['inward'],3).tolist(),round(r['approach'],3)) for r in rows])
(root/'pair_swap_velocity_comparison.json').write_text(json.dumps(dict(swaps=report,halo=halo),indent=2)+'\n',encoding='utf-8')


