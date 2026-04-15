#genesis_logging.py

import numpy as np
from pathlib import Path

def save_tension_csv(path: str | Path, times, T_series) -> None:
	"""
	Save T(t) to a simple CSV: columns [t, T].
	"""
	path = Path(path)
	arr = np.column_stack([np.asarray(times, float),
						  np.asarray(T_series, float)])
	header = "t,T"
	np.savetxt(path, arr, delimiter=",", header=header, comments="")