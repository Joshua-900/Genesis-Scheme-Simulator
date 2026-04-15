# src/genesis_grid — modular rule-based orientation field engine
#
# Latest engine (Dec 2025 – present). Orientation field theta on an NxN grid
# with pluggable physics rules, each returning a torque contribution.

from .backend import xp, to_cpu
from .core import GenesisState, GenesisParams, step, angle_diff

from . import rules_alignment
from . import rules_phase
from . import rules_dipoles
from . import rules_triads
from . import rules_curvature
from . import rules_compression
from . import rules_locking
from . import relax
from . import rules_triads_relative
from . import diagnostics
