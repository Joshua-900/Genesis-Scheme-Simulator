"""Gamma hypothesis: beta plus explicit edge-boundary permeability."""
from .core import GammaParams, GammaState, step
__all__ = ["GammaParams", "GammaState", "step"]
"""Boundary-forming gamma revision of the Genesis v2 experimental engine."""

from .core import GammaParams, GammaState, step
from src.genesis_v2_beta.core import summary

__all__ = ["GammaParams", "GammaState", "step", "summary"]
