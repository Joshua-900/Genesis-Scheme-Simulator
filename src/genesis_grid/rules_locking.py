# rules_locking.py
#
# Compression locking — the emergence mechanism.
#
# In regions where the grid has folded (C ≈ 1), this rule:
#   1. Freezes theta updates (scales total torque toward zero)
#   2. Amplifies phase-well and triad torques in compressed cores
#      so locked regions crystallize into discrete orientations
#
# This creates bistability:
#   - Fluid regions (low C): alignment dominates, smooth dynamics
#   - Frozen cores (high C): phase wells + triads lock in, structure persists

from .backend import xp


def locking_postprocess(torque_total, state, params, extra):
    """
    Post-processing step applied to the summed torque BEFORE the theta update.

    Unlike regular rules (which return additive torque), this modifies the
    total torque in-place based on compression field C.

    Returns the modified torque_total.
    """
    C = extra.get("C", state.C)

    if params.lock_strength == 0.0:
        return torque_total

    # --- Amplify phase and triad contributions in compressed cores ---
    # These are stored in extra by their respective rules
    phase_torque = extra.get("phase_torque", None)
    tri_torque = extra.get("tri_torque", None)

    if phase_torque is not None and params.phase_lock_gain > 0.0:
        # Add the amplified portion (original is already in torque_total)
        torque_total = torque_total + params.phase_lock_gain * C * phase_torque

    if tri_torque is not None and params.tri_lock_gain > 0.0:
        torque_total = torque_total + params.tri_lock_gain * C * tri_torque

    # --- Freeze theta in compressed regions ---
    # Scale total torque toward zero where C is high
    torque_total = torque_total * (1.0 - params.lock_strength * C)

    return torque_total
