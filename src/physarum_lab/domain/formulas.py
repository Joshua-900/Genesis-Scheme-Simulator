"""Bounded mathematical expressions interpreted without eval or Python execution."""
from __future__ import annotations

import ast
from dataclasses import dataclass
import math
import operator

import numpy as np

from .genesis_source import FIELD_NAMES


class FormulaError(ValueError):
    """An expression is unsupported or numerically undefined on this field."""


FUNCTIONS = {
    'sin': (np.sin, 1), 'cos': (np.cos, 1), 'tan': (np.tan, 1),
    'abs': (np.abs, 1), 'sqrt': (np.sqrt, 1), 'exp': (np.exp, 1),
    'log': (np.log, 1), 'floor': (np.floor, 1), 'ceil': (np.ceil, 1),
    'tanh': (np.tanh, 1), 'atan': (np.arctan, 1), 'atan2': (np.arctan2, 2),
    'min': (np.minimum, 2), 'max': (np.maximum, 2), 'hypot': (np.hypot, 2),
    'clip': (np.clip, 3), 'where': (np.where, 3),
}
OPERATORS = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
             ast.Div: operator.truediv, ast.Mod: operator.mod, ast.Pow: np.power}
COMPARISONS = {ast.Lt: operator.lt, ast.LtE: operator.le, ast.Gt: operator.gt,
               ast.GtE: operator.ge, ast.Eq: operator.eq, ast.NotEq: operator.ne}
CONSTANTS = {'pi': math.pi, 'tau': math.tau, 'e': math.e}


class Expression:
    def __init__(self, source: str, fields=()):
        if not isinstance(source, str) or not source.strip() or len(source) > 512:
            raise FormulaError('Enter a formula of 1–512 characters.')
        try:
            self.tree = ast.parse(source.replace('^', '**').strip(), mode='eval').body
        except (SyntaxError, RecursionError) as exc:
            raise FormulaError('Invalid syntax. Example: sin(4*pi*x + t).') from exc
        if sum(1 for _ in ast.walk(self.tree)) > 128:
            raise FormulaError('Formula is too complex; use fewer operations.')
        self.time_dependent = False
        self.fields = frozenset(fields)
        self.used_fields = set()
        self._validate(self.tree)

    def _validate(self, node, depth=0):
        if depth > 20:
            raise FormulaError('Formula nesting is too deep.')
        if isinstance(node, ast.Constant):
            if type(node.value) not in (int, float) or abs(node.value) > 1e6 or not math.isfinite(node.value):
                raise FormulaError('Use real numeric constants no larger than 1,000,000.')
            return
        if isinstance(node, ast.Name):
            if node.id in self.fields:
                self.used_fields.add(node.id)
            elif node.id in FIELD_NAMES:
                raise FormulaError(f'{node.id} requires a Genesis source. Start Genesis comparison first.')
            elif node.id not in {'x', 'y', 't', *CONSTANTS}:
                raise FormulaError(f'Unknown name: {node.id}. Use x, y, t, pi, tau or e.')
            self.time_dependent |= node.id == 't'
            return
        if isinstance(node, ast.BinOp) and type(node.op) in OPERATORS:
            children = (node.left, node.right)
        elif isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub, ast.Not)):
            children = (node.operand,)
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in FUNCTIONS:
            if node.keywords or len(node.args) != FUNCTIONS[node.func.id][1]:
                raise FormulaError(f'{node.func.id} takes {FUNCTIONS[node.func.id][1]} positional arguments.')
            children = node.args
        elif isinstance(node, ast.Compare) and len(node.ops) == 1 and type(node.ops[0]) in COMPARISONS:
            children = (node.left, node.comparators[0])
        elif isinstance(node, ast.BoolOp) and isinstance(node.op, (ast.And, ast.Or)):
            children = node.values
        else:
            raise FormulaError('Only arithmetic, comparisons and the listed math functions are allowed.')
        for child in children:
            self._validate(child, depth + 1)

    def evaluate(self, x, y, t, bindings=None):
        variables = dict(x=x, y=y, t=t, **CONSTANTS)
        if self.used_fields:
            variables.update({name: bindings[name] for name in self.used_fields})

        def checked(value):
            value = np.asarray(value)
            if not np.isfinite(value).all() or (np.abs(value) > 1e6).any():
                raise FormulaError('Undefined or excessive values. Check division, roots, logs and scale.')
            return value

        def visit(node):
            if isinstance(node, ast.Constant):
                return float(node.value)
            if isinstance(node, ast.Name):
                return variables[node.id]
            if isinstance(node, ast.BinOp):
                a, b = visit(node.left), visit(node.right)
                if isinstance(node.op, ast.Pow) and (np.abs(b) > 16).any():
                    raise FormulaError('Exponents must stay between -16 and 16.')
                return checked(OPERATORS[type(node.op)](a, b))
            if isinstance(node, ast.UnaryOp):
                value = visit(node.operand)
                return -value if isinstance(node.op, ast.USub) else np.logical_not(value) if isinstance(node.op, ast.Not) else value
            if isinstance(node, ast.Compare):
                return COMPARISONS[type(node.ops[0])](visit(node.left), visit(node.comparators[0]))
            if isinstance(node, ast.BoolOp):
                fn = np.logical_and if isinstance(node.op, ast.And) else np.logical_or
                value = visit(node.values[0])
                for part in node.values[1:]:
                    value = fn(value, visit(part))
                return value
            return checked(FUNCTIONS[node.func.id][0](*(visit(arg) for arg in node.args)))

        try:
            with np.errstate(all='ignore'):
                result = np.broadcast_to(checked(visit(self.tree)), np.broadcast_shapes(np.shape(x), np.shape(y)))
                return np.asarray(result, dtype=np.float32)
        except (FloatingPointError, OverflowError, ZeroDivisionError, TypeError) as exc:
            raise FormulaError('Formula is undefined on these coordinates.') from exc


