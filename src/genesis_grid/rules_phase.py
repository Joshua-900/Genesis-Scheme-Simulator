
from backend import xp

def phase_rule(state, params, extra):
	theta = state.theta
	phase_force = -params.phase * xp.sin(4.0 * theta)
	return {"torque": phase_force}