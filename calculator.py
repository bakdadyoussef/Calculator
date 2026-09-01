#!/usr/bin/env python3
"""
Single-file PySide6 Calculator
Modern dark-themed desktop calculator with keyboard support.
"""

from __future__ import annotations

import sys

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QKeyEvent
from PySide6.QtWidgets import (
    QApplication,
    QGridLayout,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)


# ─────────────────────────────────────────────────────────────
#  Logic
# ─────────────────────────────────────────────────────────────

class CalculatorLogic:
    def __init__(self) -> None:
        self.clear()

    def clear(self) -> None:
        self.current: str = "0"
        self.previous: float | None = None
        self.operator: str | None = None
        self.waiting_for_operand: bool = False
        self.error: bool = False

    def get_display(self) -> str:
        if self.error:
            return "Error"
        return self.current

    def input_digit(self, digit: str) -> None:
        if self.error:
            self.clear()
        if self.waiting_for_operand:
            self.current = digit
            self.waiting_for_operand = False
        else:
            if self.current == "0" and digit != ".":
                self.current = digit
            else:
                self.current += digit

    def input_decimal(self) -> None:
        if self.error:
            self.clear()
        if self.waiting_for_operand:
            self.current = "0."
            self.waiting_for_operand = False
        elif "." not in self.current:
            self.current += "."

    def input_operator(self, op: str) -> None:
        if self.error:
            self.clear()
            return
        if self.operator and not self.waiting_for_operand:
            self.calculate()
        try:
            self.previous = float(self.current)
        except ValueError:
            self.previous = 0.0
        self.operator = op
        self.waiting_for_operand = True

    def calculate(self) -> None:
        if self.error or self.operator is None or self.previous is None:
            return
        try:
            current_value = float(self.current)
        except ValueError:
            current_value = 0.0

        result: float | None = None
        if self.operator == "+":
            result = self.previous + current_value
        elif self.operator == "-":
            result = self.previous - current_value
        elif self.operator == "×":
            result = self.previous * current_value
        elif self.operator == "÷":
            if current_value == 0:
                self.error = True
                self.current = "Error"
                self.operator = None
                self.previous = None
                self.waiting_for_operand = False
                return
            result = self.previous / current_value

        if result is not None:
            if result == int(result):
                self.current = str(int(result))
            else:
                self.current = f"{result:.10g}"

        self.previous = None
        self.operator = None
        self.waiting_for_operand = True

    def backspace(self) -> None:
        if self.error:
            self.clear()
            return
        if self.waiting_for_operand:
            return
        if len(self.current) > 1:
            self.current = self.current[:-1]
        else:
            self.current = "0"

    def toggle_sign(self) -> None:
        if self.error:
            self.clear()
            return
        if self.current == "0":
            return
        if self.current.startswith("-"):
            self.current = self.current[1:]
        else:
            self.current = "-" + self.current

    def percent(self) -> None:
        if self.error:
            self.clear()
            return
        try:
            value = float(self.current) / 100
            if value == int(value):
                self.current = str(int(value))
            else:
                self.current = f"{value:.10g}"
        except ValueError:
            self.current = "0"
        self.waiting_for_operand = True


# ─────────────────────────────────────────────────────────────
#  UI
# ─────────────────────────────────────────────────────────────

class CalculatorWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.logic = CalculatorLogic()
        self.setWindowTitle("Calculator")
        self.setMinimumSize(320, 480)
        self.resize(340, 520)

        self._setup_ui()
        self._apply_styles()
        self._connect_signals()
        self._update_display()

    def _setup_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)

        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(10)

        # Display
        self.display = QLineEdit()
        self.display.setReadOnly(True)
        self.display.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.display.setMaxLength(20)
        font = QFont("Segoe UI", 28)
        font.setBold(True)
        self.display.setFont(font)
        self.display.setMinimumHeight(70)
        self.display.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
        )
        main_layout.addWidget(self.display)

        # Button grid
        grid = QGridLayout()
        grid.setSpacing(8)
        main_layout.addLayout(grid)

        buttons = [
            ("C", 0, 0), ("⌫", 0, 1), ("%", 0, 2), ("÷", 0, 3),
            ("7", 1, 0), ("8", 1, 1), ("9", 1, 2), ("×", 1, 3),
            ("4", 2, 0), ("5", 2, 1), ("6", 2, 2), ("-", 2, 3),
            ("1", 3, 0), ("2", 3, 1), ("3", 3, 2), ("+", 3, 3),
            ("±", 4, 0), ("0", 4, 1), (".", 4, 2), ("=", 4, 3),
        ]

        self.buttons: dict[str, QPushButton] = {}
        for text, row, col in buttons:
            btn = QPushButton(text)
            btn.setSizePolicy(
                QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
            )
            btn.setMinimumHeight(55)
            font = QFont("Segoe UI", 16)
            if text in {"+", "-", "×", "÷", "="}:
                font.setBold(True)
            btn.setFont(font)
            grid.addWidget(btn, row, col)
            self.buttons[text] = btn

    def _apply_styles(self) -> None:
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1e1e2e;
            }
            QLineEdit {
                background-color: #313244;
                color: #cdd6f4;
                border: none;
                border-radius: 10px;
                padding: 8px 16px;
            }
            QPushButton {
                background-color: #45475a;
                color: #cdd6f4;
                border: none;
                border-radius: 10px;
            }
            QPushButton:hover {
                background-color: #585b70;
            }
            QPushButton:pressed {
                background-color: #6c7086;
            }
        """)

        operator_style = """
            QPushButton {
                background-color: #fab387;
                color: #1e1e2e;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #f9c6a0;
            }
            QPushButton:pressed {
                background-color: #e89a6a;
            }
        """
        for op in ("÷", "×", "-", "+", "="):
            self.buttons[op].setStyleSheet(operator_style)

        special_style = """
            QPushButton {
                background-color: #585b70;
                color: #cdd6f4;
            }
            QPushButton:hover {
                background-color: #6c7086;
            }
            QPushButton:pressed {
                background-color: #7f849c;
            }
        """
        for key in ("C", "⌫", "%", "±"):
            self.buttons[key].setStyleSheet(special_style)

    def _connect_signals(self) -> None:
        for digit in "0123456789":
            self.buttons[digit].clicked.connect(
                lambda checked=False, d=digit: self._on_digit(d)
            )
        self.buttons["."].clicked.connect(self._on_decimal)
        for op in ("+", "-", "×", "÷"):
            self.buttons[op].clicked.connect(
                lambda checked=False, o=op: self._on_operator(o)
            )
        self.buttons["="].clicked.connect(self._on_equals)
        self.buttons["C"].clicked.connect(self._on_clear)
        self.buttons["⌫"].clicked.connect(self._on_backspace)
        self.buttons["%"].clicked.connect(self._on_percent)
        self.buttons["±"].clicked.connect(self._on_toggle_sign)

    def _update_display(self) -> None:
        self.display.setText(self.logic.get_display())

    def _on_digit(self, digit: str) -> None:
        self.logic.input_digit(digit)
        self._update_display()

    def _on_decimal(self) -> None:
        self.logic.input_decimal()
        self._update_display()

    def _on_operator(self, op: str) -> None:
        self.logic.input_operator(op)
        self._update_display()

    def _on_equals(self) -> None:
        self.logic.calculate()
        self._update_display()

    def _on_clear(self) -> None:
        self.logic.clear()
        self._update_display()

    def _on_backspace(self) -> None:
        self.logic.backspace()
        self._update_display()

    def _on_percent(self) -> None:
        self.logic.percent()
        self._update_display()

    def _on_toggle_sign(self) -> None:
        self.logic.toggle_sign()
        self._update_display()

    def keyPressEvent(self, event: QKeyEvent) -> None:
        key = event.key()
        text = event.text()

        if text in "0123456789":
            self._on_digit(text)
        elif text == ".":
            self._on_decimal()
        elif text in "+-":
            self._on_operator(text)
        elif text == "*":
            self._on_operator("×")
        elif text == "/":
            self._on_operator("÷")
        elif key in (Qt.Key.Key_Return, Qt.Key.Key_Enter, Qt.Key.Key_Equal):
            self._on_equals()
        elif key == Qt.Key.Key_Backspace:
            self._on_backspace()
        elif key == Qt.Key.Key_Escape:
            self._on_clear()
        elif text == "%":
            self._on_percent()
        else:
            super().keyPressEvent(event)


# ─────────────────────────────────────────────────────────────
#  Entry point
# ─────────────────────────────────────────────────────────────

def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("Calculator")
    window = CalculatorWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
