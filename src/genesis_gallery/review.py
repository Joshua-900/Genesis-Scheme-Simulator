"""Bounded visual review of existing generator configurations; no physics gates.

python -B -m src.genesis_gallery.review --output results/generative_review_new
"""

from __future__ import annotations

import argparse
import copy
from datetime import datetime,timezone
import hashlib
from pathlib import Path

import numpy as np

from genesis_multiscale_audit import ROOT,engine_hashes,write_json
from genesis_v2_integrated_coupling_dose_response import params_for_gain
from src.genesis_audit.analysis import winding
from src.genesis_audit.verify import verify
from src.genesis_audit.v1_adapter import V1Adapter
from src.genesis_v2_integrated import IntegratedState,step as integrated_step
from . import legacy


LABELS={'alignment':'Alignment only','v1':'V1 structural','v1_no_geometry':'V1 without geometry',
    'legacy_full':'Historical full recipe','legacy_no_geometry':'Historical texture rules','v2_integrated':'V2 bridge, gain 0.20'}
ORDER=tuple(LABELS)


def create(name,n,seed,theta):
    if name.startswith('legacy'):
        state={k:np.zeros((n,n)) for k in ('tau','ux','uy','C')};state['theta']=theta.copy()
        params=legacy.defaults()
        if name=='legacy_no_geometry':params.update(kappa0=0.,curv0=0.,shell_geom_gain=0.)
        return state,params
    if name=='v2_integrated':
        previous=np.random.get_state()
        try:state=IntegratedState(n,dt=.05,seed=seed)
        finally:np.random.set_state(previous)
        state.theta=theta.copy()
        return state,params_for_gain(.20)
    adapter=V1Adapter('alignment_only' if name=='alignment' else 'geometry_ablation' if name=='v1_no_geometry' else 'v1')
    if name=='v1_no_geometry':adapter.params.curv=0.
    state=adapter.create(n,seed);state.theta=theta.copy()
    return state,adapter


def advance(name,state,params,count):
    for _ in range(count):
        if name.startswith('legacy'):legacy.step(state,params)
        elif name=='v2_integrated':integrated_step(state,params)
        else:params.advance(state,1)


def fields(state):
    return {k:np.asarray(state[k] if isinstance(state,dict) else getattr(state,k)).copy() for k in ('theta','tau','ux','uy','C')}


def theta_of(state):return state['theta'] if isinstance(state,dict) else state.theta


def metrics(theta,previous):
    phasor=np.exp(1j*theta)
    roughness=float(.5*np.mean(1-np.cos(np.roll(theta,-1,0)-theta))+.5*np.mean(1-np.cos(np.roll(theta,-1,1)-theta)))
    out={'bond_disagreement':roughness,'vortex_plaquettes':int(np.count_nonzero(winding(theta))),
        'global_coherence':float(np.abs(phasor.mean())),'fourfold_concentration':float(np.abs(np.exp(4j*theta).mean()))}
    if previous is None:out.update(raw_interval_change=0.,phase_aligned_interval_change=0.)
    else:
        before=np.exp(1j*previous)
        rotation=np.angle(np.mean(phasor*np.conj(before)))
        out.update(raw_interval_change=float(np.sqrt(np.mean(np.abs(phasor-before)**2))),
            phase_aligned_interval_change=float(np.sqrt(np.mean(np.abs(phasor*np.exp(-1j*rotation)-before)**2))))
    return out


def poke(state):
    theta=theta_of(state);n=len(theta)
    y,x=np.indices(theta.shape);r=np.sqrt((x-n/2)**2+(y-n/2)**2)
    weight=np.where(r<=5,.5*(1+np.cos(np.pi*r/5)),0.)
    changed=(theta+np.pi/2*weight)%(2*np.pi)
    if isinstance(state,dict):state['theta']=changed
    else:state.theta=changed


