"""Experimental vacancy semantics, isolated from every preserved engine.

Absent sites contribute no alignment bond, dipole edge or triad. Geometry uses
no-flux missing-edge differences. A hole does not connect its former neighbors.
Fully occupied states dispatch to the unchanged historical recipe exactly.
"""
import numpy as np
from src.genesis_gallery import legacy

FIELDS=('theta','tau','ux','uy','C')


def step(state,p):
    active=state['active']
    if np.all(active):
        legacy.step(state,p);return
    theta,tau,ux,uy=[np.where(active,state[k],0.) for k in FIELDS[:4]]
    n=len(theta);rows,cols=np.indices(theta.shape)
    neighbor=lambda v,di,dj:np.roll(v,(-di,-dj),(0,1))
    edge=lambda di,dj:active & neighbor(active,di,dj)
    align=sum(edge(di,dj)*np.sin(neighbor(theta,di,dj)-theta) for di,dj in ((1,0),(-1,0),(0,1),(0,-1)))
    tau=active*((1-p['decay_tau'])*tau+p['gamma0']*np.abs(align))
    ux=active*((1-p['geom_decay'])*ux+p['kappa0']*tau*np.cos(theta))
    uy=active*((1-p['geom_decay'])*uy+p['kappa0']*tau*np.sin(theta))
    xd,yd=cols+ux,rows+uy
    phase=-p['well0']*np.sin(4*theta)
    dipole=np.zeros_like(theta)
    for di,dj in ((1,0),(-1,0),(0,1),(0,-1)):
        valid=edge(di,dj)&(rows+di>=0)&(rows+di<n)&(cols+dj>=0)&(cols+dj<n)
        thn=neighbor(theta,di,dj)
        phi=np.arctan2(neighbor(yd,di,dj)-yd,neighbor(xd,di,dj)-xd)
        quality=np.cos(theta-phi)*np.cos(thn-(phi+np.pi))
        dipole+=p['dipole0']*valid*quality*np.sin(phi-theta)
        dipole+=np.roll(p['dipole0']*valid*quality*np.sin(phi+np.pi-thn),(di,dj),(0,1))
    tri=np.zeros_like(theta)
    wrap=lambda v:(v+np.pi)%(2*np.pi)-np.pi
    templates=[((0,0),(1,0),(0,1),(.25*np.pi,0,.5*np.pi)),((0,0),(-1,0),(0,1),(.75*np.pi,np.pi,.5*np.pi)),
        ((0,0),(1,0),(0,-1),(-.25*np.pi,0,-.5*np.pi)),((0,0),(-1,0),(0,-1),(-.75*np.pi,np.pi,-.5*np.pi))]
    for o0,o1,o2,angles in templates:
        offsets=(o0,o1,o2);valid=np.ones_like(active);fields=[]
        for di,dj in offsets:
            valid&=neighbor(active,di,dj)&(rows+di>=0)&(rows+di<n)&(cols+dj>=0)&(cols+dj<n)
            fields.append(neighbor(theta,di,dj))
        score=np.exp(-sum(wrap(th-a)**2 for th,a in zip(fields,angles))/p['tri_sigma2'])
        score*=valid*(score>=1e-3)
        for (di,dj),th,a in zip(offsets,fields,angles):
            tri+=np.roll(p['tri0']*score*np.sin(a-th),(di,dj),(0,1))
    difference=lambda v,di,dj:edge(di,dj)*(neighbor(v,di,dj)-v)
    lap=lambda v:sum(difference(v,di,dj) for di,dj in ((1,0),(-1,0),(0,1),(0,-1)))
    lx,ly=lap(ux),lap(uy)
    curvature=p['curv0']*(np.hypot(lx,ly)+1e-6)*np.sin(np.arctan2(ly,lx)-theta)
    ux_x,ux_y=difference(ux,0,1),difference(ux,1,0)
    uy_x,uy_y=difference(uy,0,1),difference(uy,1,0)
    determinant=(1+ux_x)*(1+uy_y)-ux_y*uy_x
    c=active*np.exp(-determinant**2/(p['sigma_c2']+1e-8))
    ux+=p['shell_geom_gain']*.5*(difference(c,0,1)-difference(c,0,-1))
    uy+=p['shell_geom_gain']*.5*(difference(c,1,0)-difference(c,-1,0))
    total=p['alpha0']*align+.1*tau+phase*(1+p['phase_lock_gain']*c)+dipole+tri*(1+p['tri_lock_gain']*c)+curvature
    state.update(theta=np.where(active,(theta+p['dt']*total*(1-p['lock_strength']*c))%(2*np.pi),0.),
        tau=tau,ux=np.where(active,ux,0.),uy=np.where(active,uy,0.),C=c)
