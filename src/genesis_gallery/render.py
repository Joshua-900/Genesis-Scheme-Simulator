"""Identical phase rendering for the frozen generative review outputs."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from .review import LABELS, ORDER


def render(directory):
    protocol=json.loads((directory/'protocol.json').read_text())
    report=json.loads((directory/'report.json').read_text())
    seeds=protocol['seeds'];seed=seeds[0]
    data={name:np.load(directory/f'{name}_seed{seed}.npz') for name in ORDER}
    ticks=data[ORDER[0]]['updates']
    chosen=(0,200,2000,8000)
    fig,axes=plt.subplots(4,6,figsize=(17,11),layout='constrained')
    for col,name in enumerate(ORDER):
        for row,tick in enumerate(chosen):
            ax=axes[row,col];index=int(np.flatnonzero(ticks==tick)[0])
            ax.imshow(data[name]['theta'][index],cmap='twilight',vmin=0,vmax=2*np.pi,origin='lower',interpolation='nearest')
            ax.set_xticks([]);ax.set_yticks([])
            if row==0:ax.set_title(LABELS[name],fontsize=11)
            if col==0:ax.set_ylabel(f'Update {tick}',fontsize=11)
    fig.suptitle(f'Genesis generator review · same initial angles · seed {seed}\nColor = orientation θ, fixed cyclic scale; no boundary overlays',fontsize=15)
    fig.savefig(directory/'comparison.png',dpi=120);plt.close(fig)

    fig,axes=plt.subplots(3,6,figsize=(17,8.5),layout='constrained')
    for col,name in enumerate(ORDER):
        for row,tick in enumerate(chosen[1:]):
            index=int(np.flatnonzero(ticks==tick)[0]);ax=axes[row,col]
            ax.imshow(data[name]['C'][index],cmap='magma',vmin=0,vmax=1,origin='lower',interpolation='nearest')
            ax.set_xticks([]);ax.set_yticks([])
            if row==0:ax.set_title(LABELS[name],fontsize=11)
            if col==0:ax.set_ylabel(f'Update {tick}')
    fig.suptitle(f'Compression indicator C · seed {seed} · shared scale 0–1\nA model diagnostic, not a geometric height map',fontsize=15)
    fig.savefig(directory/'compression.png',dpi=120);plt.close(fig)

    fig,axes=plt.subplots(len(seeds),6,figsize=(17,8.5),layout='constrained')
    for row,s in enumerate(seeds):
        for col,name in enumerate(ORDER):
            with np.load(directory/f'{name}_seed{s}.npz') as d:
                axes[row,col].imshow(d['theta'][-1],cmap='twilight',vmin=0,vmax=2*np.pi,origin='lower',interpolation='nearest')
            axes[row,col].set_xticks([]);axes[row,col].set_yticks([])
            if row==0:axes[row,col].set_title(LABELS[name],fontsize=11)
            if col==0:axes[row,col].set_ylabel(f'Seed {s}')
    fig.suptitle('Final textures at update 8000 · all three seeds',fontsize=15)
    fig.savefig(directory/'all_seeds.png',dpi=120);plt.close(fig)

    fig,axes=plt.subplots(3,6,figsize=(17,9),layout='constrained')
    for col,name in enumerate(ORDER):
        d=data[name];control=d['pulse_control_theta'];pulse=d['pulse_theta']
        for row,a in enumerate((control,pulse,np.abs(np.exp(1j*pulse)-np.exp(1j*control)))):
            axes[row,col].imshow(a,cmap='magma' if row==2 else 'twilight',vmin=0,vmax=2 if row==2 else 2*np.pi,origin='lower',interpolation='nearest')
            axes[row,col].set_xticks([]);axes[row,col].set_yticks([])
            if row==0:axes[row,col].set_title(LABELS[name],fontsize=11)
            if col==0:axes[row,col].set_ylabel(('Unforced','After local pulse','Difference (0–2)')[row])
    fig.suptitle(f'Response 400 updates after the same local angular pulse · seed {seed}\nDifference uses a shared scale; faint responses are not amplified',fontsize=15)
    fig.savefig(directory/'pulse.png',dpi=120);plt.close(fig)

    fig,axes=plt.subplots(1,2,figsize=(12,4),layout='constrained')
    for col,name in enumerate(ORDER):
        color=plt.get_cmap('tab10')(col)
        for r in report['records']:
            if r['model']!=name:continue
            records=r['records']
            axes[0].plot([x['update'] for x in records[1:]],[x['phase_aligned_interval_change'] for x in records[1:]],color=color,alpha=.65,label=LABELS[name] if r['seed']==seed else None)
            axes[1].plot([x['update'] for x in records],[x['bond_disagreement'] for x in records],color=color,alpha=.65)
    axes[0].set_title('Spatial change per 100 updates (global rotation removed)')
    axes[0].set_yscale('log');axes[0].set_ylabel('RMS phasor change')
    axes[1].set_title('Neighboring orientation disagreement')
    for ax in axes:ax.set_xlabel('Update');ax.grid(alpha=.2)
    axes[0].legend(fontsize=8)
    fig.savefig(directory/'activity.png',dpi=130);plt.close(fig)

    # Raster animation uses the exact same colormap and no inferred contours.
    try:font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',20)
    except OSError:font=ImageFont.load_default()
    cmap=plt.get_cmap('twilight');frames=[]
    for index,tick in enumerate(ticks):
        canvas=Image.new('RGB',(1000,760),'white');draw=ImageDraw.Draw(canvas)
        draw.text((20,10),f'Genesis · same seed {seed} · update {tick} · color = θ',fill='black',font=font)
        for panel,name in enumerate(ORDER):
            x=15+(panel%3)*330;y=55+(panel//3)*350
            draw.text((x,y),LABELS[name],fill='black',font=font)
            rgba=(cmap(data[name]['theta'][index]/(2*np.pi))*255).astype(np.uint8)
            tile=Image.fromarray(rgba[:,:,:3]).transpose(Image.Transpose.FLIP_TOP_BOTTOM).resize((310,310),Image.Resampling.NEAREST)
            canvas.paste(tile,(x,y+30))
        frames.append(canvas)
    frames[0].save(directory/'comparison.gif',save_all=True,append_images=frames[1:],duration=120,loop=0,optimize=False)
    for d in data.values():d.close()
    print(f'Rendered gallery in {directory}')


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('directory',type=Path)
    render(parser.parse_args().directory)
