"""Headless legacy recipe and vectorized evaluation of its existing rules.

The original file is read but never imported: GUI setup is not executed.
The reference update is extracted directly for parity checks. Mixed periodic
alignment/open dipole-triad boundaries, forward compression and PRE-shell
curvature are deliberately retained. This is not the modern seven-rule adapter.
"""

from __future__ import annotations

import ast
from pathlib import Path

import numpy as np


SOURCE = Path(__file__).resolve().parents[2] / 'genesis_fields_pretty.py'
CONSTANTS = {'dt','alpha0','gamma0','kappa0','well0','dipole0','tri0','curv0','decay_tau','geom_decay',
    'tri_sigma','tri_sigma2','sigma_c','sigma_c2','lock_strength','tri_lock_gain','phase_lock_gain','shell_geom_gain'}


def reference(n):
    tree=ast.parse(SOURCE.read_text(encoding='utf-8'))
    nodes=[]
    for node in tree.body:
        if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id in CONSTANTS for t in node.targets):
            nodes.append(node)
        elif isinstance(node,ast.FunctionDef) and node.name in ('angle_diff','update_genesis'):
            nodes.append(node)
    namespace={'np':np,'N':n}
    namespace['X'],namespace['Y']=np.meshgrid(np.arange(n),np.arange(n))
    exec(compile(ast.Module(body=nodes,type_ignores=[]),str(SOURCE),'exec'),namespace)
    return namespace


def defaults():
    namespace=reference(4)
    return {name:float(namespace[name]) for name in CONSTANTS}


def step(state,p):
    theta,tau,ux,uy=[state[k] for k in ('theta','tau','ux','uy')]
    n=len(theta)
    up,down,left,right=[np.roll(theta,s,a) for a,s in ((0,-1),(0,1),(1,1),(1,-1))]
    align=np.sin(up-theta)+np.sin(down-theta)+np.sin(left-theta)+np.sin(right-theta)
    tau=(1-p['decay_tau'])*tau+p['gamma0']*np.abs(align)
    ux=(1-p['geom_decay'])*ux+p['kappa0']*tau*np.cos(theta)
    uy=(1-p['geom_decay'])*uy+p['kappa0']*tau*np.sin(theta)
    x,y=np.meshgrid(np.arange(n),np.arange(n));xd,yd=x+ux,y+uy
    phase=-p['well0']*np.sin(4*theta)
    dipole=np.zeros_like(theta)
    rows,cols=np.indices(theta.shape)
    for di,dj in ((1,0),(-1,0),(0,1),(0,-1)):
        valid=(rows+di>=0)&(rows+di<n)&(cols+dj>=0)&(cols+dj<n)
        thn=np.roll(theta,(-di,-dj),(0,1))
        phi=np.arctan2(np.roll(yd,(-di,-dj),(0,1))-yd,np.roll(xd,(-di,-dj),(0,1))-xd)
        quality=np.cos(theta-phi)*np.cos(thn-(phi+np.pi))
        dipole+=p['dipole0']*valid*quality*np.sin(phi-theta)
        dipole+=np.roll(p['dipole0']*valid*quality*np.sin(phi+np.pi-thn),(di,dj),(0,1))
    tri=np.zeros_like(theta)
    wrap=lambda v:(v+np.pi)%(2*np.pi)-np.pi
    templates=[((0,0),(1,0),(0,1),(.25*np.pi,0,.5*np.pi)),((0,0),(-1,0),(0,1),(.75*np.pi,np.pi,.5*np.pi)),
        ((0,0),(1,0),(0,-1),(-.25*np.pi,0,-.5*np.pi)),((0,0),(-1,0),(0,-1),(-.75*np.pi,np.pi,-.5*np.pi))]
    for o0,o1,o2,angles in templates:
        offsets=(o0,o1,o2)
        valid=np.ones_like(theta,dtype=bool)
        fields=[]
        for di,dj in offsets:
            valid&=(rows+di>=0)&(rows+di<n)&(cols+dj>=0)&(cols+dj<n)
            fields.append(np.roll(theta,(-di,-dj),(0,1)))
        score=np.exp(-sum(wrap(th-a)**2 for th,a in zip(fields,angles))/p['tri_sigma2'])
        score=score*valid*(score>=1e-3)
        for (di,dj),th,a in zip(offsets,fields,angles):
            tri+=np.roll(p['tri0']*score*np.sin(a-th),(di,dj),(0,1))
    lap=lambda v:sum(np.roll(v,s,a) for a in (0,1) for s in (-1,1))-4*v
    lx,ly=lap(ux),lap(uy)
    curvature=p['curv0']*(np.hypot(lx,ly)+1e-6)*np.sin(np.arctan2(ly,lx)-theta)
    ux_x,ux_y=np.roll(ux,-1,1)-ux,np.roll(ux,-1,0)-ux
    uy_x,uy_y=np.roll(uy,-1,1)-uy,np.roll(uy,-1,0)-uy
    determinant=(1+ux_x)*(1+uy_y)-ux_y*uy_x
    c=np.exp(-determinant**2/(p['sigma_c2']+1e-8))
    ux+=p['shell_geom_gain']*.5*(np.roll(c,-1,1)-np.roll(c,1,1))
    uy+=p['shell_geom_gain']*.5*(np.roll(c,-1,0)-np.roll(c,1,0))
    total=p['alpha0']*align+.1*tau+phase*(1+p['phase_lock_gain']*c)+dipole+tri*(1+p['tri_lock_gain']*c)+curvature
    state.update(theta=(theta+p['dt']*total*(1-p['lock_strength']*c))%(2*np.pi),tau=tau,ux=ux,uy=uy,C=c)
