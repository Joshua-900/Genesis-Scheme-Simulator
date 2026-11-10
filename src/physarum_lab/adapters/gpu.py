"""Optional VisPy display adapter. Simulation stays on the CPU, graphics on GPU."""
from __future__ import annotations

import logging
from pathlib import Path

import numpy as np
from vispy import app, gloo

from .render import PALETTES, guide_overlay, intensity_map

VERTEX = '''
attribute vec2 position;
void main() { gl_Position = vec4(position, 0., 1.); }
'''


class DensityCanvas(app.Canvas):
    def __init__(self, parent, failure):
        super().__init__(parent=parent, keys=None, app='pyqt5', vsync=False)
        fragment = Path(__file__).with_name('density.frag').read_text(encoding='utf-8')
        self.program = gloo.Program(VERTEX, fragment)
        self.program['position'] = np.array([[-1, -1], [1, -1], [-1, 1], [1, 1]], np.float32)
        self.failure, self.ready = failure, False
        self.texture = None

    def present(self, simulation, look, zoom, center, show_guide):
        data = np.empty((*simulation.trail.shape, 4), np.float32)
        amber = getattr(simulation, 'amber', None)
        data[:, :, 0] = (
            intensity_map(simulation.trail, simulation.density, simulation.rules.agents, look.exposure)
            if amber is None or look.layer != 'amber' else 0
        )
        data[:, :, 1] = (
            intensity_map(amber.trail, amber.density, amber.rules.agents, look.exposure)
            if amber is not None and look.layer != 'ivory' else 0
        )
        data[:, :, 2] = guide_overlay(simulation) if show_guide else 0
        data[:, :, 3] = 1
        if self.texture is None:
            self.texture = gloo.Texture2D(data, interpolation='linear', wrapping='repeat', internalformat='rgba16f')
            self.program['field'] = self.texture
        else:
            self.texture.set_data(data)
        self.program['size'] = tuple(float(v) for v in self.physical_size)
        self.program['resolution'] = float(simulation.rules.size)
        self.program['bloom'] = float(look.bloom)
        self.program['zoom'] = float(zoom)
        self.program['center'] = tuple(float(v) for v in center)
        self.program['show_guide'] = float(show_guide)
        self.program['chase'] = float(amber is not None)
        for index, color in enumerate(PALETTES[look.palette]):
            self.program[f'color{index}'] = color / 255
        self.ready = True
        self.update()

    def on_draw(self, event):
        if not self.ready:
            return
        try:
            gloo.set_viewport(0, 0, *self.physical_size)
            gloo.set_state(depth_test=False, blend=False, cull_face=False)
            gloo.clear(color=(.012, .025, .04, 1.))
            self.program.draw('triangle_strip')
        except Exception:
            logging.exception('Physarum GPU display failed; using software')
            self.ready = False
            self.failure()
