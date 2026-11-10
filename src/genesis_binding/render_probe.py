"""Descriptive views of the fixed probe calibration; no extra response gate."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

from src.genesis_motion.observations import delta

COLORS={'stretch':'#ae414b','compress':'#326da1','translate_plus':'#698c58','translate_minus':'#a07138'}


def analyze(directory,report):
    records=[];comparisons=[]
    for seed in (1005,3001):
        for speed in (.05,.1):
            rows={r['arm']:r for r in report['records'] if r['seed']==seed and r['speed']==speed}
            data={name:np.load(directory/r['file']) for name,r in rows.items()}
            for name,d in data.items():
                displacement=delta(d['positions'][80:],d['positions'][80],64)
                theta=d['frames_theta'][16:].astype(float)
                a,b=np.exp(1j*theta[:-1]),np.exp(1j*theta[1:])
                rotation=np.angle(np.mean(b*np.conj(a),axis=(1,2)))
                aligned=np.sqrt(np.mean(np.abs(b*np.exp(-1j*rotation[:,None,None])-a)**2,axis=(1,2)))
                records.append(dict(seed=seed,speed=speed,arm=name,
                    maximum_post_cutoff_grid_displacement=float(np.nanmax(np.linalg.norm(displacement,axis=2))),
                    phase_aligned_post_cutoff_theta_change_mean_per5_updates=float(aligned.mean()),
                    global_mean_post_cutoff_activity={k:float(d[f'activity_{k}'][80:].mean()) for k in ('theta','tau','ux','uy','C')}))
            for slot,a,b in ((0,'stretch','translate_minus'),(0,'compress','translate_plus'),
                             (1,'stretch','translate_plus'),(1,'compress','translate_minus')):
                difference=delta(data[a]['positions'][:,slot],data[b]['positions'][:,slot],64)
                comparisons.append(dict(seed=seed,speed=speed,slot=slot,arms=[a,b],own_nominal_direction_unchanged=True,
                    maximum_tracked_trajectory_difference=float(np.nanmax(np.linalg.norm(difference,axis=1)))))
            for d in data.values():d.close()
    result=dict(purpose='Post-collection descriptive summary; does not modify frozen calibration acceptance or establish a general interaction law.',
        limitations=['Only two old development states and two nominal probe levels.',
            'Positions have one-plaquette resolution; sub-grid or longer-time coupling is unresolved.',
            'Own input prescription is held fixed, not necessarily actual delivered torque exposure.',
            'Per-update theta activity is raw phasor change and includes global rotation; the separate aligned five-update descriptor removes best common phase rotation from saved float32 frames.',
            'Activity is a global field mean and does not identify internal activity of a particular object.'],
        release_observations=records,partner_input_comparisons=comparisons)
    (directory/'descriptive_release.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')


def render(directory):
    report=json.loads((directory/'report.json').read_text())
    analyze(directory,report)
    fig,axes=plt.subplots(2,2,figsize=(12,7),layout='constrained',sharex=True)
    for row,seed in enumerate((1005,3001)):
        with np.load(directory/f'seed{seed}_reference.npz') as d:
            base=d['positions'].copy()
        base_separation=np.linalg.norm(delta(base[:,1],base[:,0],64),axis=1)
        for col,speed in enumerate((.05,.1)):
            ax=axes[row,col]
            for r in report['records']:
                if r['seed']!=seed or r['speed']!=speed:continue
                with np.load(directory/r['file']) as d:
                    pos=d['positions']
                    difference=np.linalg.norm(delta(pos[:,1],pos[:,0],64),axis=1)-base_separation
                ax.plot(np.arange(len(difference)),difference,label=r['arm'].replace('_',' '),color=COLORS[r['arm']],
                        linestyle='--' if r['arm'].startswith('translate') else '-')
            ax.axvspan(0,80,color='#eeeeee');ax.axvline(80,color='black',linestyle=':',linewidth=1)
            ax.axhline(0,color='#777777',linewidth=.6);ax.grid(alpha=.2)
            ax.set_title(f'Seed {seed} · nominal input {speed}')
            ax.set_ylabel('Separation change vs untouched (cells)')
            ax.set_xlabel('Updates since probe start')
    axes[0,0].legend(fontsize=8,loc='upper left')
    fig.suptitle('Temporary probe and release · input off at update 80\nNo grid-resolved recoil during the following 80 updates; calibration states only',fontsize=14)
    fig.savefig(directory/'probe_release.png',dpi=130);plt.close(fig)

    fig,axes=plt.subplots(1,3,figsize=(13,4),layout='constrained')
    for ax,key,title in zip(axes,('theta','ux','C'),('Orientation θ (raw phasor)','Displacement ux component','Compression C')):
        with np.load(directory/'seed1005_reference.npz') as d:
            activity=d[f'activity_{key}'].copy()
        ax.plot(np.arange(1,len(activity)+1),activity,color='black',linewidth=1.7,label='untouched')
        for r in report['records']:
            if r['seed']!=1005 or r['speed']!=.1:continue
            with np.load(directory/r['file']) as d:activity=d[f'activity_{key}'].copy()
            ax.plot(np.arange(1,len(activity)+1),activity,color=COLORS[r['arm']],alpha=.8,label=r['arm'].replace('_',' '))
        ax.axvline(80,color='black',linestyle=':',linewidth=1)
        ax.set_title(title);ax.set_xlabel('Update');ax.set_ylabel('Global RMS change per update')
        ax.set_yscale('log');ax.grid(alpha=.2)
    axes[0].legend(fontsize=8)
    fig.suptitle('Field values keep evolving after the probe · seed 1005, higher fixed input\nFixed defect positions do not imply a full-state fixed point',fontsize=13)
    fig.savefig(directory/'field_activity.png',dpi=130);plt.close(fig)
    print(f'Rendered descriptive probe plots in {directory}')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('directory',type=Path)
    render(p.parse_args().directory)
