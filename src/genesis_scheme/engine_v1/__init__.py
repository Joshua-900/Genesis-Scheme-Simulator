# src/genesis_scheme/engine_v1 — two-field reaction-diffusion engine
#
# Gray-Scott base with Genesis tension feedback.
# Supports multiple parameter regimes (worms, spots, etc.)

from .field2 import Field2
from .ops_genesis import step_genesis, compute_tension
from .ops_grayscott import step_gs, step_gs_genesis
from .tension import tension_norm
