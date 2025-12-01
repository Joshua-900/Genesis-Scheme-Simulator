#src/genesis_scheme/algebra_2d.py

from dataclasses import dataclass
import numpy as np

@dataclass
class UnityState2D:
	s: np.ndarray  # shape (2,)
	t: float       # tension (kept constant in this visual mode)

RADIUS = 2.0
T_VISUAL = 1.0      # fixed tension for visualization

def _normalize_to_radius(v: np.ndarray, r: float) -> np.ndarray:
	norm = float(np.linalg.norm(v))
	if norm < 1e-8:
		return np.array([r, 0.0], dtype=float)
	return v * (r / norm)

def F(s: np.ndarray, t: float) -> np.ndarray:
	"""
	Form-Capacity (stabilizer):
	here: a mild smoothing / identity-like behavior (holds shape).
	"""
	# very light smoothing (can tweak)
	return 0.98 * s

def A(s: np.ndarray, t: float) -> np.ndarray:
	"""
	Force-Activation (activator):
	here: pure rotation on the circle + tiny wobble.
	"""
	# constant rotation angle set by t
	theta = 0.3 * t
	rot = np.array([
		[np.cos(theta), -np.sin(theta)],
		[np.sin(theta),  np.cos(theta)],
	])

	# small orthogonal push to avoid trivially repeating paths
	wobble = 0.02 * np.array([-s[1], s[0]])

	return rot @ s + wobble

def step2d(unity: UnityState2D) -> UnityState2D:
	"""
	One Unity -> Duality -> Recombination step in 2D (visual mode).

	- Use fixed tension T_VISUAL.
	- Combine F and A, then project back to a circle.
	"""
	s, _ = unity.s, unity.t
	t = T_VISUAL

	Fs = F(s, t)
	As = A(s, t)

	# symmetric mutual action of form and force
	s_next = 0.5 * (Fs + As)

	# keep motion on a fixed-radius circle
	s_next = _normalize_to_radius(s_next, RADIUS)

	return UnityState2D(s=s_next, t=t)