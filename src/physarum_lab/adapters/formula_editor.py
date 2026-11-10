"""Modeless formula authoring with draft previews and explicit live application."""
from __future__ import annotations

import numpy as np
from PIL import Image, ImageDraw
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtWidgets import (
    QComboBox, QDialog, QDoubleSpinBox, QFormLayout, QHBoxLayout, QLabel,
    QPlainTextEdit, QPushButton, QScrollArea, QSlider, QVBoxLayout, QWidget,
)

from ..domain.formulas import FormulaField, FormulaSpec, FormulaError
from ..domain.chase import Chase, SPIRAL
from .render import colorize

EXAMPLES = {
    'Chase spiral': SPIRAL,
    'Moving interference': FormulaSpec(),
    'Radial ripples': FormulaSpec(expression='sin(12*sqrt(x*x + y*y) - 2*t)'),
    'Spiral': FormulaSpec(expression='sin(5*atan2(y,x) + 12*sqrt(x*x+y*y) - t)'),
    'Breathing ring': FormulaSpec(expression='x*x + y*y - (0.55 + 0.15*sin(t))^2'),
    'Peaks and islands': FormulaSpec(expression='cos(3*pi*x)*cos(3*pi*y + t)', response='high'),
    'Vortex current': FormulaSpec(response='flow', velocity_x='-y', velocity_y='x'),
    'Weaving current': FormulaSpec(response='flow', velocity_x='sin(3*pi*y+t)', velocity_y='cos(3*pi*x-t)'),
}
GENESIS_EXAMPLES = {
    'Genesis displacement': FormulaSpec(response='flow', velocity_x='ux', velocity_y='uy'),
    'Genesis compression contour': FormulaSpec(expression='C - 0.1'),
}
RESPONSES = {'Gather at zero contours': 'zero', 'Gather near peaks': 'high',
             'Repel from peaks': 'low', 'Vector current (u, v)': 'flow'}


def preview_image(field: FormulaField, tick: int, side=256):
    values = field.grid(side, tick)
    response = field.spec.response
    if response == 'flow':
        magnitude = np.hypot(*values)
        intensity = np.tanh(magnitude)
    elif response == 'zero':
        intensity = np.exp(-np.clip(values[0], -100, 100)**2 / .02)
    else:
        intensity = .5 + .5 * np.tanh(values[0]) * (1 if response == 'high' else -1)
    image = Image.fromarray(colorize(intensity[::-1], 'Pearl').astype(np.uint8))
    if response == 'flow':
        draw = ImageDraw.Draw(image)
        for row in range(12, side, 24):
            for col in range(12, side, 24):
                dx, dy = float(values[0][row, col]), -float(values[1][row, col])
                length = np.hypot(dx, dy)
                if length < 1e-6:
                    continue
                dx, dy = dx / length * 9, dy / length * 9
                x, y = col, side - 1 - row
                draw.line((x - dx / 2, y - dy / 2, x + dx / 2, y + dy / 2), fill='#f4eedb', width=1)
                draw.line((x + dx / 2, y + dy / 2, x + dx / 4 - dy / 3, y + dy / 4 + dx / 3), fill='#f4eedb')
    low = min(float(value.min()) for value in values)
    high = max(float(value.max()) for value in values)
    return image, low, high


