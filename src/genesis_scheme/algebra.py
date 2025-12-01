#src/genesis_scheme/algebra.py

from dataclasses import dataclass

@dataclass
class UnityState:
    """
    Represents a single 'unity' in the toy model:
    - s: state of the world (scalar for now)
    - t: tension (latent asymmetry)
    """
    s: float
    t: float

def F(s: float, t: float) -> float:
    """
    Form-Capacity mode (stabilizer):
    pulls the state inward / contracts it by tension.
    """
    return s * (1.0 - t)

def A(s: float, t: float) -> float:
    """
    Force-Activation mode (activator):
    pushes the state outward / adds activation proportional to tension.
    """
    return s + t

def step(unity: UnityState) -> UnityState:
    """
    One full Unity -> Duality -> Recombination step.

    1) Expression: derive dual modes F and A acting on current state s, tension t.
    2) Recombination:
        - new tension = disagreement between F(s) and A(s)
        - new state   = symmetric blend of F(A(s)) and A(F(s))

    Returns a new UnityState (s', t').
    """
    s, t = unity.s, unity.t

    # Dual expression
    Fs = F(s, t)
    As = A(s, t)

    # Recompute next tension from disagreement
    t_next = abs(As - Fs)

    # Recombination: symmetric mutual action
    s_next = 0.5 * (F(As, t) + A(Fs, t))

    return UnityState(s=s_next, t=t_next)