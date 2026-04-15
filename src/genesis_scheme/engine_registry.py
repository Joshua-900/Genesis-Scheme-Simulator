# src/genesis_scheme/engine_registry.py
#
# Central registry for discovering available engines.
# Engines register themselves; consumers query the registry.

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .engine_interface import GenesisEngine

_ENGINES: dict[str, "GenesisEngine"] = {}


def register(engine: "GenesisEngine") -> None:
    """Add an engine instance to the registry."""
    _ENGINES[engine.name] = engine


def get(name: str) -> "GenesisEngine":
    """Retrieve a registered engine by name. Raises KeyError if not found."""
    return _ENGINES[name]


def list_engines() -> list["GenesisEngine"]:
    """Return all registered engines, sorted newest-first by created date."""
    return sorted(_ENGINES.values(), key=lambda e: e.created, reverse=True)


def names() -> list[str]:
    """Return registered engine names, sorted newest-first."""
    return [e.name for e in list_engines()]
