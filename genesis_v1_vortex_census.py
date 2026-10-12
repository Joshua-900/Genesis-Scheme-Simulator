"""Headless census of individual, topologically charged V1 vortex candidates."""
from __future__ import annotations
import argparse, json
from pathlib import Path
import numpy as np
from genesis_v1_compression_ablation import RULES, make_params
from src.genesis_grid import GenesisState, diagnostics, rules_locking, step
from src.genesis_grid.backend import to_cpu
from src.genesis_grid.defect_tracker import DefectTracker

def main():
 p=argparse.ArgumentParser(description='Census individual topological vortex candidates.')
 p.add_argument('--N',type=int,default=64);p.add_argument('--frames',type=int,default=3000);p.add_argument('--seeds',type=int,default=10);p.add_argument('--sample-interval',type=int,default=25);p.add_argument('--kappa',type=float,default=.1);p.add_argument('--min-age',type=int,default=500);p.add_argument('--output',type=Path,default=Path('results/v1_vortex_census.json'));a=p.parse_args(); records=[];runs=[]
 for seed in range(1,a.seeds+1):
  np.random.seed(seed);s=GenesisState(a.N,.05);params=make_params(a.kappa);t=DefectTracker();avg=np.zeros((a.N,a.N));life={}
  for f in range(1,a.frames+1):
   step(s,params,RULES,post=rules_locking.locking_postprocess)
   if f%a.sample_interval:continue
   plus,minus,w=diagnostics.detect_vortices(s);c=np.asarray(to_cpu(s.C));avg=.95*avg+.05*c;tracks=t.update(f,[(x,y,1) for y,x in plus]+[(x,y,-1) for y,x in minus],C=c,C_avg=avg)
   for z in tracks:
    r=life.setdefault(z.id,{'seed':seed,'id':z.id,'charge':z.charge,'birth':z.birth_frame,'last_seen':z.last_seen_frame,'max_age':0,'observations':0,'max_speed':0.0})
    r['last_seen']=z.last_seen_frame;r['max_age']=max(r['max_age'],z.age);r['observations']+=1;r['max_speed']=max(r['max_speed'],float(np.hypot(z.vx,z.vy)))
  records.extend(life.values());runs.append({'seed':seed,'observed':len(life),'persistent':sum(r['max_age']>=a.min_age for r in life.values()),'final_net_winding':int(np.sum(w))});print(seed,runs[-1])
 persistent=[r for r in records if r['max_age']>=a.min_age]
 out={'schema_version':1,'claim_boundary':'Topological candidate census only; persistence does not alone establish autonomy or metaphysics.','experiment':{'N':a.N,'frames':a.frames,'seeds':a.seeds,'kappa':a.kappa,'min_age':a.min_age},'runs':runs,'summary':{'observed':len(records),'persistent':len(persistent),'median_persistent_age':float(np.median([r['max_age'] for r in persistent])) if persistent else 0.0},'vortices':records}
 a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(out,indent=2),encoding='utf-8');print(out['summary'])
if __name__=='__main__':main()
