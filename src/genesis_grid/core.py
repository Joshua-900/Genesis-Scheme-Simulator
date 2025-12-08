
from backend import xp

class GenesisState:
    def __init__(self, N, dt):
        self.N  = N
        self.dt = dt

        self.theta = xp.random.rand(N, N) * 2 * xp.pi
        self.tau   = xp.zeros((N, N))
        self.ux    = xp.zeros((N, N))
        self.uy    = xp.zeros((N, N))
        self.C     = xp.zeros((N, N))   # compression field

        x = xp.arange(N)
        y = xp.arange(N)
        self.X, self.Y = xp.meshgrid(x, y)

class GenesisParams:
    """Things driven by sliders live here."""
    def __init__(self):
        self.alpha = 0.4   # alignment
        self.gamma = 0.05  # tension gain
        self.kappa = 0.50 # geometry
        self.phase = 0.08
        self.dipole = 0.6
        self.triads = 1.3
        self.curv   = 0.03

        # relaxation knobs
        self.gamma_soft = 0.7
        self.kappa_soft = 0.5
        self.curv_soft  = 0.8
        self.relax_geom = 0.03
        self.theta_diff = 0.002

        # housekeeping
        self.decay_tau  = 0.02
        self.geom_decay = 0.05
        self.sigma_c2   = 0.15 ** 2

# ---------- helper: angle_diff ----------

def angle_diff(a, b):
    d = a - b
    return (d + xp.pi) % (2*xp.pi) - xp.pi

# ---------- step() orchestrates all rules ----------

def step(state: GenesisState, params: GenesisParams, rules):
    """
    rules: list of callables(state, params) -> dict of contributions
    Each rule can mutate state and/or return a torque term.
    """

    N  = state.N
    dt = state.dt

    # store contributions here
    torque_total = xp.zeros_like(state.theta)
    extra = {}  # for intermediate fields if rules want to share

    for rule in rules:
        out = rule(state, params, extra)
        if out is None:
            continue
        # convention: each rule returns {"torque": ..., "extra": {...optional...}}
        if "torque" in out:
            torque_total += out["torque"]
        if "extra" in out:
            extra.update(out["extra"])

    # final theta update
    state.theta = (state.theta + dt * torque_total) % (2 * xp.pi)