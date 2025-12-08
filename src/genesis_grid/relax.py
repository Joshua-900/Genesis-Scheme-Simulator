
from backend import xp
def relaxation_rule(state, params, extra):
    C = extra.get("C", state.C)

    # soften gains
    gamma_soft_field = params.gamma * (1.0 - params.gamma_soft * C)
    kappa_soft_field = params.kappa * (1.0 - params.kappa_soft * C)

    # reuse grad from alignment
    grad = extra.get("grad_align", 0.0)
    state.tau = (1.0 - params.decay_tau) * state.tau + gamma_soft_field * grad

    # geometry with softened kappa
    state.ux = (1.0 - params.geom_decay) * state.ux + kappa_soft_field * state.tau * xp.cos(state.theta)
    state.uy = (1.0 - params.geom_decay) * state.uy + kappa_soft_field * state.tau * xp.sin(state.theta)

    # relaxation of geometry in highly compressed zones
    state.ux *= (1.0 - params.relax_geom * C)
    state.uy *= (1.0 - params.relax_geom * C)

    # tiny angular diffusion
    theta = state.theta
    theta_lap = (xp.roll(theta, -1, 0) + xp.roll(theta, 1, 0) +
                 xp.roll(theta, -1, 1) + xp.roll(theta, 1, 1) -
                 4.0 * theta)
    diff_term = params.theta_diff * theta_lap

    return {"torque": diff_term}