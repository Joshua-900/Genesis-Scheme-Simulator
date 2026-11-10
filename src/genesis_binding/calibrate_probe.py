"""Fixed two-level temporary-probe calibration; no binding inference."""
from __future__ import annotations

import argparse
import copy
from dataclasses import asdict
from datetime import datetime,timezone
import json
from pathlib import Path

import numpy as np

from src.genesis_audit.analysis import winding
from src.genesis_audit.v1_adapter import FIELDS,V1Adapter
from src.genesis_audit.verify import ROOT,verify
from src.genesis_motion.observations import PeriodicTracker,delta
from .calibrate import sha,write
from .dynamic_probe import AngularProbe,ProbeConfig,step_with_probe
from .relocation import Relocation,arms


def observe(state,tracker,selected,tick):
    positions=np.full((2,2),np.nan)
    for index,identity in enumerate(selected):
        t=tracker.tracks.get(identity)
        if t is not None:positions[index]=[t.x,t.y]
    charge=winding(state.theta)
    return positions,int(np.count_nonzero(charge)),sum(t.birth==tick for t in tracker.tracks.values()) if tick else 0


def collect(adapter,initial,pair,probe):
    state=copy.deepcopy(initial)
    config=probe.config
    tracker=PeriodicTracker(state.N)
    tracker.update(state.theta,0)
    selected=[]
    for p,sign in zip(pair,(1,-1)):
        matches=[t.id for t in tracker.tracks.values() if t.charge==sign and np.linalg.norm(delta([t.x,t.y],p,state.N))<1e-12]
        if len(matches)!=1:raise ValueError('Initial slot assignment is not unique.')
        selected.append(matches[0])
    positions=[];counts=[];births=[];external=[];activities=[];snapshots=[]
    finite=True;release_exact=True
    for tick in range(config.duration+config.follow+1):
        if tick:
            before=adapter.snapshot(state)
            if tick==config.duration+1:
                reference=copy.deepcopy(state);adapter.advance(reference,1)
            external.append(step_with_probe(adapter,state,probe,tick-1))
            if tick==config.duration+1:
                release_exact=all(np.array_equal(getattr(state,k),getattr(reference,k)) for k in FIELDS)
            tracker.update(state.theta,tick)
            current=adapter.snapshot(state)
            finite=finite and all(np.isfinite(a).all() for a in current.values())
            if not finite:raise RuntimeError('Nonfinite field during fixed probe calibration.')
            activities.append({k:float(np.sqrt(np.mean(np.abs(np.exp(1j*current[k])-np.exp(1j*before[k]))**2)))
                               if k=='theta' else float(np.sqrt(np.mean((current[k]-before[k])**2))) for k in FIELDS})
        position,count,birth=observe(state,tracker,selected,tick)
        positions.append(position);counts.append(count);births.append(birth)
        if tick%config.interval==0:snapshots.append(adapter.snapshot(state))
        if tick==config.duration:release_state=adapter.snapshot(state)
    return dict(positions=np.array(positions),counts=np.array(counts),births=np.array(births),
        external=external,activities=activities,snapshots=snapshots,
        initial_state=adapter.snapshot(initial),release_state=release_state,final_state=adapter.snapshot(state),
        finite=finite,release_exact=release_exact,
        post_cutoff_external_exact_zero=all(r['peak_external_angle_increment']==0 and r['external_angle_increment_l1']==0 for r in external[config.duration:]))


