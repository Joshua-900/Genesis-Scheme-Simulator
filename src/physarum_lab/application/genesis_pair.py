"""Matched chase lanes driven by a shared set of user controls."""
from dataclasses import replace

from .session import Session
from ..domain.chase import Chase
from ..domain.formulas import FormulaSpec
from ..domain.genesis_source import FrozenGenesis

GENESIS_FLOW = FormulaSpec(response='flow', velocity_x='ux', velocity_y='uy')

class GenesisFeed:
    """Advance the source between paired ticks and expose read-only samples."""

    def __init__(self, model, source):
        self.model = model
        self.current = source
        self.seed = source.seed
        self.baseline = {lane: params.copy() for lane, params in model.parameters.items()}

    def scale_parameter(self, name, multiplier):
        for lane, params in self.model.parameters.items():
            params[name] = self.baseline[lane][name] * multiplier
            if name in ('tri_sigma', 'sigma_c'):
                squared = name + '2'
                params[squared] = self.baseline[lane][squared] * multiplier**2

    @property
    def tick(self):
        return self.current.tick

    def grid(self, size, names):
        return self.current.grid(size, names)

    def snapshot(self):
        return self.current.snapshot()

    def advance(self):
        self.model.advance()
        self.current = FrozenGenesis(self.seed, self.model.update, self.model.states['geometry_on'])


class GenesisPair:
    def __init__(self, seed, rules, source, genesis_model=None):
        self.feed = GenesisFeed(genesis_model, source) if genesis_model is not None else None
        self.evolving = False
        if self.feed is not None:
            source = self.feed
        chase = Chase(seed, rules, genesis=source)
        control = Chase.restore(chase.snapshot())
        self.guided = Session(chase, playing=False, guidance=.45, target_guidance=.45)
        self.control = Session(control, playing=False, guidance=.45, target_guidance=.45)
        self.set_formula(GENESIS_FLOW, 'ivory')
        self.set_formula(FormulaSpec(response='flow', velocity_x='0', velocity_y='0'), 'amber')

    def set_formula(self, spec, target):
        self.guided.simulation.set_formula(spec, target)
        neutral = (replace(spec, expression='0', velocity_x='0', velocity_y='0')
                   if spec is not None else FormulaSpec(expression='0'))
        self.control.simulation.set_formula(neutral, target)

    def set_modes(self, m, n):
        self.guided.simulation.set_modes(m, n)
        self.control.simulation.set_modes(m, n)
        self.control.simulation.set_formula(FormulaSpec(expression='0'))

    def reseed(self, seed):
        """Restart matched populations against the current, held source."""
        fresh = []
        for session in (self.guided, self.control):
            previous = session.simulation
            chase = Chase(seed, replace(previous.rules, agents=previous.population),
                          previous.follow, previous.erase, genesis=previous.genesis)
            for target, population in (('ivory', previous), ('amber', previous.amber)):
                chase.set_formula(population.formula.spec if population.formula else None, target)
            fresh.append(chase)
        self.guided.simulation, self.control.simulation = fresh
        self.guided.playing = self.control.playing = self.evolving = False

    def advance(self):
        self.guided.advance(force=True)
        self.control.advance(force=True)
        if self.evolving and self.feed is not None:
            self.feed.advance()
