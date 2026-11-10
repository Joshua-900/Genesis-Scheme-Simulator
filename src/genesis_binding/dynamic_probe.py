"""Temporary angular transport probe; retained fields follow unchanged V1 rules.

The probe is an external intervention, not a new autonomous Genesis mechanism.
It samples no state onto new coordinates and never changes retained fields.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from src.genesis_grid import step
from src.genesis_grid.rules_locking import locking_postprocess
from src.genesis_motion.observations import delta


@dataclass(frozen=True)
class ProbeConfig:
    radius: float = 3.
    duration: int = 80
    follow: int = 80
    interval: int = 5
    speeds: tuple[float,...] = (.05,.10)
    directional_gradient_cap: float = 1.
    minimum_axial_movement: float = .5
    maximum_translation_relative_error: float = 1.
    numerical_tolerance: float = 1e-12


def phase_gradient(theta):
    wrap = lambda v:(v+np.pi)%(2*np.pi)-np.pi
    gx = .5*(wrap(np.roll(theta,-1,1)-theta)+wrap(theta-np.roll(theta,1,1)))
    gy = .5*(wrap(np.roll(theta,-1,0)-theta)+wrap(theta-np.roll(theta,1,0)))
    return np.stack((gx,gy),axis=-1)


class AngularProbe:
    def __init__(self,n,centers,directions,speed,config=ProbeConfig()):
        self.n,self.centers,self.directions = n,np.asarray(centers,float),np.asarray(directions,float)
        self.speed,self.config = float(speed),config
        if self.centers.shape!=(2,2) or self.directions.shape!=(2,2):
            raise ValueError('Need two centers and two input directions.')
        if not np.isfinite(self.centers).all() or not np.isfinite(self.directions).all():
            raise ValueError('Probe centers and directions must be finite.')
        if not np.isfinite(speed) or speed<0 or np.any(np.linalg.norm(self.directions,axis=1)>1+1e-12):
            raise ValueError('Need finite nonnegative speed and directions of norm at most one.')
        if not 0<config.radius<n/4 or config.duration<1 or config.directional_gradient_cap<=0:
            raise ValueError('Invalid probe support, duration or gradient cap.')
        if np.linalg.norm(delta(self.centers[1],self.centers[0],n))<=2*config.radius:
            raise ValueError('Probe disks must be disjoint.')
        y,x = np.indices((n,n));points = np.stack((x,y),axis=-1)
        r = np.linalg.norm(delta(points[...,None,:],self.centers,n),axis=-1)
        self.windows = np.where(r<config.radius,.5*(1+np.cos(np.pi*np.minimum(r/config.radius,1))),0.)
        self.support = np.any(self.windows>0,axis=-1)

    def envelope(self,index):
        if not 0<=index<self.config.duration:return 0.
        return float(np.sin(np.pi*(index+.5)/self.config.duration)**2)

    def torque(self,theta,dt,index):
        if dt<=0:raise ValueError('dt must be positive.')
        envelope = self.envelope(index)
        if envelope==0 or self.speed==0:return np.zeros_like(theta)
        projected = np.einsum('...d,kd->...k',phase_gradient(theta),self.directions)
        projected = np.clip(projected,-self.config.directional_gradient_cap,self.config.directional_gradient_cap)
        return -(self.speed/dt)*envelope*np.sum(self.windows*projected,axis=-1)


def step_with_probe(adapter,state,probe,index):
    """The extra torque is subject to native compression locking, without compensation."""
    if index>=probe.config.duration or index<0 or probe.speed==0:
        adapter.advance(state,1)
        return dict(peak_external_angle_increment=0.,external_angle_increment_l1=0.)
    observed = {}

    def rule(current,params,extra):
        torque = probe.torque(current.theta,current.dt,index)
        increment = current.dt*(1-params.lock_strength*current.C)*torque
        observed.update(peak_external_angle_increment=float(np.max(np.abs(increment))),
                        external_angle_increment_l1=float(np.sum(np.abs(increment))))
        return {'torque':torque}

    step(state,adapter.params,adapter.rules+(rule,),post=locking_postprocess)
    return observed
