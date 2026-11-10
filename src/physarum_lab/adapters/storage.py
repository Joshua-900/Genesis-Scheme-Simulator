"""Versioned local snapshots. Loading never unpickles or executes code."""
from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

import numpy as np

from ..application.session import Session
from ..domain.model import Simulation
from ..domain.chase import Chase
from .render import Look, render

VERSION = 4
ARRAYS = ('x', 'y', 'heading', 'trail', 'density')


def save_bundle(session: Session, look: Look, directory: Path) -> Path:
    """Create a new, complete PNG + numerical snapshot bundle; never overwrite."""
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=False)
    snapshot = session.simulation.snapshot()
    arrays = {key: snapshot.pop(key) for key in ARRAYS}
    if 'amber' in snapshot:
        arrays.update({f'amber_{key}': snapshot['amber'].pop(key) for key in ARRAYS})
    np.savez_compressed(directory / 'state.npz', **arrays)
    render(session.simulation, look, side=1600).save(directory / 'artwork.png')
    sources = Path(__file__).resolve().parents[1]
    metadata = dict(version=VERSION, created_utc=datetime.now(timezone.utc).isoformat(),
                    simulation=snapshot, look=asdict(look),
                    session=dict(guidance=session.guidance, target_guidance=session.target_guidance,
                                 transition_ticks=session.transition_ticks, release_at=session.release_at),
                    numpy_version=np.__version__,
                    state_sha256=hashlib.sha256((directory / 'state.npz').read_bytes()).hexdigest(),
                    sources={p.relative_to(sources).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                             for p in sources.rglob('*') if p.suffix in ('.py', '.frag')})
    (directory / 'bundle.json').write_text(json.dumps(metadata, indent=2) + '\n', encoding='utf-8')
    return directory


def load_bundle(path: Path) -> tuple[Session, Look]:
    path = Path(path)
    if path.is_dir():
        path = path / 'bundle.json'
    metadata = json.loads(path.read_text(encoding='utf-8'))
    if metadata.get('version') not in (1, 2, 3, VERSION):
        raise ValueError('Unsupported Physarum snapshot version')
    state_path = path.parent / 'state.npz'
    if hashlib.sha256(state_path.read_bytes()).hexdigest() != metadata['state_sha256']:
        raise ValueError('Snapshot checksum does not match')
    snapshot = metadata['simulation']
    with np.load(state_path, allow_pickle=False) as archive:
        snapshot.update({key: archive[key] for key in ARRAYS})
        if 'amber' in snapshot:
            snapshot['amber'].update({key: archive[f'amber_{key}'] for key in ARRAYS})
    simulation = Chase.restore(snapshot) if 'amber' in snapshot else Simulation.restore(snapshot)
    return Session(simulation, playing=False, **metadata['session']), Look(**metadata['look'])
