import numpy as np

def phase_rule(state, params, extra):
	theta = state.theta
	phase_force = -params.phase * np.sin(4.0 * theta)
	return {"torque": phase_force}