def run(output,n=64,seeds=(1,7,42),updates=8000,interval=100):
    if output.exists():raise ValueError('Refusing to overwrite a review.')
    parent=verify(ROOT/'results/v1_baseline_audit_2026-10-31/manifest.json')
    if not parent['fingerprints_match'] or not parent['environment_matches']:raise ValueError('Review baseline delta first.')
    before=engine_hashes();legacy_sha=hashlib.sha256(legacy.SOURCE.read_bytes()).hexdigest()
    output.mkdir(parents=True)
    parameters={}
    for name in ORDER:
        _,p=create(name,n,seeds[0],np.zeros((n,n)))
        parameters[name]=p if isinstance(p,dict) else vars(p.params) if isinstance(p,V1Adapter) else vars(p)
    write_json(output/'protocol.json',{'purpose':'Generative behavior and controllability review, not a physics/object/prediction gate or global novelty proof.',
        'created_utc':datetime.now(timezone.utc).isoformat(),'N':n,'seeds':seeds,'updates':updates,'interval':interval,'models':LABELS,
        'parameters':parameters,'engine_source_sha256_before':before,'legacy_source_sha256':legacy_sha,
        'review_source_sha256':{p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in (ROOT/'src/genesis_gallery').glob('*.py')},
        'initialization':'Identical theta from local default_rng(seed) in every lane. V1/legacy structural fields start zero. V2 has its native seeded extra source fields; cross-version comparison is not a single-mechanism causal test.',
        'controls':'V1 no-geometry disables kappa, shell and curvature; tension/turning and rest of preset retained. Legacy texture control disables only kappa, shell and curvature, retaining explicit phase/dipole/triad rules and locking coefficients.',
        'legacy':'Vectorized headless evaluation of actual genesis_fields_pretty.py rules, checked against the AST-extracted original function. Original mixed boundaries and stage timing retained. Floating summation order differs; no bitwise historical trajectory replay is claimed.',
        'pulse':'At update4000 clone each lane, apply pi/2 compact radius5 angular pulse, and evolve400 updates; compare with unforced trajectory at4400. No extra driving during baseline run.',
        'rendering':'Same cyclic palette and fixed angle range, nearest pixel rendering, no inferred boundaries. First seed supplies animation; all seeds supply contact sheets and metrics.',
        'metrics':'Descriptive only. Phase-aligned interval change removes best global phase rotation; high raw color change alone is not ongoing spatial novelty. Bond roughness/coherence/fourfold concentration/vortex plaquettes have no synthetic interestingness score.',
        'limits':['Three seeds and fixed configurations, no sweep or post-review tuning.','Equal update counts do not match physical time or effective relaxation speed across engines.',
            'Visual difference is not proof of uniqueness among known generative systems.','Four preferred angles and directional triad templates are explicitly supplied to the legacy recipe.',
            'Long-lived static textures can be useful generators even if they lack autonomous moving objects.','Existing scientific negative results are retained but are not a verdict on generative usefulness.']})
    records=[]
    for seed in seeds:
        initial=np.random.default_rng(seed).uniform(0,2*np.pi,(n,n))
        for name in ORDER:
            state,p=create(name,n,seed,initial)
            phases=[];compression=[];observations=[];previous=None;pulsed=None
            for tick in range(0,updates+1,interval):
                if tick:advance(name,state,p,interval)
                snapshot=fields(state);theta=snapshot['theta']
                if not all(np.isfinite(a).all() for a in snapshot.values()):raise RuntimeError(f'Nonfinite field in {name}')
                phases.append(theta.astype(np.float32));compression.append(snapshot['C'].astype(np.float32))
                observations.append({'update':tick,**metrics(theta,previous)});previous=theta
                if tick==4000:
                    pulsed=copy.deepcopy(state);poke(pulsed);advance(name,pulsed,p,400)
                if tick==4400:
                    pulse_fields=fields(pulsed)
                    pulse_delta=float(np.sqrt(np.mean(np.abs(np.exp(1j*pulse_fields['theta'])-np.exp(1j*theta))**2)))
                    pulse_control=theta.astype(np.float32)
                    pulse_theta=pulse_fields['theta'].astype(np.float32)
            np.savez_compressed(output/f'{name}_seed{seed}.npz',theta=np.asarray(phases),C=np.asarray(compression),
                pulse_control_theta=pulse_control,pulse_theta=pulse_theta,updates=np.arange(0,updates+1,interval))
            late=[r for r in observations if r['update']>=4000]
            result={'seed':seed,'model':name,'records':observations,'final':observations[-1],
                'late_mean_phase_aligned_change':float(np.mean([r['phase_aligned_interval_change'] for r in late])),
                'pulse_rms_phasor_difference_at400_updates':pulse_delta}
            records.append(result)
            write_json(output/'progress.json',{'completed':[{k:r[k] for k in ('seed','model')} for r in records]})
            print(f"{name} seed={seed}: late change={result['late_mean_phase_aligned_change']:.4g}; roughness={result['final']['bond_disagreement']:.4g}",flush=True)
    if before!=engine_hashes() or legacy_sha!=hashlib.sha256(legacy.SOURCE.read_bytes()).hexdigest():raise RuntimeError('Preserved source changed.')
    report={'records':records,'engines_and_legacy_unchanged':True,'engine_source_sha256_after':engine_hashes(),
        'claim_boundary':'Fixed-recipe descriptive generative review; human assessment of usefulness, no global novelty or physics claim.'}
    write_json(output/'report.json',report)
    print(f'Completed {output}',flush=True)


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();run(args.output)


if __name__=='__main__':main()
