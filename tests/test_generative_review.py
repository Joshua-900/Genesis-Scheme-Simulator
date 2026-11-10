import unittest

import numpy as np

from src.genesis_gallery import legacy
from src.genesis_gallery.review import ORDER, advance, create, metrics, poke, theta_of


class GenerativeReviewTests(unittest.TestCase):
    def test_vectorized_recipe_matches_original_function(self):
        for n in (5, 8):
            for geometry in (True, False):
                with self.subTest(n=n, geometry=geometry):
                    rng = np.random.default_rng(19)
                    state = dict(theta=rng.uniform(0, 2*np.pi, (n,n)),
                                 tau=rng.uniform(0, .5, (n,n)),
                                 ux=rng.normal(0, .3, (n,n)), uy=rng.normal(0, .3, (n,n)))
                    original = [state[k].copy() for k in ('theta','tau','ux','uy')]
                    p = legacy.defaults()
                    if not geometry:
                        p.update(kappa0=0., curv0=0., shell_geom_gain=0.)
                    ref = legacy.reference(n)
                    ref.update(p)
                    args = [p[k] for k in ('alpha0','gamma0','kappa0','well0','dipole0','tri0','curv0')]
                    for _ in range(10):
                        result = ref['update_genesis'](*original, *args)
                        original = list(result[:4])
                        legacy.step(state, p)
                        for key, value in zip(('theta','tau','ux','uy','C'), (*result[:4], result[7])):
                            np.testing.assert_allclose(state[key], value, atol=2e-11, rtol=2e-11)

    def test_initial_angles_match_in_all_lanes_and_rng_is_preserved(self):
        theta = np.random.default_rng(1).uniform(0, 2*np.pi, (8,8))
        for name in ORDER:
            np.random.seed(812)
            expected = np.random.random(5)
            np.random.seed(812)
            state, _ = create(name, 8, 1, theta)
            np.testing.assert_array_equal(theta_of(state), theta)
            np.testing.assert_array_equal(np.random.random(5), expected)

    def test_phase_aligned_change_removes_global_rotation(self):
        theta = np.random.default_rng(4).uniform(0, 2*np.pi, (8,8))
        result = metrics(theta+.4, theta)
        self.assertLess(result['phase_aligned_interval_change'], 1e-14)
        self.assertGreater(result['raw_interval_change'], .3)

    def test_pulse_is_compact(self):
        state = {'theta':np.ones((32,32))}
        poke(state)
        y,x = np.indices((32,32))
        outside = (x-16)**2+(y-16)**2 >= 25
        np.testing.assert_array_equal(state['theta'][outside], np.ones(outside.sum()))
        self.assertAlmostEqual(state['theta'][16,16], 1+np.pi/2)

    def test_controls_do_not_generate_displacement(self):
        theta = np.random.default_rng(8).uniform(0, 2*np.pi, (8,8))
        for name in ('v1_no_geometry','legacy_no_geometry'):
            state,p = create(name,8,8,theta)
            advance(name,state,p,10)
            for key in ('ux','uy'):
                value = state[key] if isinstance(state,dict) else getattr(state,key)
                np.testing.assert_array_equal(value, np.zeros_like(value))


if __name__ == '__main__':
    unittest.main()
