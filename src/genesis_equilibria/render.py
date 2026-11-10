"""Present frozen equilibrium search results without changing any fit or gate."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def render(directory):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt

    report=json.loads((directory/'report.json').read_text(encoding='utf-8'))
    roots=report['roots']
    fig,axes=plt.subplots(1,3,figsize=(12,4.6),layout='constrained',sharex=True,sharey=True)
    for axis,n in zip(axes,(4,6,8)):
        axis.axvspan(1e-3,1,color='#4f9763',alpha=.07)
        axis.axhspan(1e-16,1e-8,color='#4f9763',alpha=.07)
        for mode,color in (('full','#356f9c'),('curvature_off','#b37144')):
            for accepted,marker in ((True,'o'),(False,'x')):
                rows=[r for r in roots if r['grid']==n and r['mode']==mode and r['accepted']==accepted]
                axis.scatter([max(r['rms_alignment_torque'],1e-16) for r in rows],[max(r['raw_torque_max'],1e-16) for r in rows],
                    color=color,marker=marker,s=42,label=f"{mode.replace('_',' ')}: {'accepted' if accepted else 'rejected'}")
        axis.axhline(1e-8,color='#777777',linestyle='--',linewidth=.8)
        axis.axvline(1e-3,color='#777777',linestyle='--',linewidth=.8)
        axis.set(xscale='log',yscale='log',xlim=(5e-17,1),ylim=(5e-17,1),title=f'{n}×{n} periodic grid',xlabel='RMS net alignment torque')
        axis.set_xticks([1e-16,1e-12,1e-8,1e-4,1])
    axes[0].set_ylabel('Maximum raw angular torque')
    axes[0].legend(fontsize=7,loc='upper left')
    fig.suptitle('Bounded V1 equilibrium search: no accepted nonzero-torque witness',fontsize=13)
    fig.supxlabel('Dashed thresholds: raw torque ≤ 1e−8 and RMS alignment ≥ 1e−3. Values below 1e−16 plotted at the floor.',fontsize=9)
    fig.savefig(directory/'search_summary.png',dpi=160)
    plt.close(fig)
    lines=['# V1 equilibrium search','',report['claim_boundary'],'',
        f"Attempts: **{len(roots)}**. Accepted numerical roots: **{report['accepted_roots']}**. Accepted nonzero-alignment witnesses: **{report['interesting_roots']}**.",
        f"Milestone gate: **{'passed' if report['milestone_gate_passed'] else 'not passed'}**. Preserved engines unchanged: **{report['baseline_and_engines_unchanged']}**.",'',
        'Acceptance is a finite residual criterion, not an existence proof. A solver success flag alone was not accepted.','',
        '| Grid | Model | Attempts | Accepted | Nonzero-alignment witnesses | Solver success but rejected |',
        '| --- | --- | ---: | ---: | ---: | ---: |']
    for n in (4,6,8):
        for mode in ('full','curvature_off'):
            rows=[r for r in roots if r['grid']==n and r['mode']==mode]
            lines.append(f"| {n}×{n} | {mode} | {len(rows)} | {sum(r['accepted'] for r in rows)} | {sum(r['interesting_nonzero_alignment'] for r in rows)} | {sum(r['solver_success'] and not r['accepted'] for r in rows)} |")
    lines+=['','![Residuals and witness thresholds](search_summary.png)','',
        '## Stability coverage','',
        'Only uniform/checkerboard controls qualified for the scheduled checks. Their zero-source/nonsmooth locations prevent ordinary Jacobian certification under this protocol. Some uniform directions are nearly neutral; checkerboard spectra show expansion near 1.12, with numerical base drift explicitly recorded. “Unresolved” does not mean the uniform state was proved unstable.',
        '', 'No accepted interesting root existed, so conditional locking-off and doubled-grid witness tests were not triggered. The known local tiling identity is unit-tested; this is not empirical larger-grid validation of a new pattern.', '',
        '## Complete attempt log','', '| ID | Solver success | Accepted | Max raw torque | RMS alignment | SciPy nfev |','| --- | --- | --- | ---: | ---: | ---: |']
    for r in roots:
        lines.append(f"| {r['id']} | {r['solver_success']} | {r['accepted']} | {r['raw_torque_max']:.6g} | {r['rms_alignment_torque']:.6g} | {r['function_evaluations']} |")
    lines+=['', '## Scope','',
        'The frozen 160 max_nfev budget is SciPy’s reported function-evaluation counter. Batched finite-difference Jacobian evaluations add work outside that counter. No budget, parameter, acceptance threshold or witness criterion was changed after results.',
        '', 'A bounded multistart failure does not establish nonexistence. Rejected cases include stalled optimization and budget exhaustion. Dynamic/rotating structures and geometry-only equilibria with zero alignment torque are outside the specific nonzero-alignment witness gate.',
        '', '## Artifacts','', '- [Frozen protocol](protocol.json)', '- [Metrics and stability traces](report.json)', '- `candidate_states.npz`: all final active-state vectors, including rejected attempts.',
        '- [Separate shell-balance algebra checks](shell_balance_checks.json)',
        '', 'The shell-balance supplement is a post-search analytical deduction, not a changed search criterion or a successful equilibrium witness.','']
    (directory/'summary.md').write_text('\n'.join(lines),encoding='utf-8')
    (directory/'presentation.json').write_text(json.dumps({'renderer_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'report_sha256':hashlib.sha256((directory/'report.json').read_bytes()).hexdigest(),'fits_or_gates_changed':False},indent=2)+'\n',encoding='utf-8')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory',type=Path)
    args=parser.parse_args()
    render(args.directory)


if __name__=='__main__':
    main()
