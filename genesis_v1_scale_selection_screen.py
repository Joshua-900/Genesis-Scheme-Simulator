"""Small fixed screen for V1 compression-driven scale selection."""
from __future__ import annotations
import argparse, json
from pathlib import Path
import numpy as np
from genesis_v1_compression_ablation import make_params
from src.genesis_grid import GenesisState, diagnostics, rules_alignment, rules_compression, rules_curvature, rules_locking, step
from src.genesis_grid import rules_scale_selection
from src.genesis_grid.backend import to_cpu
from src.genesis_grid.defect_tracker import DefectTracker
from src.genesis_grid.pairline_tracker import PairLineTracker

RULES=(rules_alignment.alignment_rule,rules_compression.compression_rule,rules_scale_selection.scale_selection_rule,rules_curvature.curvature_rule)

def one(seed,damping,args):
 np.random.seed(seed); s=GenesisState(args.N,.05); p=make_params(.1); p.inhibitor_source=.5; p.inhibitor_decay=.1; p.inhibitor_diffusion=.4; p.inhibitor_tension_damping=damping
 d=DefectTracker(); q=PairLineTracker(max_pair_distance=64); avg=np.zeros((args.N,args.N)); ages={}
 for f in range(1,args.frames+1):
  step(s,p,RULES,post=rules_locking.locking_postprocess)
  if f%25: continue
  plus,minus,_=diagnostics.detect_vortices(s); tracks=d.update(f,[(c,r,1) for r,c in plus]+[(c,r,-1) for r,c in minus],C=np.asarray(to_cpu(s.C)),C_avg=avg)
  avg=.95*avg+.05*np.asarray(to_cpu(s.C))
  for pair in q.update(frame=f,defect_tracks=tracks,C=np.asarray(to_cpu(s.C)),C_avg=avg): ages[pair.id]=max(ages.get(pair.id,0),pair.age)
 a=list(ages.values()); return {'seed':seed,'persistent':sum(x>=100 for x in a),'long':sum(x>=500 for x in a),'compression':float(np.mean(to_cpu(s.C))),'inhibitor':float(np.mean(to_cpu(s.inhibitor)))}

def main():
 p=argparse.ArgumentParser(); p.add_argument('--damping',type=float,nargs='+',default=(0,.25,.5,1,2)); p.add_argument('--N',type=int,default=64); p.add_argument('--frames',type=int,default=2000); p.add_argument('--seeds',type=int,default=3); p.add_argument('--output',type=Path,default=Path('results/v1_scale_selection_screen.json')); a=p.parse_args(); out=[]
 for x in a.damping:
  runs=[one(seed,x,a) for seed in range(1,a.seeds+1)]; med={k:float(np.median([r[k] for r in runs])) for k in runs[0] if k!='seed'}; out.append({'damping':x,'runs':runs,'median':med}); print(x,med)
 a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_text(json.dumps({'claim_boundary':'Regime screen only; no object claim.','conditions':out},indent=2),encoding='utf-8')
if __name__=='__main__': main()
