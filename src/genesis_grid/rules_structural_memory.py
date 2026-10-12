"""Compression-gated structural-template memory for V1 object experiments."""

from .backend import xp


def structural_memory_rule(state, params, extra):
    if not (
        params.template_write_rate
        or params.template_decay
        or params.template_restore_gain
    ):
        return {"torque": 0.0}

    compression = extra.get("C", state.C)
    write = params.template_write_rate * compression
    state.memory_x = (1.0 - params.template_decay * state.dt) * state.memory_x + state.dt * write * (xp.cos(state.theta) - state.memory_x)
    state.memory_y = (1.0 - params.template_decay * state.dt) * state.memory_y + state.dt * write * (xp.sin(state.theta) - state.memory_y)
    memory_strength = xp.sqrt(state.memory_x * state.memory_x + state.memory_y * state.memory_y)
    memory_angle = xp.arctan2(state.memory_y, state.memory_x)
    extra["structural_memory_strength"] = memory_strength
    return {"torque": params.template_restore_gain * compression * memory_strength * xp.sin(memory_angle - state.theta)}
