"""Run the desktop studio, or produce artwork and a snapshot without a window."""
from __future__ import annotations

import argparse
import os
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--seed', type=int, default=7)
    parser.add_argument('--preset', choices=('Silk', 'Estuary', 'Filigree'), default='Silk')
    parser.add_argument('--load', type=Path, help='A saved bundle.json or its directory')
    parser.add_argument('--headless', action='store_true', help='Save a bundle and exit without Qt')
    parser.add_argument('--ticks', type=int, default=None, help='Warmup ticks (default 180 for desktop, 400 headless)')
    parser.add_argument('--guidance', type=float, default=None, help='Initial target guidance, 0..1')
    parser.add_argument('--size', type=int, default=None, help='Field width for a new run (default 512)')
    parser.add_argument('--agents', type=int, default=None, help='Population for a new run (default 90000)')
    parser.add_argument('--output', type=Path, default=Path('work/physarum_exports'))
    args = parser.parse_args()
    os.environ.setdefault('OPENBLAS_NUM_THREADS', '1')
    from .domain.model import PRESETS, Simulation
    from .application.session import Session
    from .adapters.render import Look
    from .adapters.storage import load_bundle, save_bundle
    from datetime import datetime, timezone
    from dataclasses import replace
    try:
        if args.ticks is not None and args.ticks < 0:
            raise ValueError('Ticks must be nonnegative')
        if args.load:
            if args.size is not None or args.agents is not None:
                raise ValueError('A loaded state keeps its saved dimensions and population')
            session, look = load_bundle(args.load)
        else:
            rules = replace(PRESETS[args.preset], size=512 if args.size is None else args.size,
                            agents=90_000 if args.agents is None else args.agents)
            session, look = Session(Simulation(args.seed, rules)), Look()
        if args.guidance is not None:
            session.guide(args.guidance)
        ticks = args.ticks if args.ticks is not None else (0 if args.load else 400 if args.headless else 180)
        session.advance(ticks, force=True)
        if args.headless:
            stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
            path = save_bundle(session, look, args.output / stamp)
            print(path.resolve())
            return 0
    except (ValueError, KeyError, OSError) as exc:
        parser.error(str(exc))
    from PyQt5.QtWidgets import QApplication
    from .adapters.desktop import StudioWindow
    app = QApplication([])
    app.setApplicationName('Physarum Studio')
    window = StudioWindow(session, look, args.output)
    if not args.load:
        window.preset.blockSignals(True)
        window.preset.setCurrentText(args.preset)
        window.preset.blockSignals(False)
    window.show()
    print(f'Physarum Studio ready / {app.platformName()} / tick {session.simulation.tick}', flush=True)
    return app.exec_()


if __name__ == '__main__':
    raise SystemExit(main())
