"""Density-based art rendering. No access to simulation mutation or RNG."""
from __future__ import annotations

from dataclasses import dataclass
import math

import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter

PALETTES = {
    'Pearl': np.array([[3, 8, 14], [12, 41, 49], [57, 111, 111], [186, 197, 168], [255, 241, 211]], np.float32),
    'Ember': np.array([[8, 4, 10], [44, 14, 28], [131, 45, 40], [238, 129, 67], [255, 238, 199]], np.float32),
    'Moon': np.array([[4, 6, 12], [20, 29, 48], [67, 85, 113], [164, 185, 202], [244, 247, 245]], np.float32),
}


@dataclass(frozen=True)
class Look:
    palette: str = 'Pearl'
    exposure: float = 1.3
    bloom: float = .18
    layer: str = 'both'

    def __post_init__(self):
        if self.layer not in ('both', 'ivory', 'amber'):
            raise ValueError('Choose both, ivory or amber.')
        if self.palette not in PALETTES:
            raise ValueError('Unknown palette')
        if not math.isfinite(self.exposure) or not .1 <= self.exposure <= 4:
            raise ValueError('Exposure must be in .1..4')
        if not math.isfinite(self.bloom) or not 0 <= self.bloom <= 1:
            raise ValueError('Bloom must be in 0..1')


def colorize(intensity: np.ndarray, palette: str) -> np.ndarray:
    colors = PALETTES[palette]
    ramp = np.clip(intensity, 0, 1) * (len(colors) - 1)
    index = np.minimum(ramp.astype(int), len(colors) - 2)
    fraction = (ramp - index)[..., None]
    return colors[index] * (1 - fraction) + colors[index + 1] * fraction


def guide_alpha(simulation) -> np.ndarray:
    """Overlay follows the selected response, rather than always drawing zeros."""
    response = simulation.formula.spec.response if simulation.formula is not None else 'zero'
    wave = simulation.wave
    if response == 'zero':
        return np.exp(-wave**2 / .00025)
    if response == 'flow':
        return np.tanh(wave)
    return .5 + .5 * np.tanh(wave) * (1 if response == 'high' else -1)


def guide_overlay(simulation):
    alpha = guide_alpha(simulation)
    amber = getattr(simulation, 'amber', None)
    return np.maximum(alpha, guide_alpha(amber)) if amber is not None else alpha


def intensity_map(trail: np.ndarray, density: np.ndarray, agents: int, exposure: float) -> np.ndarray:
    """Stable exposure tied to population, rather than pumping per-frame extrema."""
    scale = agents / trail.size * 40
    mass = np.maximum(trail / scale - .08, 0)
    intensity = np.log1p(mass * exposure) / np.log(26.)
    # Live deposits add fine structure within the much smoother memory field.
    detail = np.sqrt(np.maximum(density, 0) / (agents / trail.size + 1))
    return np.clip(intensity + .035 * detail * intensity, 0, 1)


def radiance(trail: np.ndarray, density: np.ndarray, agents: int, look: Look) -> np.ndarray:
    rgb = colorize(intensity_map(trail, density, agents, look.exposure), look.palette)
    if look.bloom:
        light = np.maximum(rgb - 100, 0)
        for channel in range(3):
            rgb[:, :, channel] += gaussian_filter(light[:, :, channel], 3, mode='wrap') * look.bloom
    return np.ascontiguousarray(np.clip(rgb, 0, 255).astype(np.uint8))


def render(simulation, look: Look | None = None, side: int | None = None) -> Image.Image:
    look = look or Look()
    amber = getattr(simulation, 'amber', None)
    if amber is None:
        rgb = radiance(simulation.trail, simulation.density, simulation.rules.agents, look)
    else:
        ivory_light = intensity_map(simulation.trail, simulation.density, simulation.rules.agents, look.exposure)
        amber_light = intensity_map(amber.trail, amber.density, amber.rules.agents, look.exposure)
        if look.layer == 'ivory':
            amber_light.fill(0)
        elif look.layer == 'amber':
            ivory_light.fill(0)
        rgb = (np.array([3, 8, 14]) + ivory_light[..., None] * np.array([232, 222, 196])
               + amber_light[..., None] * np.array([242, 124, 41]))
        rgb = np.clip(rgb, 0, 255).astype(np.uint8)
    result = Image.fromarray(rgb[::-1])
    if side is not None and side != result.width:
        result = result.resize((side, side), Image.Resampling.LANCZOS)
    return result
