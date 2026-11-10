"""Two populations with independent memories and a shared tick."""
from dataclasses import replace
import math

import numpy as np

from .formulas import FormulaSpec
from .model import Rules, Simulation

SPIRAL = FormulaSpec(expression='sin(atan2(y,x) + 13*hypot(x,y))')


class Chase(Simulation):
    """Ivory lays trails. Amber follows them and erases them underfoot."""

    def __init__(self, seed: int, rules: Rules, follow=2.5, erase=.35, *, genesis=None):
        if rules.agents < 2:
            raise ValueError('Chase needs at least two agents.')
        ivory = (rules.agents + 1) // 2
        super().__init__(seed, replace(rules, agents=ivory), genesis=genesis)
        self.amber = Simulation(seed ^ 0xACE, replace(rules, agents=rules.agents - ivory,
                                                      speed=min(10., rules.speed * 1.18)), genesis=genesis)
        # Start amber in a smaller pocket so its pursuit has a visible front.
        self.amber.x[:] = (self.amber.x - rules.size * .5) * .45 + rules.size * .67
        self.amber.y[:] = (self.amber.y - rules.size * .5) * .45 + rules.size * .40
        self.set_interaction(follow, erase)
        self.set_formula(SPIRAL)

    @property
    def population(self):
        return self.rules.agents + self.amber.rules.agents

    def set_interaction(self, follow, erase):
        if not math.isfinite(follow) or not 0 <= follow <= 8:
            raise ValueError('Follow must be in 0–8.')
        if not math.isfinite(erase) or not 0 <= erase <= 1:
            raise ValueError('Erase must be in 0–1.')
        self.follow, self.erase = float(follow), float(erase)

    def _prepare(self, guidance):
        ivory = super()._prepare(guidance)
        amber = self.amber._prepare(guidance)
        score, wave, velocity = amber
        score += self.follow * np.log1p(self.trail)
        return ivory, (score, wave, velocity)

    def _advance(self, guidance, prepared):
        ivory, amber = prepared
        super()._advance(guidance, ivory)
        self.amber._advance(guidance, amber)
        if self.erase:
            self.trail *= np.power(1 - self.erase, self.amber.density)

    def set_formula(self, spec, target='both'):
        if target == 'amber':
            self.amber.set_formula(spec)
        elif target in ('ivory', 'both'):
            super().set_formula(spec)
            if target == 'both':
                self.amber.formula, self.amber.wave = self.formula, self.wave
        else:
            raise ValueError('Choose ivory, amber or both populations.')

    def set_modes(self, m, n):
        super().set_modes(m, n)
        self.amber.set_modes(m, n)

    def disturb(self, x, y, radius=24., strength=1.):
        super().disturb(x, y, radius, strength)
        self.amber.disturb(x, y, radius, strength)

    def snapshot(self):
        amber = self.amber.snapshot()
        amber.pop('genesis', None)
        return dict(super().snapshot(), amber=amber,
                    follow=self.follow, erase=self.erase)

    @classmethod
    def restore(cls, snapshot):
        ivory = Simulation.restore(snapshot)
        amber = Simulation.restore(snapshot['amber'], genesis=ivory.genesis)
        if ivory.tick != amber.tick or ivory.rules.size != amber.rules.size:
            raise ValueError('Chase populations must share a field and tick.')
        result = cls.__new__(cls)
        result.__dict__.update(ivory.__dict__)
        result.amber = amber
        result.set_interaction(snapshot['follow'], snapshot['erase'])
        return result
