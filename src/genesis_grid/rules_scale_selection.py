"""Optional compression-driven long-range inhibition for finite-scale structure.

Compression acts as the local activator already present in V1.  This rule adds
only the missing counterweight: a diffusing memory of compression that damps
stored tension where compression has persisted or spread.  Its parameters all
default to zero, so it cannot alter established V1 experiments accidentally.
"""

from .backend import xp


def _laplacian(field):
    return (
        xp.roll(field, -1, axis=0)
        + xp.roll(field, 1, axis=0)
        + xp.roll(field, -1, axis=1)
        + xp.roll(field, 1, axis=1)
        - 4.0 * field
    )


def scale_selection_rule(state, params, extra):
    if not (
        params.inhibitor_source
        or params.inhibitor_decay
        or params.inhibitor_diffusion
        or params.inhibitor_tension_damping
    ):
        return {"torque": 0.0}

    compression = extra.get("C", state.C)
    state.inhibitor = xp.maximum(
        0.0,
        state.inhibitor
        + state.dt
        * (
            params.inhibitor_source * compression
            - params.inhibitor_decay * state.inhibitor
            + params.inhibitor_diffusion * _laplacian(state.inhibitor)
        ),
    )
    if params.inhibitor_tension_damping:
        state.tau = state.tau / (1.0 + params.inhibitor_tension_damping * state.inhibitor)
    extra["inhibitor"] = state.inhibitor
    return {"torque": 0.0}
