import numpy as np

def compression_rule(state, params, extra):
	# use grad from alignment
	grad = extra.get("grad_align", 0.0)

	# ----- tension -----
	gamma_field = params.gamma     # relaxed later
	state.tau = (1.0 - params.decay_tau) * state.tau + gamma_field * grad

	# ----- geometry -----
	state.ux = (1.0 - params.geom_decay) * state.ux + params.kappa * state.tau * np.cos(state.theta)
	state.uy = (1.0 - params.geom_decay) * state.uy + params.kappa * state.tau * np.sin(state.theta)

	# ----- compression from deformation -----
	ux, uy = state.ux, state.uy
	ux_x = np.roll(ux, -1, axis=1) - ux
	ux_y = np.roll(ux, -1, axis=0) - ux
	uy_x = np.roll(uy, -1, axis=1) - uy
	uy_y = np.roll(uy, -1, axis=0) - uy

	detF = (1.0 + ux_x) * (1.0 + uy_y) - ux_y * uy_x
	C = np.exp(-(detF * detF) / (params.sigma_c2 + 1e-8))
	state.C = np.clip(C, 0.0, 1.0)

	# save for relaxation & curvature
	extra["detF"] = detF
	extra["C"]    = state.C

	# slight torque from tension if you want:
	torque = 0.1 * state.tau
	return {"torque": torque}