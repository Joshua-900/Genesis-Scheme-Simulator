#genesis_signature.py

import numpy as np
from dataclasses import dataclass

@dataclass
class TensionSignature:
    mean: float
    std: float

def tension_signature(T_series, tail_min: int = 2000,
tail_fraction: float = 0.2) -> TensionSignature:
    """
    Given a list/array of T(t), return the mean & std of the tail.
    This is our candidate 'Genesis Tension Invariant'.
    """
    T_arr = np.asarray(T_series, dtype=float)
    if T_arr.size == 0:
        return TensionSignature(mean=float("nan"), std=float("nan"))

    # how much of the tail to use
    tail = max(tail_min, int(len(T_arr) * tail_fraction))
    tail = min(tail, len(T_arr))

    T_tail = T_arr[-tail:]
    return TensionSignature(
        mean=float(T_tail.mean()),
        std=float(T_tail.std())
    )