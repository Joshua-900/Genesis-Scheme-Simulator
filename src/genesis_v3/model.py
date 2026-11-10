"""Nearest-neighbor exchange and geometric diagnostics."""

import numpy as np
from scipy.ndimage import center_of_mass, label


def fixture(size, kind, support_radius=.25, width=1., *, center_x=0., winding=1, phase=0.):
    """A fixed up-pointing perimeter on a square."""
    axis = np.linspace(-width / 2, width / 2, size)
    x, y = np.meshgrid(axis, axis)
    x -= center_x
    radius = np.hypot(x, y)
    profile = np.pi * np.maximum(1 - radius / support_radius, 0)**2
    if kind == 'uniform':
        profile.fill(0)
    azimuth = np.zeros_like(x)
    if kind == 'charged':
        azimuth = winding * np.arctan2(y, x) + phase
    elif kind == 'uncharged':
        azimuth = 2 * np.pi * x
    return np.stack((np.sin(profile) * np.cos(azimuth),
                     np.sin(profile) * np.sin(azimuth), np.cos(profile)), axis=-1)


def effective_field(field, steepness=0., axis_weight=0.):
    """Negative energy derivative on the interior, up to radial terms."""
    center = field[1:-1, 1:-1]
    neighbors = (field[:-2, 1:-1] + field[2:, 1:-1]
                 + field[1:-1, :-2] + field[1:-1, 2:])
    if steepness:
        for neighbor in (field[:-2, 1:-1], field[2:, 1:-1],
                         field[1:-1, :-2], field[1:-1, 2:]):
            difference = neighbor - center
            distance_squared = np.einsum('...i,...i->...', difference, difference)[..., None]
            neighbors += steepness * distance_squared * difference
    neighbors[..., 2] += axis_weight * center[..., 2]
    return neighbors


def step(field, factor, steepness=0., axis_weight=0.):
    """Advance projected exchange descent, with a fixed perimeter."""
    center = field[1:-1, 1:-1]
    neighbors = effective_field(field, steepness, axis_weight)
    projection = np.einsum('...i,...i->...', center, neighbors)[..., None]
    tangent = neighbors - projection * center
    candidate = center + factor * tangent
    length = np.sqrt(np.einsum('...i,...i->...', candidate, candidate))[..., None]
    center[:] = candidate / length


def charge_map(field):
    """Return signed charge per plaquette and the ambiguous triangle count."""
    a, b = field[:-1, :-1], field[:-1, 1:]
    c, d = field[1:, 1:], field[1:, :-1]
    area = np.zeros(a.shape[:2])
    ambiguous = 0
    for u, v, w in ((a, b, c), (a, c, d)):
        numerator = np.sum(u * np.cross(v, w), axis=-1)
        denominator = 1 + np.sum(u * v + v * w + w * u, axis=-1)
        ambiguous += int(np.count_nonzero((denominator <= 1e-12) & (np.abs(numerator) <= 1e-12)))
        area += 2 * np.arctan2(numerator, denominator)
    return area / (4 * np.pi), ambiguous


def measure(field, steepness=0., axis_weight=0., width=1.):
    """Exchange energy above uniform, lattice charge, and equivalent core radius."""
    charge_density, ambiguous = charge_map(field)
    energy = 0.
    for axis in (0, 1):
        squared = np.sum(np.diff(field, axis=axis)**2, axis=-1)
        energy += float(np.sum(.5 * squared + .25 * steepness * squared**2))
    radius_cells = float(np.sqrt(np.count_nonzero(field[..., 2] < 0) / np.pi))
    energy += .5 * axis_weight * float(np.sum(field[..., :2]**2))
    spacing = width / (len(field) - 1)
    tilt_radius = float(np.sqrt(np.sum((1 - field[..., 2]) / 2) / np.pi) * spacing)
    charge_columns = charge_density.sum(axis=0)
    x = (np.arange(len(charge_columns)) + .5) * spacing - width / 2
    halves = {}
    for name, mask in (('left', x < 0), ('right', x >= 0)):
        charge = float(charge_columns[mask].sum())
        # Suppress a centroid when no substantial signed texture remains.
        centroid = float(np.dot(x[mask], charge_columns[mask]) / charge) if abs(charge) >= .5 else None
        halves[name] = dict(charge=None if ambiguous else charge, x=None if ambiguous else centroid)
    core_mask = field[..., 2] < 0
    components, count = label(core_mask)
    centers = center_of_mass(core_mask, components, range(1, count + 1))
    separation = float(np.linalg.norm(np.subtract(*centers)) * spacing) if count == 2 else None
    return dict(energy=energy, charge=None if ambiguous else float(charge_columns.sum()),
                ambiguous_triangles=ambiguous, core_radius_cells=radius_cells,
                core_radius=radius_cells * spacing, tilt_radius=tilt_radius,
                halves=halves,
                core_count=count, core_separation=separation,
                max_out_of_control_plane=float(np.max(np.abs(field[..., 1]))))
