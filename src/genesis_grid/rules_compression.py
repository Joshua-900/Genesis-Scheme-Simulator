
from .backend import xp

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
	# Central differences (symmetric — no directional bias from the grid)
	ux, uy = state.ux, state.uy
	ux_x = 0.5 * (xp.roll(ux, -1, axis=1) - xp.roll(ux, 1, axis=1))
	ux_y = 0.5 * (xp.roll(ux, -1, axis=0) - xp.roll(ux, 1, axis=0))
	uy_x = 0.5 * (xp.roll(uy, -1, axis=1) - xp.roll(uy, 1, axis=1))
	uy_y = 0.5 * (xp.roll(uy, -1, axis=0) - xp.roll(uy, 1, axis=0))

	detF = (1.0 + ux_x) * (1.0 + uy_y) - ux_y * uy_x
	C = xp.exp(-(detF * detF) / (params.sigma_c2 + 1e-8))
	state.C = xp.clip(C, 0.0, 1.0)

	# save for relaxation & curvature
	extra["detF"] = detF
	extra["C"]    = state.C

	# --- shell geometry: compression gradients push geometry outward ---
	# This sharpens boundaries around compressed cores
	if params.shell_geom_gain > 0.0:
		Cx = 0.5 * (xp.roll(state.C, -1, axis=1) - xp.roll(state.C, 1, axis=1))
		Cy = 0.5 * (xp.roll(state.C, -1, axis=0) - xp.roll(state.C, 1, axis=0))
		state.ux = state.ux + params.shell_geom_gain * Cx
		state.uy = state.uy + params.shell_geom_gain * Cy

	# slight torque from tension
	torque = 0.1 * state.tau
	return {"torque": torque}