@dataclass(frozen=True)
class FormulaSpec:
    expression: str = 'sin(4*pi*x + t) * cos(3*pi*y - t)'
    response: str = 'zero'
    velocity_x: str = '-y'
    velocity_y: str = 'x'
    scale: float = 1.
    time_speed: float = 1.

    def __post_init__(self):
        if self.response not in ('zero', 'high', 'low', 'flow'):
            raise FormulaError('Choose zero contours, peaks, repel peaks, or vector flow.')
        if not math.isfinite(self.scale) or not .1 <= self.scale <= 16:
            raise FormulaError('Spatial scale must be .1–16.')
        if not math.isfinite(self.time_speed) or not 0 <= self.time_speed <= 10:
            raise FormulaError('Time speed must be 0–10.')


class FormulaField:
    """Owns parsed expressions and caches fields that do not depend on time."""
    def __init__(self, spec: FormulaSpec, genesis=None):
        self.spec = spec
        self.genesis = genesis
        sources = (spec.velocity_x, spec.velocity_y) if spec.response == 'flow' else (spec.expression,)
        self.expressions = tuple(Expression(source, FIELD_NAMES if genesis is not None else ()) for source in sources)
        self.used_fields = set().union(*(expr.used_fields for expr in self.expressions))
        self.static = not any(expr.time_dependent for expr in self.expressions) or spec.time_speed == 0
        self._cached = None
        self._bindings = None

    def sample(self, x, y, size, tick, bindings=None):
        scale = self.spec.scale
        x, y = (np.asarray(x) / size * 2 - 1) * scale, (np.asarray(y) / size * 2 - 1) * scale
        t = tick / 60 * self.spec.time_speed
        return tuple(expr.evaluate(x, y, t, bindings) for expr in self.expressions)

    def grid(self, size, tick):
        key = (size, self.genesis.tick if self.used_fields else None)
        if self.static and self._cached is not None and self._cached[0] == key:
            return self._cached[1]
        axis = np.arange(size, dtype=np.float32) + .5
        if self.used_fields and (self._bindings is None or self._bindings[0] != key):
            self._bindings = key, self.genesis.grid(size, self.used_fields)
        bindings = self._bindings[1] if self._bindings is not None else None
        values = self.sample(axis[None, :], axis[:, None], size, tick, bindings)
        if self.static:
            self._cached = (key, values)
        return values
