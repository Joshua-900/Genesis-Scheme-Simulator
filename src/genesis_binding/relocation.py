"""Compact periodic relocation of angle and retained state, without evolution.

This is a prepared counterfactual, not a physical coordinate transformation.
Vector components are transported as stored lab-frame values. The map is
identity outside radius-three disks and a rigid shift inside radius one.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from src.genesis_audit.analysis import winding
from src.genesis_motion.observations import PeriodicTracker, delta

FIELDS = ('theta', 'tau', 'ux', 'uy', 'C')


@dataclass(frozen=True)
class Relocation:
    inner: float = 1.
    outer: float = 3.
    magnitude: float = 1.
    inverse_tolerance: float = 1e-12
    inverse_iterations: int = 512
    minimum_phase_norm: float = .2
    coordinate_tolerance: float = 1e-10
    core_value_tolerance: float = 1e-10
    phase_roundtrip_rms_limit: float = .35
    tau_roundtrip_relative_limit: float = .25
    displacement_roundtrip_relative_limit: float = .25
    compression_roundtrip_relative_limit: float = .50


def arms(pair, n, config):
    """Dominant Cartesian pair axis, so the requested shifts are grid-resolved.

    Relative arms move both constituents by one cell in opposite directions;
    translation arms move both by one cell in the same direction.
    """
    vector = delta(pair[1], pair[0], n)
    axis = int(np.argmax(np.abs(vector)))
    direction = np.zeros(2)
    direction[axis] = np.sign(vector[axis])*config.magnitude
    return {
        'sham':np.zeros((2,2)),
        'stretch':np.array([-direction,direction]),
        'compress':np.array([direction,-direction]),
        'translate_plus':np.array([direction,direction]),
        'translate_minus':np.array([-direction,-direction]),
    }


def grid(n):
    rows,cols = np.indices((n,n))
    return np.stack((cols,rows),axis=-1).astype(float)


def weights(coordinates, centers, n, config):
    radii = np.linalg.norm(delta(coordinates[...,None,:],centers,n),axis=-1)
    z = np.clip((radii-config.inner)/(config.outer-config.inner),0,1)
    return .5*(1+np.cos(np.pi*z))


def deformation(coordinates, centers, shifts, n, config):
    return np.einsum('...k,kd->...d',weights(coordinates,centers,n,config),shifts)


def sample(values, coordinates):
    """Periodic bilinear interpolation, with exact nodal copying at integers."""
    n = len(values)
    x,y = coordinates[...,0],coordinates[...,1]
    x0,y0 = np.floor(x).astype(int),np.floor(y).astype(int)
    fx,fy = x-x0,y-y0
    return ((1-fx)*(1-fy)*values[y0%n,x0%n]
            +fx*(1-fy)*values[y0%n,(x0+1)%n]
            +(1-fx)*fy*values[(y0+1)%n,x0%n]
            +fx*fy*values[(y0+1)%n,(x0+1)%n])


def sampled_fields(state, coordinates, active):
    out = {key:value.copy() for key,value in state.items()}
    phase = sample(np.exp(1j*state['theta']),coordinates)
    out['theta'][active] = np.angle(phase[active])%(2*np.pi)
    for key in FIELDS[1:]:out[key][active] = sample(state[key],coordinates)[active]
    return out, np.abs(phase)


def relocate(state, pair, shifts, config=Relocation()):
    n = len(state['theta'])
    pair,shifts = np.asarray(pair,dtype=float),np.asarray(shifts,dtype=float)
    if pair.shape!=(2,2) or shifts.shape!=(2,2) or not np.isfinite(pair).all() or not np.isfinite(shifts).all():
        raise ValueError('Need two finite centers and two finite displacement vectors.')
    if not (0 < config.inner < config.outer < n/4):
        raise ValueError('Need 0 < inner < outer < N/4.')
    if np.linalg.norm(delta(pair[1],pair[0],n)) <= 2*config.outer:
        raise ValueError('Relocation disks must be disjoint.')
    bound = float(np.linalg.norm(shifts,axis=1).max()*np.pi/(2*(config.outer-config.inner)))
    if bound>=1:
        raise ValueError('The declared contraction/injectivity bound must be below one.')
    if not all(state[key].shape==(n,n) and np.isfinite(state[key]).all() for key in FIELDS):
        raise ValueError('Invalid input fields.')
    destination = grid(n)
    active = np.any(weights(destination,pair,n,config)>0,axis=-1)
    inverse = destination.copy()
    error = 0.
    iterations = 0
    for iterations in range(1,config.inverse_iterations+1):
        following = destination-deformation(inverse,pair,shifts,n,config)
        error = float(np.max(np.abs(following-inverse)))
        inverse = following
        if error<=config.inverse_tolerance:break
    residual = float(np.max(np.abs(inverse+deformation(inverse,pair,shifts,n,config)-destination)))
    if np.all(shifts==0):
        # Identity is exact by construction, independently of angle conversion.
        out = {key:value.copy() for key,value in state.items()}
        phase_norm = np.ones((n,n))
    else:out,phase_norm = sampled_fields(state,inverse,active)
    forward = destination+deformation(destination,pair,shifts,n,config)
    if np.all(shifts==0):roundtrip = {key:value.copy() for key,value in out.items()}
    else:roundtrip,_ = sampled_fields(out,forward,active)
    return out,roundtrip,dict(active=active,inverse_iterations=iterations,
        inverse_step_error=error,inverse_residual=residual,lipschitz_bound=bound,
        determinant_lower_bound=1-bound,phase_norm_min=float(phase_norm[active].min()))


def relative_error(before, after, mask):
    return float(np.linalg.norm((after-before)[mask])/max(np.linalg.norm(before[mask]),1e-12))


def inspect(state, relocated, roundtrip, pair, shifts, info, config=Relocation()):
    n = len(state['theta'])
    active = info['active']
    original_charge = winding(state['theta'])
    expected_charge = original_charge.copy()
    source_signs = []
    for x,y in pair:
        source_signs.append(int(original_charge[int(y)%n,int(x)%n]))
        expected_charge[int(y)%n,int(x)%n] = 0
    expected_pair = (pair+shifts)%n
    for (x,y),sign in zip(expected_pair,source_signs):
        expected_charge[int(y)%n,int(x)%n] += sign
    measured_charge = winding(relocated['theta'])
    charge_exact = bool(np.array_equal(measured_charge,expected_charge))
    phase_change = np.abs(np.exp(1j*roundtrip['theta'])-np.exp(1j*state['theta']))
    phase_error = float(np.sqrt(np.mean(phase_change[active]**2)))
    geometry_before = np.stack((state['ux'],state['uy']),axis=-1)
    geometry_after = np.stack((roundtrip['ux'],roundtrip['uy']),axis=-1)
    errors = dict(theta_phasor_rms=phase_error,
        tau_relative_l2=relative_error(state['tau'],roundtrip['tau'],active),
        displacement_relative_l2=relative_error(geometry_before,geometry_after,active),
        C_relative_l2=relative_error(state['C'],roundtrip['C'],active))
    change = {key:dict(rms=float(np.sqrt(np.mean((np.angle(np.exp(1j*(relocated[key]-state[key]))) if key=='theta'
                  else relocated[key]-state[key])[active]**2))),
                  max_abs=float(np.max(np.abs(np.angle(np.exp(1j*(relocated[key]-state[key]))) if key=='theta'
                  else relocated[key]-state[key])))) for key in FIELDS}
    core_errors = {key:0. for key in FIELDS}
    # Protected plaquette corners must be copied along with each core.
    for center,shift in zip(pair,shifts):
        for ox,oy in ((-.5,-.5),(.5,-.5),(-.5,.5),(.5,.5)):
            x,y = center+[ox,oy]
            tx,ty = (np.array([x,y])+shift)%n
            if not np.allclose([tx,ty],np.rint([tx,ty]),atol=config.coordinate_tolerance,rtol=0):
                raise ValueError('Core-corner check needs integer grid displacements.')
            for key in FIELDS:
                a,b = state[key][int(y)%n,int(x)%n],relocated[key][int(round(ty))%n,int(round(tx))%n]
                difference = abs(np.angle(np.exp(1j*(b-a)))) if key=='theta' else abs(b-a)
                core_errors[key] = max(core_errors[key],float(difference))
    tracker = PeriodicTracker(n)
    tracker.update(relocated['theta'],0)
    assignments = []
    for position,sign in zip(expected_pair,source_signs):
        matches = [t.id for t in tracker.tracks.values() if t.charge==sign and np.linalg.norm(delta([t.x,t.y],position,n))<config.coordinate_tolerance]
        assignments.append(matches[0] if len(matches)==1 else None)
    tests = dict(source_pair_charges=source_signs==[1,-1],
        inverse_converged=info['inverse_residual']<=config.coordinate_tolerance,
        phase_interpolation_resolved=info['phase_norm_min']>=config.minimum_phase_norm,
        entire_winding_map_matches_expected=charge_exact,
        fresh_tracker_assignments_unique=all(t is not None for t in assignments) and len(set(assignments))==2,
        off_support_exact=all(np.array_equal(state[k][~active],relocated[k][~active]) for k in FIELDS),
        protected_core_values_transported=max(core_errors.values())<=config.core_value_tolerance,
        finite_fields=all(np.isfinite(relocated[k]).all() for k in FIELDS),
        nonnegative_tension=bool(np.min(relocated['tau'])>=0),
        compression_bounds=bool(np.min(relocated['C'])>=0 and np.max(relocated['C'])<=1),
        phase_roundtrip=errors['theta_phasor_rms']<=config.phase_roundtrip_rms_limit,
        tau_roundtrip=errors['tau_relative_l2']<=config.tau_roundtrip_relative_limit,
        displacement_roundtrip=errors['displacement_relative_l2']<=config.displacement_roundtrip_relative_limit,
        compression_roundtrip=errors['C_relative_l2']<=config.compression_roundtrip_relative_limit)
    before_vector = delta(pair[1],pair[0],n)
    after_vector = delta(expected_pair[1],expected_pair[0],n)
    return dict(passes=all(tests.values()),tests=tests,expected_pair=expected_pair.tolist(),
        measured_pair=expected_pair.tolist() if charge_exact else None,
        fresh_tracker_ids=assignments,old_ids_inherited=False,
        initial_separation=float(np.linalg.norm(before_vector)),
        relocated_separation=float(np.linalg.norm(after_vector)),
        relative_vector_change=(after_vector-before_vector).tolist(),
        center_displacement=np.mean(shifts,axis=0).tolist(),
        constituent_displacement_magnitudes=np.linalg.norm(shifts,axis=1).tolist(),
        roundtrip_errors=errors,protected_core_max_errors=core_errors,changes_within_support=change,
        forward_winding_mismatched_plaquettes=int(np.count_nonzero(measured_charge!=expected_charge)),
        **{key:value for key,value in info.items() if key!='active'})
