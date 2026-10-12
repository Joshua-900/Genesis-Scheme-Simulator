"""Screen compression-gated structural memory in the V1 candidate regime."""
from __future__ import annotations
import argparse, json
from pathlib import Path
import numpy as np
from genesis_v1_compression_ablation import make_params
from src.genesis_grid import GenesisState, diagnostics, rules_alignment, rules_compression, rules_curvature, rules_locking, step
from src.genesis_grid import rules_structural_memory
from src.genesis_grid.backend import to_cpu
from src.genesis_grid.defect_tracker import DefectTracker
from src.genesis_grid.pairline_tracker import PairLineTracker
RULES=(rules_alignment.alignment_rule,rules_compression.compression_rule,rules_structural_memory.structural_memory_rule,rules_curvature.curvature_rule)
def one(seed,gain,a):
 np.random.seed(seed); s=GenesisState(a.N,.05); p=make_params(.1); p.template_write_rate=.2; p.template_decay=.02; p.template_restore_gain=gain; d=DefectTracker(); q=PairLineTracker(max_pair_distance=64); avg=np.zeros((a.N,a.N)); ages={}
 for f in range(1,a.frames+1):
  step(s,p,RULES,post=rules_locking.locking_postprocess)
  if f%25: continue
  plus,minus,_=diagnostics.detect_vortices(s); c=np.asarray(to_cpu(s.C)); avg=.95*avg+.05*c; tracks=d.update(f,[(x,y,1) for y,x in plus]+[(x,y,-1) for y,x in minus],C=c,C_avg=avg)
  for z in q.update(frame=f,defect_tracks=tracks,C=c,C_avg=avg): ages[z.id]=max(ages.get(z.id,0),z.age)
 v=list(ages.values()); return {'seed':seed,'persistent':sum(x>=100 for x in v),'long':sum(x>=500 for x in v),'compression':float(np.mean(to_cpu(s.C))),'memory':float(np.mean(np.hypot(to_cpu(s.memory_x),to_cpu(s.memory_y))))}
def main():
 p=argparse.ArgumentParser();p.add_argument('--gains',type=float,nargs='+',default=(0,.1,.3,.6,1));p.add_argument('--N',type=int,default=64);p.add_argument('--frames',type=int,default=2000);p.add_argument('--seeds',type=int,default=3);p.add_argument('--output',type=Path,default=Path('results/v1_structural_memory_screen.json'));a=p.parse_args(); out=[]
 for g in a.gains:
  rs=[one(i,g,a) for i in range(1,a.seeds+1)];m={k:float(np.median([r[k] for r in rs])) for k in rs[0] if k!='seed'};out.append({'gain':g,'runs':rs,'median':m});print(g,m)
 a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps({'claim_boundary':'Regime screen only; no object claim.','conditions':out},indent=2),encoding='utf-8')
if __name__=='__main__':main()
