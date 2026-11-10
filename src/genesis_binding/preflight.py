"""Inspect existing motion archives for a distinct binding-response milestone.

This performs no evolution, new candidate search, predictor fit or gate revision.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

from src.genesis_audit.analysis import winding
from src.genesis_audit.verify import ROOT, verify
from src.genesis_motion.observations import delta


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(source, output):
    if output.exists():
        raise ValueError('Refusing to overwrite a preparation record.')
    inherited = verify(ROOT/'results/v1_baseline_audit_2026-10-31/manifest.json')
    if not inherited['fingerprints_match'] or not inherited['environment_matches']:
        raise ValueError('Review the explicit baseline delta before proceeding.')
    protocol = json.loads((source/'protocol.json').read_text())
    config = protocol['config']
    seeds = config['train']+config['test']+config['replication']
    hashes = {name:sha(source/name) for name in ('protocol.json','report.json')}
    rows = []
    for seed in seeds:
        name = f'seed_{seed}.npz'
        path = source/name
        if not path.exists():
            rows.append(dict(seed=seed,archive_present=False));continue
        hashes[name] = sha(path)
        with np.load(path) as data:
            fields = {key:data[f'initial_{key}'] for key in ('theta','tau','ux','uy','C')}
            n = len(fields['theta'])
            finite = all(a.shape==(n,n) and np.isfinite(a).all() for a in fields.values())
            if not finite:raise ValueError(f'Invalid initial fields in {name}')
            positions = data['untouched_positions']
            pair = positions[0]
            charge = winding(fields['theta'])
            actual_charges = [int(charge[int(y)%n,int(x)%n]) for x,y in pair]
            if actual_charges != [1,-1]:raise ValueError(f'Initial pair charge mismatch: {name}')
            separation = float(np.linalg.norm(delta(pair[1],pair[0],n)))
            centers = np.argwhere(charge!=0)[:,::-1].astype(float)+.5
            other = centers[np.all(np.linalg.norm(delta(centers[:,None,:],pair[None,:,:],n),axis=2)>1e-8,axis=1)]
            external = [float(np.linalg.norm(delta(other,p,n),axis=1).min()) if len(other) else None for p in pair]
            jointly_observed = np.isfinite(positions).all(axis=(1,2))
            missing = np.flatnonzero(~jointly_observed)
            length = int(missing[0]) if len(missing) else len(positions)
            prefix = positions[:length]
            distances = np.linalg.norm(delta(prefix[:,1,:],prefix[:,0,:],n),axis=1)
            movement = np.linalg.norm(delta(prefix,pair,n),axis=2)
            # Preparation criterion uses only initial geometry, never later motion.
            clearance = separation>=8 and all(d is None or d>4 for d in external)
            rows.append(dict(seed=seed,archive_present=True,n=n,initial_charges=actual_charges,
                initial_pair=pair.tolist(),initial_separation=separation,
                total_vortex_plaquettes=int(np.count_nonzero(charge)),nearest_other_defect_distances=external,
                initial_clearance_for_radius3_relocation_calibration=bool(clearance),
                contiguous_joint_samples=length,contiguous_joint_updates=(length-1)*config['interval'],
                maximum_grid_displacement_in_contiguous_prefix=float(movement.max()),
                separation_range_in_contiguous_prefix=[float(distances.min()),float(distances.max())],
                both_original_identities_observed_at_end=bool(jointly_observed[-1])))
    present = [r for r in rows if r['archive_present']]
    clearance = [r['seed'] for r in present if r['initial_clearance_for_radius3_relocation_calibration']]
    summary = dict(archives_present=len(present),full_state_and_initial_charge_checks_pass=True,
        seeds_with_initial_calibration_clearance=clearance,
        first_calibration_seed_by_initial_geometry=min(clearance) if clearance else None,
        original_pairs_with_no_grid_motion_before_first_joint_loss=sum(r['maximum_grid_displacement_in_contiguous_prefix']==0 for r in present),
        original_pairs_observed_at_end=sum(r['both_original_identities_observed_at_end'] for r in present))
    result = dict(milestone='binding_response_preparation',status='preflight_complete_not_a_binding_result',
        purpose='Inspect existing full-state snapshots and controls; no trajectories generated and no prior gates changed.',
        baseline_verification=inherited,source_directory=source.relative_to(ROOT).as_posix(),
        source_sha256=hashes,preflight_source_sha256=sha(Path(__file__)),summary=summary,records=rows,
        limitations=['Grid-level persistence does not establish binding or restoring response.',
            'Tracker loss does not establish annihilation.',
            'Old candidates inhabit populated fields; background pinning must be distinguished from pair cohesion.',
            'Initial clearance is a geometric prerequisite for calibration, not a scientific object criterion.',
            'Old cohorts are for method development only; confirmatory seed design and acceptance thresholds remain to be frozen before any new response collection.'])
    output.mkdir(parents=True)
    (output/'report.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(summary,indent=2))
    return result


if __name__=='__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',type=Path,default=ROOT/'results/vortex_motion_2026-10-31')
    parser.add_argument('--output',type=Path,required=True)
    args = parser.parse_args()
    run(args.source.resolve(),args.output.resolve())
