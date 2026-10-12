"""Matched smooth-deformation robustness test for an individual V1 vortex."""
from __future__ import annotations
import argparse,copy,json
from pathlib import Path
import numpy as np
from genesis_v1_compression_ablation import RULES,make_params
from src.genesis_grid import GenesisState,diagnostics,rules_locking,step
from src.genesis_grid.backend import to_cpu,xp
from src.genesis_grid.defect_tracker import DefectTracker

def twist(state,x,y,amplitude,sigma):
 rows,cols=np.indices((state.N,state.N));dx=np.minimum(abs(cols-x),state.N-abs(cols-x));dy=np.minimum(abs(rows-y),state.N-abs(rows-y));state.theta=(state.theta+amplitude*xp.asarray(np.exp(-(dx*dx+dy*dy)/(2*sigma*sigma))))%(2*xp.pi)
def update(state,tracker,avg,frame):
 plus,minus,_=diagnostics.detect_vortices(state);c=np.asarray(to_cpu(state.C));avg=.95*avg+.05*c;tracks=tracker.update(frame,[(x,y,1) for y,x in plus]+[(x,y,-1) for y,x in minus],C=c,C_avg=avg);return tracks,avg
def follow(state,tracker,avg,key,start,p,a):
 seen=0;end=False
 for f in range(start+1,start+a.follow+1):
  step(state,p,RULES,post=rules_locking.locking_postprocess)
  if f%a.interval:continue
  tracks,avg=update(state,tracker,avg,f)
  alive=any((z.id,z.charge)==key for z in tracks);seen+=alive;end=alive
 return {'continuation_samples':seen,'survived_to_end':end}
def one(seed,a):
 np.random.seed(seed);s=GenesisState(a.N,.05);p=make_params(.1);t=DefectTracker();avg=np.zeros((a.N,a.N));tracks=[]
 for f in range(1,a.burn+1):
  step(s,p,RULES,post=rules_locking.locking_postprocess)
  if f%a.interval==0:tracks,avg=update(s,t,avg,f)
 if not tracks:return {'seed':seed,'status':'none'}
 z=max(tracks,key=lambda q:q.age);key=(z.id,z.charge);bx=(z.x+a.N/2)%a.N;by=(z.y+a.N/2)%a.N;out={}
 for name,loc in [('untouched',None),('core',(z.x,z.y)),('background',(bx,by))]:
  ss=copy.deepcopy(s);tt=copy.deepcopy(t)
  if loc:twist(ss,*loc,a.amplitude,a.sigma)
  out[name]=follow(ss,tt,avg.copy(),key,a.burn,p,a)
 return {'seed':seed,'status':'tested','branches':out}
def main():
 p=argparse.ArgumentParser();p.add_argument('--N',type=int,default=64);p.add_argument('--burn',type=int,default=1000);p.add_argument('--follow',type=int,default=1000);p.add_argument('--interval',type=int,default=25);p.add_argument('--seeds',type=int,default=20);p.add_argument('--amplitude',type=float,default=.5);p.add_argument('--sigma',type=float,default=3);p.add_argument('--output',type=Path,default=Path('results/v1_vortex_robustness.json'));a=p.parse_args();runs=[one(i,a) for i in range(1,a.seeds+1)];tested=[r for r in runs if r['status']=='tested'];summary={n:{'median':float(np.median([r['branches'][n]['continuation_samples'] for r in tested])),'end':sum(r['branches'][n]['survived_to_end'] for r in tested)} for n in ('untouched','core','background')};a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps({'claim_boundary':'Smooth-deformation robustness of a topological candidate only.','runs':runs,'summary':summary},indent=2),encoding='utf-8');print(summary)
if __name__=='__main__':main()