def assess(case,reference,probe,name):
    c=probe.config;t=c.duration;n=probe.n
    during=case['positions'][:t+1]
    survivors=bool(np.isfinite(during).all())
    direction_projection=None;separation_change=None;relative_movement=None
    measured=False
    if survivors and np.isfinite(reference['positions'][t]).all():
        movement=delta(case['positions'][t],reference['positions'][t],n)
        projection=np.sum(movement*probe.directions,axis=1)
        direction_projection=projection.tolist()
        separation_change=float(np.linalg.norm(delta(case['positions'][t,1],case['positions'][t,0],n))-
                                np.linalg.norm(delta(reference['positions'][t,1],reference['positions'][t,0],n)))
        relative_movement=float(np.linalg.norm(movement[1]-movement[0]))
        mode_correct=(separation_change>=c.minimum_axial_movement if name=='stretch' else
                      -separation_change>=c.minimum_axial_movement if name=='compress' else
                      relative_movement<=c.maximum_translation_relative_error)
        measured=bool(np.all(projection>=c.minimum_axial_movement) and mode_correct)
    extra_count=int(np.maximum(case['counts'][:t+1]-reference['counts'][:t+1],0).max())
    births=int(case['births'][1:t+1].sum());reference_births=int(reference['births'][1:t+1].sum())
    peak=max(r['peak_external_angle_increment'] for r in case['external'])
    safety=dict(selected_identities_observed_through_pulse=survivors,
        no_excess_vortex_count_during_pulse=extra_count==0,
        no_excess_tracked_births_during_pulse=births<=reference_births,
        finite_fields=bool(case['finite']),native_release_exact=bool(case['release_exact']),
        post_cutoff_input_exact_zero=bool(case['post_cutoff_external_exact_zero']),
        bounded_external_angle_increment=peak<=probe.speed*c.directional_gradient_cap+c.numerical_tolerance)
    return dict(safety_pass=all(safety.values()),safety=safety,
        movement_resolved=measured,calibrated=bool(all(safety.values()) and measured),
        axial_movement_at_release=direction_projection,separation_change_at_release=separation_change,
        differential_movement_norm_at_release=relative_movement,
        peak_external_angle_increment=peak,
        external_angle_increment_l1_total=sum(r['external_angle_increment_l1'] for r in case['external']),
        maximum_excess_vortex_count=extra_count,tracked_births_during_pulse=births,reference_tracked_births=reference_births,
        selected_identities_observed_at_followup=bool(np.isfinite(case['positions'][-1]).all()))


def save_case(path,case):
    np.savez_compressed(path,positions=case['positions'],vortex_counts=case['counts'],tracked_births=case['births'],
        external_peak=np.array([r['peak_external_angle_increment'] for r in case['external']]),
        external_l1=np.array([r['external_angle_increment_l1'] for r in case['external']]),
        **{f'activity_{k}':np.array([r[k] for r in case['activities']]) for k in FIELDS},
        **{f'{prefix}_{k}':values[k] for prefix,values in (('initial',case['initial_state']),('release',case['release_state']),('final',case['final_state'])) for k in FIELDS},
        **{f'frames_{k}':np.array([s[k] for s in case['snapshots']],dtype=np.float32) for k in FIELDS})


