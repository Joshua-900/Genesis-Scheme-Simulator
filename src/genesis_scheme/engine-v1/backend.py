#backend.py
#Simple switch between NumPy (CPU) and CuPy (GPU)

# try:
# 	import cupy as xp   # GPU path (requires CUDA + CuPy installed)
# 	GPU = True
# except ImportError:
# 	import numpy as xp  # Fallback to CPU
# 	GPU = False