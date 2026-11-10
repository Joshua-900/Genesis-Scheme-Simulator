"""Algebraic checks of an equilibrium torque identity, not new root searches."""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

import numpy as np

from genesis_multiscale_audit import write_json
from src.genesis_audit.v1_adapter import V1Adapter
from .equations import alignment, derivative, laplacian


def check(n, seed, params):
    rng = np.random.default_rng(seed)
    theta = rng.uniform(-np.pi, np.pi, (n,n))
    tau = params.gamma / params.decay_tau * np.abs(alignment(theta))
    c = rng.uniform(0,1,(n,n))
    k, s = params.kappa / params.geom_decay, params.shell_geom_gain / params.geom_decay
    ux = k * tau * np.cos(theta) + s * derivative(c,-1)
    uy = k * tau * np.sin(theta) + s * derivative(c,-2)
    lx,ly=laplacian(ux),laplacian(uy)
    r=params.curv*(np.hypot(lx,ly)+1e-8)*np.sin(np.arctan2(ly,lx)-theta)
    epsilon_term=params.curv*1e-8*np.sin(np.arctan2(ly,lx)-theta)
    w=params.alpha+params.curv*k*tau
    neighbour=sum(np.roll(w,shift,axis)*np.sin(np.roll(theta,shift,axis)-theta) for axis in (-2,-1) for shift in (-1,1))
    shell=params.curv*s*(-np.sin(theta)*laplacian(derivative(c,-1))+np.cos(theta)*laplacian(derivative(c,-2)))
    torque=params.alpha*alignment(theta)+.1*tau+r
    max_error=float(np.max(np.abs(torque-(neighbour+.1*tau+shell+epsilon_term))))
    cancelled=float(abs(np.sum(w*neighbour)))
    budget_error=float(abs(np.sum(w*torque)-np.sum(w*(.1*tau+shell+epsilon_term))))
    if max(max_error,cancelled,budget_error)>1e-11:
        raise AssertionError("Weighted equilibrium-form algebra did not agree.")
    return {'N':n,'seed':seed,'decomposition_max_error':max_error,'weighted_neighbour_sum_error':cancelled,'weighted_budget_identity_error':budget_error}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory',type=Path)
    args=parser.parse_args()
    destination=args.directory/'shell_balance_checks.json'
    if destination.exists():
        raise ValueError('Do not overwrite a completed algebra supplement.')
    params=V1Adapter().params
    checks=[check(n,s,params) for n in (4,6,8) for s in (1,2,3)]
    write_json(destination,{'kind':'post-search analytic refinement; frozen search unchanged','source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'checks':checks,'shell_off_exact_equilibrium_weighted_mean_tau_bound':params.curv*1e-8/.1,
        'scope':'Constructed fields obey displacement equilibrium form only. Random C is not asserted to satisfy the nonlinear compression relation or to be a full fixed point. These check algebraic identities, not equilibrium existence or stability.',
        'numerical_caution':'Exact-equilibrium bounds require residual allowances when applied to approximate roots; raw/source acceptance at1e-8 is not exact equality.'})
    print('Verified decomposition and weighted cancellation identities on nine constructed fields; no new solve or dynamics.')


if __name__=='__main__':
    main()
