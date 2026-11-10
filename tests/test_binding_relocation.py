"""Check relocation topology, transported core state and interpolation errors."""
import unittest

import numpy as np

from src.genesis_binding.relocation import Relocation, arms, grid, inspect, relocate, sample
from src.genesis_audit.analysis import winding


def pair_state(n=40):
    points = grid(n)
    # Compact interior pair, avoiding the torus seam in the calibration support.
    pair = np.array([[12.5,16.5],[24.5,16.5]])
    z = points[...,0]+1j*points[...,1]
    theta = (np.angle(z-(pair[0,0]+1j*pair[0,1]))-np.angle(z-(pair[1,0]+1j*pair[1,1])))%(2*np.pi)
    rng = np.random.default_rng(2)
    return dict(theta=theta,tau=.5+.01*rng.random((n,n)),ux=.2+.01*rng.random((n,n)),
        uy=.3+.01*rng.random((n,n)),C=.2+.01*rng.random((n,n))),pair


class RelocationTests(unittest.TestCase):
    def test_periodic_sampler_copies_exact_integer_translations(self):
        rng = np.random.default_rng(3)
        values = rng.random((12,12))+1j*rng.random((12,12))
        coordinates = grid(12)+[1,-2]
        np.testing.assert_array_equal(sample(values,coordinates),np.roll(values,(2,-1),(0,1)))

    def test_identity_is_exact_for_every_field(self):
        state,pair = pair_state()
        out,back,info = relocate(state,pair,np.zeros((2,2)))
        for key in state:
            np.testing.assert_array_equal(state[key],out[key])
            np.testing.assert_array_equal(state[key],back[key])
        self.assertTrue(inspect(state,out,back,pair,np.zeros((2,2)),info)['passes'])

    def test_stretch_compress_translation_move_only_expected_charges(self):
        state,pair = pair_state()
        original = {k:v.copy() for k,v in state.items()}
        for name,shifts in arms(pair,40,Relocation()).items():
            with self.subTest(name=name):
                out,back,info = relocate(state,pair,shifts)
                result = inspect(state,out,back,pair,shifts,info)
                self.assertTrue(result['tests']['entire_winding_map_matches_expected'])
                self.assertTrue(result['tests']['protected_core_values_transported'])
                self.assertTrue(result['tests']['off_support_exact'])
                self.assertTrue(result['tests']['fresh_tracker_assignments_unique'])
                self.assertLess(result['inverse_residual'],1e-10)
                self.assertFalse(result['old_ids_inherited'])
        for key in state:np.testing.assert_array_equal(state[key],original[key])

    def test_periodic_relocation_transports_a_core_across_seam(self):
        state,pair = pair_state()
        for key in state:state[key]=np.roll(state[key],-13,axis=1)
        pair[:,0]=(pair[:,0]-13)%40
        shifts = np.array([[1.,0.],[1.,0.]])
        out,back,info = relocate(state,pair,shifts)
        result = inspect(state,out,back,pair,shifts,info)
        self.assertTrue(result['tests']['entire_winding_map_matches_expected'])
        self.assertTrue(result['tests']['protected_core_values_transported'])
        self.assertTrue(result['tests']['off_support_exact'])

    def test_roundtrip_detects_loss_of_a_sharp_retained_field(self):
        state,pair = pair_state()
        state['C'][:]=0
        state['C'][16,15]=1
        shifts = arms(pair,40,Relocation())['translate_plus']
        out,back,info = relocate(state,pair,shifts)
        result = inspect(state,out,back,pair,shifts,info)
        self.assertGreater(result['roundtrip_errors']['C_relative_l2'],.1)
        self.assertTrue(result['tests']['entire_winding_map_matches_expected'])

    def test_rejects_overlapping_supports_and_noncontractive_map(self):
        state,pair = pair_state()
        with self.assertRaisesRegex(ValueError,'disjoint'):
            relocate(state,np.array([[12.5,16.5],[16.5,16.5]]),np.ones((2,2)))
        with self.assertRaisesRegex(ValueError,'bound'):
            relocate(state,pair,np.array([[2.,0.],[2.,0.]]))


if __name__=='__main__':unittest.main()
