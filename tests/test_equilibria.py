"""Equilibrium algebra and full active-state differentiation checks."""

from __future__ import annotations

import unittest
import numpy as np

from src.genesis_audit.v1_adapter import V1Adapter
from src.genesis_equilibria.equations import (
    active_from_reduced, active_jacobian, active_map, alignment,
    normalized_difference, reduced_fields, reduced_jacobian, reduced_residual,
)
from src.genesis_equilibria.search import Config, accepted_state


class EquilibriumTests(unittest.TestCase):
    def test_batched_active_map_matches_preserved_source(self):
        rng = np.random.default_rng(4)
        for n in (4, 8):
            for beta in (0., .04):
                for lock in (0., .96):
                    adapter = V1Adapter()
                    adapter.params.curv, adapter.params.lock_strength = beta, lock
                    x = np.stack((rng.uniform(-np.pi, np.pi, (n,n)), rng.uniform(0, .3, (n,n)), rng.normal(0,.1,(n,n)), rng.normal(0,.1,(n,n)))).ravel()
                    state = adapter.create(n, 1)
                    for key, field in zip(("theta", "tau", "ux", "uy"), x.reshape(4,n,n)):
                        setattr(state, key, field.copy())
                    adapter.advance(state, 1)
                    expected = active_map(np.stack((x,x)), n, adapter.params)
                    actual = np.stack((state.theta,state.tau,state.ux,state.uy))
                    difference = expected[0].reshape(4,n,n)-actual
                    difference[0]=(difference[0]+np.pi)%(2*np.pi)-np.pi
                    self.assertLess(np.max(np.abs(difference)),1e-12)
                    np.testing.assert_array_equal(expected[0],expected[1])

    def test_eliminated_tension_is_exact_equilibrium_recurrence(self):
        p=V1Adapter().params;n=4
        x=np.random.default_rng(7).normal(size=3*n*n)
        theta,tau,ux,uy=reduced_fields(x,n,p)
        np.testing.assert_allclose((1-p.decay_tau)*tau+p.gamma*np.abs(alignment(theta)),tau,rtol=0,atol=1e-15)

    def test_reduced_residual_does_not_reward_locking(self):
        p=V1Adapter().params;n=4
        x=np.random.default_rng(8).normal(size=3*n*n)
        locked=reduced_residual(x,n,p)
        p.lock_strength=0
        np.testing.assert_array_equal(locked,reduced_residual(x,n,p))

    def test_solver_jacobian_matches_scalar_differences(self):
        p=V1Adapter().params;n=4
        x=np.random.default_rng(10).normal(0,.3,size=3*n*n)
        j=reduced_jacobian(x,n,p)
        for column in (0,12,20,40):
            h=1e-6*max(1,abs(x[column]));y=x.copy();y[column]+=h
            expected=(reduced_residual(y,n,p)-reduced_residual(x,n,p))/h
            np.testing.assert_allclose(j[:,column],expected,rtol=1e-10,atol=1e-10)

    def test_uniform_control_passes_independent_source_acceptance(self):
        n=4;p=V1Adapter().params
        result=accepted_state(np.zeros(3*n*n),n,p,Config())
        self.assertTrue(result['accepted'])
        self.assertFalse(result['interesting_nonzero_alignment'])

    def test_exact_periodic_tiling_preserves_local_map(self):
        n=4;p=V1Adapter().params
        x=np.random.default_rng(13).normal(0,.1,size=4*n*n)
        tiled=np.tile(x.reshape(4,n,n),(1,2,2)).ravel()
        target=np.tile(active_map(x,n,p).reshape(4,n,n),(1,2,2)).ravel()
        np.testing.assert_allclose(active_map(tiled,2*n,p),target,rtol=0,atol=1e-15)

    def test_active_spectrum_detects_unstable_checkerboard_reference(self):
        n=4;p=V1Adapter().params;p.curv=0
        rows,cols=np.indices((n,n));theta=np.pi*((rows+cols)%2)
        reduced=np.stack((theta,np.zeros_like(theta),np.zeros_like(theta))).ravel()
        active=active_from_reduced(reduced,n,p)
        radius=np.max(np.abs(np.linalg.eigvals(active_jacobian(active,n,p,1e-6))))
        self.assertGreater(radius,1.1)

    def test_distance_respects_circular_angle(self):
        n=4;x=np.zeros(4*n*n);y=x.copy();y[:n*n]=2*np.pi
        self.assertLess(normalized_difference(x,y,n),1e-14)


if __name__=='__main__':
    unittest.main()
