import numpy as np

class GenesisState:
    def __init__(self, N, dt):
        self.N  = N
        self.dt = dt

        self.theta = np.random.rand(N, N) * 2 * np.pi
        self.tau   = np.zeros((N, N))
        self.ux    = np.zeros((N, N))
        self.uy    = np.zeros((N, N))
        self.C     = np.zeros((N, N))   # compression field

        x = np.arange(N)
        y = np.arange(N)
        self.X, self.Y = np.meshgrid(x, y)

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
    return (d + np.pi) % (2*np.pi) - np.pi

# ---------- step() orchestrates all rules ----------

def step(state: GenesisState, params: GenesisParams, rules):
    """
    rules: list of callables(state, params) -> dict of contributions
    Each rule can mutate state and/or return a torque term.
    """

    N  = state.N
    dt = state.dt

    # store contributions here
    torque_total = np.zeros_like(state.theta)
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
    state.theta = (state.theta + dt * torque_total) % (2 * np.pi)