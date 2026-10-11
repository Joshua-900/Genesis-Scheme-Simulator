# src/genesis_scheme — GenesisScheme core package
#
# Exports the scalar algebra primitives and the engine registry.

from .algebra import UnityState, step
from .engine_interface import GenesisEngine
from . import engine_registry

# Auto-register all available engines
from .engine.adapter import EngineV0
from .engine_v1.adapter import EngineV1

engine_registry.register(EngineV0())
engine_registry.register(EngineV1())

# genesis_grid lives outside this package (src/genesis_grid/), so we
# register it with a lazy try/except to avoid a hard dependency.
try:
    from src.genesis_grid.adapter import GenesisGridEngine
    engine_registry.register(GenesisGridEngine())
except ImportError:
    pass

try:
    from src.genesis_v2.adapter import GenesisV2Engine
    engine_registry.register(GenesisV2Engine())
except ImportError:
    pass

try:
    from src.genesis_v2_beta.adapter import GenesisV2BetaEngine
    engine_registry.register(GenesisV2BetaEngine())
except ImportError:
    pass

try:
    from src.genesis_v2_gamma.adapter import GenesisV2GammaEngine
    engine_registry.register(GenesisV2GammaEngine())
except ImportError:
    pass