def run(output):
    if output.exists():raise ValueError('Refusing to overwrite a probe calibration.')
    parent=ROOT/'results/binding_calibration_2026-11-01'
    manifest=json.loads((parent/'manifest.json').read_text())
    for name,digest in manifest['artifacts'].items():
        if sha(parent/name)!=digest:raise ValueError(f'Changed inherited calibration artifact: {name}')
    inherited=verify(ROOT/'results/v1_baseline_audit_2026-10-31/manifest.json')
    if not inherited['fingerprints_match'] or not inherited['environment_matches']:raise ValueError('Inherited baseline differs.')
    preflight_path=ROOT/'results/binding_preflight_2026-11-01/report.json'
    preflight=json.loads(preflight_path.read_text())
    source=ROOT/preflight['source_directory']
    for name,digest in preflight['source_sha256'].items():
        if sha(source/name)!=digest:raise ValueError(f'Changed archive: {name}')
    config=ProbeConfig();seeds=(1005,3001);adapter=V1Adapter()
    sources=[Path(__file__),Path(__file__).with_name('dynamic_probe.py'),Path(__file__).with_name('relocation.py'),
             Path(__file__).with_name('calibrate.py'),ROOT/'tests/test_dynamic_probe.py']
    output.mkdir(parents=True)
    protocol=dict(stage='B2: distinct temporary dynamic probe calibration',created_utc=datetime.now(timezone.utc).isoformat(),
        config=asdict(config),seeds=seeds,baseline_verification=inherited,parameters=vars(adapter.params),
        previous_calibration_manifest_sha256=sha(parent/'manifest.json'),preflight_sha256=sha(preflight_path),
        source_sha256={p.relative_to(ROOT).as_posix():sha(p) for p in sources},
        archive_sha256={f'seed_{s}.npz':sha(source/f'seed_{s}.npz') for s in seeds},
        intervention='Temporary torque -speed/dt * sin^2(pi*(index+0.5)/80) * sum_i cosine_disk_i * clip(direction_i dot wrapped_centered_gradient(theta),-1,1). Native locking applies without compensation. Fixed disk centers; no pursuit of moving cores. No field resampling.',
        arms='Untouched reference per seed; stretch, compress, common +/- dominant Cartesian pair axis at each of two speeds. Radius3 nonoverlapping disks. Same nominal amplitude/envelope, not equal realized motion or actual torque exposure.',
        durations='80 forced updates, then80 unchanged native updates. First release step must equal a native step from the identical perturbed state bitwise. Input exactly zero throughout release.',
        safety='At every forced update: original selected tracker identities observed, no excess vortex census or cumulative tracked births over reference, finite fields, external angle increment bounded by speed, release cutoff exact. Birth/identity checks are conservative tracker observations, not exact physical particle events.',
        effectiveness='At pulse end both cores move >=0.5 cell projected along their own input direction relative to the untouched arm. Stretch/compress separation differs with requested sign by >=0.5 cell. Common translations have differential movement <=1 cell. This is manipulation resolution, not evidence of binding.',
        dose_policy='Two levels fixed in advance (0.05,0.10). A level calibrates only if all four modes on both archived states pass safety and effectiveness. Choose the lowest passing level, or none. No escalation beyond these levels or tuning after outcomes.',
        limits=['Method development on old states, not fresh-seed confirmation or a bound-object result.',
            'The externally imposed transport-like torque does not prove autonomous motion or constitute a new fuel budget.',
            'Local structure evolves naturally; earlier structural imprints are not guaranteed to follow a driven defect.',
            'Dense surroundings and individual pinning remain confounds for any later scientific interpretation.',
            'No structural-feedback ablation or confirmatory response study is collected here.',
            'Topology/positions/activity are recorded each update; full-field frames are float32 every5 updates, with float64 initial/release/final snapshots.'])
    write(output/'protocol.json',protocol)
    records=[];reference_checks=[]
    for seed in seeds:
        initial=adapter.create(64,seed)
        with np.load(source/f'seed_{seed}.npz') as data:
            for key in FIELDS:setattr(initial,key,data[f'initial_{key}'].copy())
            pair=data['untouched_positions'][0].copy()
            historical_positions=data['untouched_positions'][:(config.duration+config.follow)//config.interval+1].copy()
        directions=arms(pair,64,Relocation())
        reference_probe=AngularProbe(64,pair,directions['sham'],0.,config)
        reference=collect(adapter,initial,pair,reference_probe)
        replay_exact=bool(np.array_equal(reference['positions'][::config.interval],historical_positions,equal_nan=True))
        if not replay_exact:raise RuntimeError('Untouched position replay differs from inherited archive.')
        reference_checks.append(dict(seed=seed,archived_positions_replay_exact=True,native_release_exact=reference['release_exact']))
        save_case(output/f'seed{seed}_reference.npz',reference)
        print(f'seed{seed} reference: archived positions match',flush=True)
        for speed in config.speeds:
            for name,inputs in directions.items():
                if name=='sham':continue
                probe=AngularProbe(64,pair,inputs,speed,config)
                case=collect(adapter,initial,pair,probe)
                result=assess(case,reference,probe,name)
                filename=f'seed{seed}_v{round(1000*speed):04d}_{name}.npz'
                save_case(output/filename,case)
                result.update(seed=seed,speed=speed,arm=name,file=filename,source_pair=pair.tolist(),directions=inputs.tolist())
                records.append(result)
                print(f'seed{seed} speed={speed} {name}: safety={result["safety_pass"]}; movement={result["movement_resolved"]}; axial={result["axial_movement_at_release"]}',flush=True)
    levels={str(speed):all(r['calibrated'] for r in records if r['speed']==speed) for speed in config.speeds}
    selected=next((speed for speed in config.speeds if levels[str(speed)]),None)
    for name,digest in protocol['source_sha256'].items():
        if sha(ROOT/name)!=digest:raise RuntimeError('Producer changed during collection.')
    for name,digest in preflight['source_sha256'].items():
        if sha(source/name)!=digest:raise RuntimeError('Inherited archive changed during collection.')
    after=verify(ROOT/'results/v1_baseline_audit_2026-10-31/manifest.json')
    if not after['fingerprints_match'] or not after['environment_matches']:raise RuntimeError('Inherited baseline changed.')
    report=dict(stage=protocol['stage'],case_count=len(records),reference_checks=reference_checks,
        levels_calibrated=levels,selected_speed=selected,
        safety_pass_count=sum(r['safety_pass'] for r in records),movement_resolved_count=sum(r['movement_resolved'] for r in records),
        decision='A fixed input level resolves the intended displacement safely on these old states; no binding inference.' if selected is not None else 'Neither fixed input level calibrates every mode on both states. No binding inference or dose escalation.',
        records=records,baseline_and_inherited_inputs_unchanged=True,protocol_sha256=sha(output/'protocol.json'))
    write(output/'report.json',report);print(report['decision'],flush=True)
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    run(parser.parse_args().output.resolve())
