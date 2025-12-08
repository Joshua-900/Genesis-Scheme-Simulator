
from backend import xp

def compression_rule(state, params, extra):
	# use grad from alignment
	grad = extra.get("grad_align", 0.0)

	# ----- tension -----
	gamma_field = params.gamma     # relaxed later
	state.tau = (1.0 - params.decay_tau) * state.tau + gamma_field * grad

	# ----- geometry -----
	state.ux = (1.0 - params.geom_decay) * state.ux + params.kappa * state.tau * xp.cos(state.theta)
	state.uy = (1.0 - params.geom_decay) * state.uy + params.kappa * state.tau * xp.sin(state.theta)

	# ----- compression from deformation -----
	ux, uy = state.ux, state.uy
	ux_x = xp.roll(ux, -1, axis=1) - ux
	ux_y = xp.roll(ux, -1, axis=0) - ux
	uy_x = xp.roll(uy, -1, axis=1) - uy
	uy_y = xp.roll(uy, -1, axis=0) - uy

	detF = (1.0 + ux_x) * (1.0 + uy_y) - ux_y * uy_x
	C = xp.exp(-(detF * detF) / (params.sigma_c2 + 1e-8))
	state.C = xp.clip(C, 0.0, 1.0)

	# save for relaxation & curvature
	extra["detF"] = detF
	extra["C"]    = state.C

	# slight torque from tension if you want:
	torque = 0.1 * state.tau
	return {"torque": torque}