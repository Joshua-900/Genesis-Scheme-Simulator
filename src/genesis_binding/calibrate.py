"""Frozen, no-evolution relocation calibration on two archived V1 states."""
from __future__ import annotations

import argparse
from dataclasses import asdict
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

import numpy as np

from src.genesis_audit.verify import ROOT, verify
from .relocation import FIELDS, Relocation, arms, inspect, relocate


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path,value):path.write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')


def run(output):
    if output.exists():raise ValueError('Refusing to overwrite a calibration.')
    preflight_path = ROOT/'results/binding_preflight_2026-11-01/report.json'
    preflight = json.loads(preflight_path.read_text())
    source = ROOT/preflight['source_directory']
    for name,digest in preflight['source_sha256'].items():
        if sha(source/name)!=digest:raise ValueError(f'Changed inherited input: {name}')
    inherited = verify(ROOT/'results/v1_baseline_audit_2026-10-31/manifest.json')
    if not inherited['fingerprints_match'] or not inherited['environment_matches']:
        raise ValueError('Baseline source/evidence or numerical environment changed.')
    config = Relocation()
    seeds = preflight['summary']['seeds_with_initial_calibration_clearance']
    if seeds!=[1005,3001]:raise ValueError('This fixed calibration expects the two recorded clearance cases.')
    sources = [Path(__file__),Path(__file__).with_name('relocation.py'),ROOT/'tests/test_binding_relocation.py']
    output.mkdir(parents=True)
    protocol = dict(stage='B: intervention calibration only',created_utc=datetime.now(timezone.utc).isoformat(),
        config=asdict(config),seeds=seeds,baseline_verification=inherited,
        preflight_sha256=sha(preflight_path),archive_sha256={f'seed_{s}.npz':sha(source/f'seed_{s}.npz') for s in seeds},
        source_sha256={p.relative_to(ROOT).as_posix():sha(p) for p in sources},
        map='F(x)=x+sum_i a_i*w(periodic_distance(x,p_i)). w=1 inside radius1; cosine taper to0 at radius3. Disjoint supports. Invert by fixed-point iteration.',
        interpolation='Periodic bilinear sampling of exp(i theta), angle recovered by arg; bilinear sampling of tau, ux, uy, C. Stored vector components are transported in the lab frame, not transformed as a geometric tensor.',
        arms='Sham, relative stretch/compress, common translation along +/- dominant Cartesian pair axis. Every nonsham constituent moves exactly one cell. Opposing arms move two cells in relative axial coordinate. No evolution.',
        identity='Expected winding map moves only the selected +1/-1 plaquettes. Compare entire map exactly; instantiate a fresh tracker and assign slots at validated target locations. No old tracker IDs silently carried across.',
        error_budget='Declared numerical ceilings, not binding criteria: exact outside-support/sham; protected core corners and inverse residual <=1e-10; phasor norm>=0.2; support roundtrip phasor RMS<=0.35, tau/u relativeL2<=0.25, C relativeL2<=0.50.',
        acceptance='Every arm on both fixed archived states must satisfy every declared numerical criterion and arm geometry checks. No tolerances changed after calibration. A failure is an intervention limitation, not evidence against binding.',
        limits=['Only radius3 neighborhoods are transported; extended structural wakes outside remain unchanged.',
            'Roundtrip resampling error is an artifact diagnostic, not a conserved energy or physical displacement.',
            'C is transported as stored state; no new consistency projection is applied. The unchanged engine would overwrite it on evolution.',
            'No trajectories, restoring responses or fresh-seed confirmations are collected.',
            'A calibrated operation is not proof that pinning and binding can be distinguished; Stage C still needs its own frozen design.'])
    write(output/'protocol.json',protocol)  # Persist all choices before evaluating cases.
    records = []
    for seed in seeds:
        with np.load(source/f'seed_{seed}.npz') as data:
            state = {k:data[f'initial_{k}'].copy() for k in FIELDS}
            pair = data['untouched_positions'][0].copy()
        for name,shifts in arms(pair,len(state['theta']),config).items():
            out,back,info = relocate(state,pair,shifts,config)
            result = inspect(state,out,back,pair,shifts,info,config)
            if name=='sham':
                geometry_ok = all(np.array_equal(state[k],out[k]) for k in FIELDS)
            elif name=='stretch':
                geometry_ok = result['relocated_separation']>result['initial_separation'] and np.linalg.norm(result['center_displacement'])<1e-10
            elif name=='compress':
                geometry_ok = result['relocated_separation']<result['initial_separation'] and np.linalg.norm(result['center_displacement'])<1e-10
            else:
                geometry_ok = abs(result['relocated_separation']-result['initial_separation'])<1e-10 and abs(np.linalg.norm(result['center_displacement'])-1)<1e-10
            magnitudes_ok = name=='sham' or np.allclose(result['constituent_displacement_magnitudes'],1,atol=1e-10,rtol=0)
            result['tests']['arm_geometry_correct'] = bool(geometry_ok and magnitudes_ok)
            result['passes'] = all(result['tests'].values())
            result.update(seed=seed,arm=name,source_pair=pair.tolist(),shifts=shifts.tolist())
            records.append(result)
            np.savez_compressed(output/f'seed{seed}_{name}.npz',**{f'{prefix}_{k}':values[k] for prefix,values in (('source',state),('relocated',out),('roundtrip',back)) for k in FIELDS},
                pair=pair,shifts=shifts,support=info['active'])
            failures = [key for key,value in result['tests'].items() if not value]
            print(f'seed{seed} {name}: '+('PASS' if result['passes'] else 'FAIL '+','.join(failures)),flush=True)
    inherited_after = verify(ROOT/'results/v1_baseline_audit_2026-10-31/manifest.json')
    for name,digest in preflight['source_sha256'].items():
        if sha(source/name)!=digest:raise RuntimeError(f'Inherited input changed during calibration: {name}')
    for name,digest in protocol['source_sha256'].items():
        if sha(ROOT/name)!=digest:raise RuntimeError(f'Calibration producer changed during collection: {name}')
    if not inherited_after['fingerprints_match']:raise RuntimeError('Preserved baseline changed.')
    passes = all(r['passes'] for r in records)
    report = dict(stage='B: no-evolution relocation calibration',all_cases_pass=passes,
        case_count=len(records),passed_case_count=sum(r['passes'] for r in records),
        decision='Intervention numerically calibrated within declared bounds; Stage C design remains outstanding.' if passes else 'Intervention not calibrated under declared bounds; stop before response study. This is not a binding result.',
        records=records,baseline_unchanged=True,inherited_inputs_unchanged=True,
        protocol_sha256=sha(output/'protocol.json'))
    write(output/'report.json',report)
    print(report['decision'],flush=True)
    return report


if __name__=='__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    args = parser.parse_args();run(args.output.resolve())