class FormulaEditor(QDialog):
    def __init__(self, studio):
        super().__init__(studio)
        self.studio = studio
        self.setWindowTitle('Formula editor — Physarum Studio')
        self.resize(500, 880)
        self.setMinimumWidth(440)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        scroll.setWidget(content)
        outer.addWidget(scroll)
        layout = QVBoxLayout(content)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(10)
        heading = QLabel('FORMULA / FIELD')
        heading.setStyleSheet('font-size:20px; font-weight:600;')
        layout.addWidget(heading)
        help_text = QLabel('x, y: −1 to 1, y points up. t: ticks / 60.\nSpatial scale multiplies x/y; time speed multiplies t.')
        help_text.setWordWrap(True)
        layout.addWidget(help_text)
        self.examples = QComboBox()
        self.examples.addItems(EXAMPLES)
        self.examples.setAccessibleName('Formula examples')
        self.examples.activated.connect(self.choose_example)
        layout.addWidget(self.examples)
        self.response = QComboBox()
        for title, value in RESPONSES.items():
            self.response.addItem(title, value)
        self.response.currentIndexChanged.connect(self.response_changed)
        layout.addWidget(self.response)
        self.target = QComboBox()
        self.target.addItem('Guide both populations', 'both')
        self.target.addItem('Guide ivory only', 'ivory')
        self.target.addItem('Guide amber only', 'amber')
        layout.addWidget(self.target)
        self.genesis_hint = QLabel('Genesis variables: C (compression), ux and uy (displacement).')
        self.genesis_hint.setWordWrap(True)
        layout.addWidget(self.genesis_hint)
        self.sync_target()
        self.scalar_label = QLabel('Scalar field  F(x, y, t)')
        layout.addWidget(self.scalar_label)
        self.scalar = QPlainTextEdit()
        self.scalar.setAccessibleName('Scalar formula')
        self.scalar.setMaximumHeight(72)
        layout.addWidget(self.scalar)
        self.u_label, self.v_label = QLabel('Horizontal velocity  u(x, y, t)'), QLabel('Vertical velocity  v(x, y, t)')
        self.u, self.v = QPlainTextEdit(), QPlainTextEdit()
        self.u.setAccessibleName('Horizontal velocity formula')
        self.v.setAccessibleName('Vertical velocity formula')
        for title, editor in ((self.u_label, self.u), (self.v_label, self.v)):
            editor.setMaximumHeight(54)
            layout.addWidget(title)
            layout.addWidget(editor)
        form = QFormLayout()
        self.scale, self.time_speed = QDoubleSpinBox(), QDoubleSpinBox()
        self.scale.setRange(.1, 16)
        self.time_speed.setRange(0, 10)
        for control in (self.scale, self.time_speed):
            control.setSingleStep(.1)
            control.setDecimals(2)
        form.addRow('Spatial scale', self.scale)
        form.addRow('Time speed', self.time_speed)
        layout.addLayout(form)
        self.strength_label = QLabel('')
        layout.addWidget(self.strength_label)
        self.strength = QSlider(Qt.Horizontal)
        self.strength.setRange(0, 100)
        self.strength.setValue(studio.guidance.value() or 100)
        self.strength.valueChanged.connect(lambda value: self.strength_label.setText(f'Apply strength  {value}%'))
        self.strength_label.setText(f'Apply strength  {self.strength.value()}%')
        layout.addWidget(self.strength)
        row = QHBoxLayout()
        self.preview_button, self.apply_button = QPushButton('Preview draft'), QPushButton('Apply live')
        self.apply_button.setObjectName('primary')
        self.preview_button.clicked.connect(self.preview)
        self.apply_button.clicked.connect(self.apply)
        row.addWidget(self.preview_button)
        row.addWidget(self.apply_button)
        layout.addLayout(row)
        self.preview_label = QLabel()
        self.preview_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.preview_label)
        self.preview_caption = QLabel('')
        self.preview_caption.setWordWrap(True)
        layout.addWidget(self.preview_caption)
        self.status = QLabel('')
        self.status.setWordWrap(True)
        layout.addWidget(self.status)
        self.builtin = QPushButton('Return to wave modes')
        self.builtin.clicked.connect(self.use_builtin)
        layout.addWidget(self.builtin)
        syntax = QLabel('Functions: sin cos tan tanh abs sqrt exp log atan atan2\nmin max hypot floor ceil clip where. Constants: pi tau e.\nPowers: ^ or **. Comparisons and and/or/not supported.\nThe domain wraps; formulas may have seams at its edges.')
        syntax.setWordWrap(True)
        syntax.setStyleSheet('color:#849996; font-size:11px;')
        layout.addWidget(syntax)
        self.set_spec(studio.session.simulation.formula.spec if studio.session.simulation.formula is not None else FormulaSpec())
        self.preview()

    def set_spec(self, spec):
        self.scalar.setPlainText(spec.expression)
        self.u.setPlainText(spec.velocity_x)
        self.v.setPlainText(spec.velocity_y)
        self.response.setCurrentIndex(self.response.findData(spec.response))
        self.scale.setValue(spec.scale)
        self.time_speed.setValue(spec.time_speed)
        self.response_changed()

    def sync_target(self):
        simulation = self.studio.session.simulation
        self.target.setVisible(isinstance(simulation, Chase))
        self.genesis_hint.setVisible(simulation.genesis is not None)
        for name in GENESIS_EXAMPLES:
            index = self.examples.findText(name)
            if simulation.genesis is not None and index < 0:
                self.examples.addItem(name)
            elif simulation.genesis is None and index >= 0:
                self.examples.removeItem(index)

    def spec(self):
        return FormulaSpec(expression=self.scalar.toPlainText(), response=self.response.currentData(),
                           velocity_x=self.u.toPlainText(), velocity_y=self.v.toPlainText(),
                           scale=self.scale.value(), time_speed=self.time_speed.value())

    def choose_example(self):
        self.set_spec((EXAMPLES | GENESIS_EXAMPLES)[self.examples.currentText()])
        self.preview()

    def response_changed(self):
        vector = self.response.currentData() == 'flow'
        for widget in (self.scalar_label, self.scalar):
            widget.setVisible(not vector)
        for widget in (self.u_label, self.u, self.v_label, self.v):
            widget.setVisible(vector)

    def error(self, exc, *, clear_preview=True):
        if clear_preview:
            self.preview_label.clear()
            self.preview_caption.setText('No preview for this draft.')
        self.status.setStyleSheet('color:#f3ad9b;')
        self.status.setText(str(exc))

    def preview(self):
        try:
            simulation = self.studio.session.simulation
            field = FormulaField(self.spec(), simulation.genesis)
            tick = simulation.tick
            image, low, high = preview_image(field, tick)
            rgb = np.ascontiguousarray(image)
            qimage = QImage(rgb.data, image.width, image.height, rgb.strides[0], QImage.Format_RGB888).copy()
            self.preview_label.setPixmap(QPixmap.fromImage(qimage))
            self.preview_caption.setText(f'Draft at tick {tick:,} · values {low:.3g} to {high:.3g}. '
                                         + ('Arrows show current direction.' if field.spec.response == 'flow' else 'Bright regions attract most strongly.'))
            self.status.setStyleSheet('color:#c5d6bf;')
            self.status.setText('Valid draft. Apply live to use it; preview leaves the simulation unchanged.')
            return True
        except FormulaError as exc:
            self.error(exc)
            return False

    def apply(self):
        try:
            spec = self.spec()
            self.studio.set_active_formula(spec, self.target.currentData(), self.strength.value())
            self.status.setStyleSheet('color:#c5d6bf;')
            self.status.setText('Applied. Strength blends over simulation ticks. Press Play if paused.')
            self.studio.message.setText('Custom formula applied. Formula editor can preview or replace it while the field runs.')
        except FormulaError as exc:
            self.error(exc)

    def use_builtin(self):
        self.studio.set_active_formula(None, self.target.currentData())
        self.status.setStyleSheet('color:#c5d6bf;')
        self.status.setText('Wave modes restored; your draft remains in this editor.')
