"""Run with .venv\\Scripts\\python.exe -B -m src.genesis_sandbox."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--seed',type=int,default=1)
    parser.add_argument('--trails',action='store_true',help='Open the linked sheet and tracer view.')
    parser.add_argument('--replay',type=Path,help='Replay an exported recipe, then open it paused.')
    parser.add_argument('--export-root',type=Path,help='Parent directory for new export bundles.')
    args = parser.parse_args()
    os.environ.setdefault('GENESIS_USE_CUPY','False')
    os.environ.setdefault('OPENBLAS_NUM_THREADS','1')
    from PyQt5.QtWidgets import QApplication
    from .model import Sandbox
    from .lab_model import LabSandbox
    from .ui import SandboxWindow
    app = QApplication([sys.argv[0]])
    app.setApplicationName('Genesis creative sandbox')
    try:
        if args.replay:
            recipe=json.loads(args.replay.read_text(encoding='utf-8'))
            model=LabSandbox.replay(recipe) if recipe.get('version')==2 else Sandbox.replay(recipe)
        else:model=LabSandbox(args.seed)
    except (ValueError,KeyError,OSError) as exc:
        parser.error(str(exc))
    if args.trails:
        from .trail_view import TrailWindow
        window = TrailWindow(model, demo=not args.replay)
        window.show()
        print(f'Sheet & Trails ready · seed {model.seed} · update {model.update}', flush=True)
        return app.exec_()
    window = SandboxWindow(model,args.export_root)
    if args.replay:
        window.view.setCurrentIndex(max(0,window.view.findData(recipe.get('visible_field','theta'))))
        window.render_style.setCurrentIndex(max(0,window.render_style.findData(recipe.get('render_style','classic'))))
        window.zoom.setCurrentIndex(max(0,window.zoom.findData(recipe.get('view_zoom',1))))
        window.compare.setChecked(recipe.get('compare_view',True))
        if 'torus_camera' in recipe:
            from .torus import TorusScene
            for canvas in window.canvases:canvas.scene=TorusScene(**recipe['torus_camera'])
        window.seams.setChecked(recipe.get('show_seams',False))
        window.refresh()
    window.show()
    print(f'Field Lab ready on {app.platformName()} · seed {model.seed} · update {model.update}',flush=True)
    return app.exec_()


if __name__ == '__main__':
    raise SystemExit(main())
