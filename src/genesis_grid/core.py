
from .backend import xp

class GenesisState:
    def __init__(self, N, dt):
        self.N  = N
        self.dt = dt

        self.theta = xp.random.rand(N, N) * 2 * xp.pi

        #self.theta = xp.zeros((N, N))  # start aligned
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
        self.kappa = 0.0 # geometry
        self.phase = 0
        self.dipole = 0.1
        self.triads = 0
        self.curv   = 0

        # relaxation knobs
        self.gamma_soft = 0.7
        self.kappa_soft = 0.5
        self.curv_soft  = 0.8
        self.relax_geom = 0.03
        self.theta_diff = 0.002

        # housekeeping
        self.decay_tau   = 0.02
        self.geom_decay  = 0.05
        self.sigma_c2    = 0.25 ** 2   # compression detection width
        self.tri_sigma2  = 0.8 ** 2    # triad matching Gaussian width

        # compression locking (emergence mechanics)
        self.lock_strength   = 0.0 #0.75   # how much C freezes theta (0=off, 1=full freeze)
        self.tri_lock_gain   = 0.0 #3.0    # amplify triads in compressed cores
        self.phase_lock_gain = 0.0 #2.5    # amplify phase wells in compressed cores
        self.shell_geom_gain = 0.08   # compression gradients push geometry outward

# ---------- helper: angle_diff ----------

def angle_diff(a, b):
    d = a - b
    return (d + xp.pi) % (2*xp.pi) - xp.pi

# ---------- step() orchestrates all rules ----------

def step(state: GenesisState, params: GenesisParams, rules, post=None):
    """
    rules: list of callables(state, params, extra) -> dict of contributions
    Each rule can mutate state and/or return a torque term.

    post: optional callable(torque_total, state, params, extra) -> torque_total
    Post-processing step applied after all rules have contributed torque
    but before the theta update. Used for compression locking.
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

    # post-processing (compression locking, amplification)
    if post is not None:
        torque_total = post(torque_total, state, params, extra)

    # final theta update
    state.theta = (state.theta + dt * torque_total) % (2 * xp.pi)