"""Shared fixed-scale pixels and self-contained local export bundles."""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

import matplotlib
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from .model import LABELS, LANES


def pixels(state, field='theta'):
    if field not in ('theta','C','activity'):
        raise ValueError('View must be theta, C or activity.')
    values = state[field]/(2*np.pi) if field == 'theta' else state.get(field,np.zeros_like(state['theta']))/(2 if field=='activity' else 1)
    cmap = matplotlib.colormaps['twilight' if field == 'theta' else 'magma']
    # Row zero is the bottom of the displayed grid, matching the review gallery.
    rgb=(cmap(values)[:,:,:3]*255).astype(np.uint8)
    rgb[~state.get('active',np.ones_like(state['theta'],dtype=bool))]=[3,8,15]
    return np.ascontiguousarray(rgb[::-1])


def export_bundle(model, directory, field='theta',style='classic',zoom=1,compare=True,camera=None,seams=False):
    """Create a new directory with image, recipe and full float64 field snapshot."""
    if field not in ('theta','C','activity'):
        raise ValueError('View must be theta, C or activity.')
    if style not in ('classic','dashes','torus'):raise ValueError('Unknown rendering style.')
    if zoom not in (1,2,4):raise ValueError('Unknown view zoom.')
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=False)
    side = 640
    image = Image.new('RGB', (2*side+72 if compare else side+48, side+140), '#101820')
    draw = ImageDraw.Draw(image)
    try:
        font = ImageFont.truetype('C:/Windows/Fonts/arial.ttf', 21)
    except OSError:
        font = ImageFont.load_default()
    scale = 'orientation theta · 0 to 2π' if field == 'theta' else 'compression C · 0 to 1' if field=='C' else 'angular activity · 0 to 2'
    draw.text((24,16), f'Field Lab · seed {model.seed} · update {model.update} · {scale}', font=font, fill='#f2f5f6')
    for index, name in enumerate(LANES if compare else LANES[:1]):
        x = 24+index*(side+24)
        draw.text((x,56), LABELS[index], font=font, fill='#b8c7cd')
        from .render import image as field_image
        tile = field_image(model.states[name],field,style,side,zoom,camera,seams)
        image.paste(tile,(x,94))
    text='Vacancy experiment · shared dropouts and fresh arrivals' if hasattr(model,'active') else 'Historical recipe · identical initial angles and brush prescriptions'
    draw.text((24,side+108),text,font=font,fill='#b8c7cd')
    image.save(directory/'pattern.png')
    np.savez_compressed(directory/'fields.npz', **{f'{name}_{key}':value for name in LANES for key,value in model.states[name].items()})
    recipe = model.recipe()
    recipe.update(created_utc=datetime.now(timezone.utc).isoformat(), visible_field=field,render_style=style,view_zoom=zoom,compare_view=bool(compare),
                  numpy_version=np.__version__, snapshot_precision='float64',
                  presentation_source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    if style=='torus':
        from .torus import TorusScene
        recipe.update(torus_camera=TorusScene(**(camera or {})).camera(),show_seams=bool(seams))
        recipe['torus_renderer_sha256']=hashlib.sha256(Path(__file__).with_name('torus.py').read_bytes()).hexdigest()
    recipe['dash_renderer_sha256']=hashlib.sha256(Path(__file__).with_name('render.py').read_bytes()).hexdigest()
    (directory/'recipe.json').write_text(json.dumps(recipe,indent=2)+'\n',encoding='utf-8')
    (directory/'README.txt').write_text(
        'pattern.png records the selected fixed-scale view. fields.npz stores all fields in float64.\n'
        'recipe.json records presets, seed, update count, brush edits and source fingerprints.\n'
        'Replay from the repo root:\n'
        f'.venv\\Scripts\\python.exe -B -m src.genesis_sandbox --replay "{directory.resolve() / "recipe.json"}"\n'
        'Replay requires matching dynamics sources; the saved field snapshot remains available independently.\n',encoding='utf-8')
    return directory
