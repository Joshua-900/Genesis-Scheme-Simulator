"""Batched transcription for equilibrium analysis; never an engine dependency.

All axes before the final two spatial axes are independent evaluation batches.
The historical staged map and epsilon prescription are retained exactly.
"""

from __future__ import annotations

import numpy as np


def derivative(v, axis):
    return .5 * (np.roll(v, -1, axis) - np.roll(v, 1, axis))


def laplacian(v):
    return sum(np.roll(v, shift, axis) for axis in (-2, -1) for shift in (-1, 1)) - 4 * v


def alignment(theta):
    return sum(np.sin(np.roll(theta, shift, axis) - theta) for axis in (-2, -1) for shift in (-1, 1))


def quantities(theta, tau, ux, uy, params):
    a = alignment(theta)
    tau_next = (1 - params.decay_tau) * tau + params.gamma * np.abs(a)
    vx = (1 - params.geom_decay) * ux + params.kappa * tau_next * np.cos(theta)
    vy = (1 - params.geom_decay) * uy + params.kappa * tau_next * np.sin(theta)
    determinant = (1 + derivative(vx, -1)) * (1 + derivative(vy, -2)) - derivative(vx, -2) * derivative(vy, -1)
    compression = np.exp(-determinant ** 2 / (params.sigma_c2 + 1e-8))
    next_x = vx + params.shell_geom_gain * derivative(compression, -1)
    next_y = vy + params.shell_geom_gain * derivative(compression, -2)
    lx, ly = laplacian(next_x), laplacian(next_y)
    curvature = params.curv * (np.hypot(lx, ly) + 1e-8) * np.sin(np.arctan2(ly, lx) - theta)
    raw_torque = params.alpha * a + .1 * tau_next + curvature
    mobility = 1 - params.lock_strength * compression
    return {"a": a, "tau": tau_next, "ux": next_x, "uy": next_y, "C": compression,
        "J": determinant, "Lnorm": np.hypot(lx, ly), "R": curvature, "T": raw_torque, "q": mobility}


def reduced_fields(x, n, params):
    fields = np.asarray(x).reshape(np.shape(x)[:-1] + (3, n, n))
    theta, ux, uy = [fields[..., i, :, :] for i in range(3)]
    tau = params.gamma / params.decay_tau * np.abs(alignment(theta))
    return theta, tau, ux, uy


def reduced_residual(x, n, params):
    theta, tau, ux, uy = reduced_fields(x, n, params)
    d = quantities(theta, tau, ux, uy, params)
    # Raw torque prevents a low-mobility plateau from masquerading as a root.
    residual = np.stack((d["T"], (d["ux"] - ux) / params.geom_decay, (d["uy"] - uy) / params.geom_decay), axis=-3)
    return residual.reshape(np.shape(x))


def reduced_jacobian(x, n, params):
    """Batched forward differences for the solver, not a stability Jacobian."""
    step = 1e-6 * np.maximum(1., np.abs(x))
    trials = np.broadcast_to(x, (len(x), len(x))).copy()
    trials[np.arange(len(x)), np.arange(len(x))] += step
    return ((reduced_residual(trials, n, params) - reduced_residual(x, n, params)) / step[:, None]).T


def active_from_reduced(x, n, params):
    return np.stack(reduced_fields(x, n, params)).ravel()


def active_map(x, n, params, angular_step=.05):
    fields = np.asarray(x).reshape(np.shape(x)[:-1] + (4, n, n))
    theta, tau, ux, uy = [fields[..., i, :, :] for i in range(4)]
    d = quantities(theta, tau, ux, uy, params)
    # Lifted angle output avoids artificial differentiation across a 2pi wrap.
    result = np.stack((theta + angular_step * d["q"] * d["T"], d["tau"], d["ux"], d["uy"]), axis=-3)
    return result.reshape(np.shape(x))


def normalized_difference(x, y, n):
    difference = (np.asarray(x) - np.asarray(y)).reshape(4, n, n).copy()
    difference[0] = (difference[0] + np.pi) % (2 * np.pi) - np.pi
    difference[1] /= 2.
    difference[2:] /= 4.8
    return float(np.sqrt(np.mean(difference ** 2)))


def active_jacobian(x, n, params, step):
    """Central FD derivative in scaled active coordinates (theta,tau,ux,uy)."""
    scale = np.repeat([1., 2., 4.8, 4.8], n * n)
    perturbations = np.eye(len(x)) * (step * scale)
    positive = active_map(x[None, :] + perturbations, n, params)
    negative = active_map(x[None, :] - perturbations, n, params)
    return ((positive - negative) / (2 * step) / scale[None, :]).T
