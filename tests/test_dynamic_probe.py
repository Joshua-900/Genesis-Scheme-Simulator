"""Verify probe intervention, native-state update and exact removal."""
import copy
import unittest

import numpy as np

from src.genesis_audit.v1_adapter import FIELDS,V1Adapter
from src.genesis_binding.dynamic_probe import AngularProbe,ProbeConfig,phase_gradient,step_with_probe


class DynamicProbeTests(unittest.TestCase):
    def setUp(self):
        self.adapter=V1Adapter()
        self.state=self.adapter.create(32,7)
        self.centers=np.array([[9.5,12.5],[21.5,12.5]])

    def make_probe(self,speed=.1):
        return AngularProbe(32,self.centers,np.array([[1.,0.],[1.,0.]]),speed)

    def test_torque_is_local_rotation_invariant_and_changes_no_fields(self):
        p=self.make_probe();before=self.adapter.snapshot(self.state)
        torque=p.torque(self.state.theta,self.state.dt,40)
        np.testing.assert_array_equal(torque[~p.support],np.zeros(np.count_nonzero(~p.support)))
        np.testing.assert_allclose(torque,p.torque((self.state.theta+1.1)%(2*np.pi),self.state.dt,40),atol=1e-12)
        for key in FIELDS:np.testing.assert_array_equal(getattr(self.state,key),before[key])
        self.assertLessEqual(np.max(np.abs(torque))*self.state.dt,.1)

    def test_sign_on_a_smooth_ramp_is_translation_sign(self):
        y,x=np.indices((32,32));theta=.1*x+.2*y
        p=self.make_probe()
        torque=p.torque(theta,.05,40)
        self.assertLess(torque[12,9],0)
        np.testing.assert_allclose(phase_gradient(theta)[12,9],[.1,.2],atol=1e-14)
        reverse=AngularProbe(32,self.centers,-p.directions,.1)
        np.testing.assert_allclose(torque,-reverse.torque(theta,.05,40),atol=1e-14)

    def test_native_retained_field_updates_and_locking_are_preserved(self):
        rng=np.random.default_rng(11)
        for key in ('tau','ux','uy'):setattr(self.state,key,rng.uniform(.01,.2,(32,32)))
        native=copy.deepcopy(self.state);probed=copy.deepcopy(self.state)
        p=self.make_probe();torque=p.torque(self.state.theta,.05,40)
        self.adapter.advance(native,1)
        diagnostic=step_with_probe(self.adapter,probed,p,40)
        for key in ('tau','ux','uy','C'):
            np.testing.assert_array_equal(getattr(native,key),getattr(probed,key))
        expected=(native.theta+.05*(1-self.adapter.params.lock_strength*native.C)*torque)%(2*np.pi)
        np.testing.assert_allclose(probed.theta,expected,atol=2e-15,rtol=0)
        self.assertLessEqual(diagnostic['peak_external_angle_increment'],.1)

    def test_zero_speed_matches_native_trajectory_bitwise(self):
        native=copy.deepcopy(self.state);probed=copy.deepcopy(self.state);p=self.make_probe(0.)
        for tick in range(12):
            self.adapter.advance(native,1);step_with_probe(self.adapter,probed,p,tick)
        for key in FIELDS:np.testing.assert_array_equal(getattr(native,key),getattr(probed,key))

    def test_cutoff_matches_native_from_the_actual_perturbed_state(self):
        p=self.make_probe()
        for tick in range(5):step_with_probe(self.adapter,self.state,p,tick)
        reference=copy.deepcopy(self.state);self.adapter.advance(reference,1)
        result=step_with_probe(self.adapter,self.state,p,p.config.duration)
        for key in FIELDS:np.testing.assert_array_equal(getattr(reference,key),getattr(self.state,key))
        self.assertEqual(result['peak_external_angle_increment'],0.)
        np.testing.assert_array_equal(p.torque(self.state.theta,.05,80),np.zeros((32,32)))
        self.assertEqual(p.envelope(-1),0.)

    def test_periodic_support_and_invalid_overlapping_disks(self):
        centers=np.array([[.5,10.5],[14.5,10.5]])
        p=AngularProbe(32,centers,np.array([[1.,0.],[1.,0.]]),.1)
        self.assertTrue(p.support[10,31])
        with self.assertRaisesRegex(ValueError,'disjoint'):
            AngularProbe(32,np.array([[1.5,10.5],[3.5,10.5]]),np.ones((2,2))/2,.1)


if __name__=='__main__':unittest.main()
