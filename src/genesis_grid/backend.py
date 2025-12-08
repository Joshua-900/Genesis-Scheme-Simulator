#backend.py

import os

# Set USE_CUPY to True to use cupy, False to use numpy
USE_CUPY = os.environ.get('GENESIS_USE_CUPY', 'False').lower() in ('1', 'true', 'yes')

if USE_CUPY:
    try:
        import cupy as cp
        xp = cp
        def to_cpu(a):
            try:
                return cp.asnumpy(a)
            except Exception:
                return a
    except ImportError:
        import numpy as np
        xp = np
        def to_cpu(a):
            return a
else:
    import numpy as np
    xp = np
    def to_cpu(a):
        return a