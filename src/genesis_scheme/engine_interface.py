# src/genesis_scheme/engine_interface.py
#
# Defines the pluggable engine protocol. Any engine that conforms to this
# interface can be swapped in by scripts or the launcher without rewriting
# simulation logic.
#
# Engines that can't conform (e.g., they have fundamentally different
# state representations) simply don't register — no forcing.

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class GenesisEngine(Protocol):
    """Minimal contract every pluggable engine must satisfy."""

    @property
    def name(self) -> str:
        """Human-readable engine name (e.g. 'Genesis Grid')."""
        ...

    @property
    def description(self) -> str:
        """One-liner describing what this engine does."""
        ...

    @property
    def created(self) -> str:
        """ISO-ish date string for ordering (newest = preferred)."""
        ...

    def create_state(self, **kwargs: Any) -> Any:
        """Initialize and return the engine's simulation state."""
        ...

    def step(self, state: Any, **kwargs: Any) -> Any:
        """Advance the simulation by one timestep. Returns updated state."""
        ...
