"""Render saved calibration artifacts; no trajectory evolution or tuning."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np


def render(directory):
    report = json.loads((directory/'report.json').read_text())
    cases = [r for r in report['records'] if r['arm']!='sham']
    fig,axes = plt.subplots(1,3,figsize=(13,4),layout='constrained')
    colors = ['#b25b52' if r['seed']==1005 else '#426e96' for r in cases]
    for ax,key,limit,title in zip(axes,('tau_relative_l2','displacement_relative_l2','C_relative_l2'),
                                (25,25,50),('Tension','Displacement','Compression')):
        ax.bar(range(len(cases)),[100*r['roundtrip_errors'][key] for r in cases],color=colors)
        ax.axhline(limit,color='black',linestyle='--',label=f'Declared limit: {limit}%')
        ax.set_xticks(range(len(cases)),[str(r['seed'])+'\n'+r['arm'].replace('translate_','move ') for r in cases],rotation=60,ha='right',fontsize=8)
        ax.set_title(title);ax.set_ylim(0,60);ax.legend(fontsize=8)
        ax.set_ylabel('Roundtrip relative L2 discrepancy (%)')
        ax.grid(axis='y',alpha=.2)
    fig.suptitle('Relocation calibration · all non-sham cases fail displacement preservation')
    fig.savefig(directory/'error_budget.png',dpi=130);plt.close(fig)

    with np.load(directory/'seed1005_stretch.npz') as data:
        n = len(data['source_theta']);pair = data['pair'];shifts = data['shifts']
        x,y = np.floor(pair[0]).astype(int)
        xs,ys = (x+np.arange(-5,6))%n,(y+np.arange(-5,6))%n
        crop = lambda a:a[np.ix_(ys,xs)]
        fields = {prefix:{k:crop(data[f'{prefix}_{k}']) for k in ('theta','ux','uy','C')} for prefix in ('source','relocated','roundtrip')}
    fig,axes = plt.subplots(3,4,figsize=(12,9),layout='constrained')
    original,back = fields['source'],fields['roundtrip']
    geometry_max = max(float(np.hypot(v['ux'],v['uy']).max()) for v in fields.values())
    for row,label in enumerate(('Orientation θ','Displacement magnitude','Compression C')):
        for col,prefix in enumerate(('source','relocated','roundtrip','error')):
            ax = axes[row,col]
            if prefix=='error':
                value = (np.abs(np.angle(np.exp(1j*(back['theta']-original['theta'])))) if row==0 else
                         np.hypot(back['ux']-original['ux'],back['uy']-original['uy']) if row==1 else np.abs(back['C']-original['C']))
            else:
                v = fields[prefix]
                value = v['theta'] if row==0 else np.hypot(v['ux'],v['uy']) if row==1 else v['C']
            top = (np.pi if prefix=='error' else 2*np.pi) if row==0 else geometry_max if row==1 else 1
            im = ax.imshow(value,origin='lower',extent=(-5.5,5.5,-5.5,5.5),interpolation='nearest',vmin=0,vmax=top,
                           cmap='twilight' if row==0 and prefix!='error' else 'magma')
            if row==0:
                ax.set_title(('Source','Relocated','Mapped back','Roundtrip discrepancy')[col])
            if col==0:ax.set_ylabel(label)
            ax.set_xticks([-4,0,4]);ax.set_yticks([-4,0,4])
            plt.colorbar(im,ax=ax,shrink=.7)
    fig.suptitle('Seed 1005 · stretch arm · first core and surroundings\nNo dynamics advanced; discrepancy comes from the relocation procedure',fontsize=13)
    fig.savefig(directory/'relocation_detail.png',dpi=120);plt.close(fig)
    print(f'Rendered {directory}')


if __name__=='__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory',type=Path)
    render(parser.parse_args().directory)
