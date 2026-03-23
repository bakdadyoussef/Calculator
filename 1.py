import sys
import math
from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QRect
from PySide6.QtGui import QFont, QPalette, QLinearGradient, QColor, QAction, QKeySequence
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                               QHBoxLayout, QGridLayout, QPushButton, QLineEdit,
                               QLabel, QFrame, QGraphicsDropShadowEffect)


class ModernCalculator(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("NeonCalc")
        self.setFixedSize(400, 550)
        self.setWindowFlags(Qt.FramelessWindowHint)  # Optional: remove window border
        self.setAttribute(Qt.WA_TranslucentBackground)

        # Central widget and main layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(10, 10, 10, 10)
        self.main_layout.setSpacing(15)

        # Apply global style sheet
        self.setStyleSheet("""
            QWidget {
                font-family: 'Segoe UI', 'Inter', sans-serif;
                font-size: 20px;
            }
            QPushButton {
                background-color: #2c2f36;
                color: #ffffff;
                border: none;
                border-radius: 20px;
                font-weight: bold;
                padding: 15px;
            }
            QPushButton:hover {
                background-color: #3e424b;
            }
            QPushButton:pressed {
                background-color: #1e2127;
            }
            QPushButton#operator {
                background-color: #ff9800;
                color: #1e1e2f;
            }
            QPushButton#operator:hover {
                background-color: #ffb74d;
            }
            QPushButton#clear {
                background-color: #f44336;
                color: white;
            }
            QPushButton#clear:hover {
                background-color: #ff6659;
            }
            QPushButton#equals {
                background-color: #4caf50;
                color: white;
            }
            QPushButton#equals:hover {
                background-color: #6fbf73;
            }
            QLineEdit {
                background-color: rgba(30, 30, 47, 200);
                color: #ffffff;
                border: none;
                border-radius: 30px;
                padding: 20px;
                font-size: 32px;
                font-weight: bold;
                text-align: right;
            }
        """)

        # Create display
        self.display = QLineEdit()
        self.display.setAlignment(Qt.AlignRight)
        self.display.setReadOnly(True)
        self.display.setMinimumHeight(90)
        self.display.setMaxLength(30)

        # Add shadow effect to display
        display_shadow = QGraphicsDropShadowEffect()
        display_shadow.setBlurRadius(20)
        display_shadow.setColor(QColor(0, 0, 0, 80))
        display_shadow.setOffset(0, 4)
        self.display.setGraphicsEffect(display_shadow)

        self.main_layout.addWidget(self.display)

        # Button layout
        button_grid = QGridLayout()
        button_grid.setSpacing(12)

        # Button definitions: (text, row, col, rowspan, colspan, object_name)
        buttons = [
            ("C", 0, 0, 1, 1, "clear"),
            ("±", 0, 1, 1, 1, "sign"),
            ("%", 0, 2, 1, 1, "percent"),
            ("÷", 0, 3, 1, 1, "operator"),
            ("7", 1, 0, 1, 1, "digit"),
            ("8", 1, 1, 1, 1, "digit"),
            ("9", 1, 2, 1, 1, "digit"),
            ("×", 1, 3, 1, 1, "operator"),
            ("4", 2, 0, 1, 1, "digit"),
            ("5", 2, 1, 1, 1, "digit"),
            ("6", 2, 2, 1, 1, "digit"),
            ("-", 2, 3, 1, 1, "operator"),
            ("1", 3, 0, 1, 1, "digit"),
            ("2", 3, 1, 1, 1, "digit"),
            ("3", 3, 2, 1, 1, "digit"),
            ("+", 3, 3, 1, 1, "operator"),
            ("0", 4, 0, 1, 2, "digit"),
            (".", 4, 2, 1, 1, "decimal"),
            ("=", 4, 3, 1, 1, "equals"),
        ]

        for text, row, col, rowspan, colspan, obj_name in buttons:
            button = QPushButton(text)
            button.setObjectName(obj_name)
            if text in "÷×+-":
                button.setObjectName("operator")
            if text == "C":
                button.setObjectName("clear")
            if text == "=":
                button.setObjectName("equals")
            button.setFixedSize(80, 70)
            if text == "0":
                button.setFixedSize(170, 70)  # Span two columns
                button_grid.addWidget(button, row, col, rowspan, colspan)
            else:
                button_grid.addWidget(button, row, col, rowspan, colspan)
            button.clicked.connect(self.on_button_clicked)

        self.main_layout.addLayout(button_grid)

        # Variables to manage calculation state
        self.current_expression = ""
        self.last_result = None
        self.waiting_for_operand = False

        # Enable keyboard input
        self.setFocusPolicy(Qt.StrongFocus)

    def on_button_clicked(self):
        button = self.sender()
        text = button.text()

        if text == "C":
            self.clear_all()
        elif text == "=":
            self.evaluate_expression()
        elif text == "±":
            self.toggle_sign()
        elif text == "%":
            self.apply_percentage()
        elif text in "0123456789.":
            self.append_digit(text)
        elif text in "+-×÷":
            self.append_operator(text)

        # Update display
        self.display.setText(self.current_expression if self.current_expression else "0")

    def clear_all(self):
        self.current_expression = ""
        self.last_result = None
        self.waiting_for_operand = False

    def append_digit(self, digit):
        if self.waiting_for_operand:
            self.current_expression = ""
            self.waiting_for_operand = False
        if digit == "." and self.current_expression.count(".") > 0:
            return
        self.current_expression += digit

    def append_operator(self, op):
        if not self.current_expression and self.last_result is not None:
            self.current_expression = str(self.last_result)
        if self.current_expression and self.current_expression[-1] in "+-×÷":
            # Replace last operator
            self.current_expression = self.current_expression[:-1] + op
        else:
            self.current_expression += op
        self.waiting_for_operand = True

    def evaluate_expression(self):
        if not self.current_expression:
            return
        try:
            # Replace × and ÷ with * and / for evaluation
            expr = self.current_expression.replace("×", "*").replace("÷", "/")
            # Evaluate safely using eval (restricted environment)
            # Note: eval is used here for simplicity; ensure input is sanitized.
            # Since we only allow digits, operators, and ., it's safe.
            result = eval(expr, {"__builtins__": None}, {})
            # Round to avoid floating point artifacts
            if isinstance(result, float):
                result = round(result, 10)
            self.current_expression = str(result)
            self.last_result = result
            self.waiting_for_operand = True
        except ZeroDivisionError:
            self.current_expression = "Error: Division by zero"
            self.last_result = None
            self.waiting_for_operand = False
        except Exception:
            self.current_expression = "Error"
            self.last_result = None
            self.waiting_for_operand = False

    def toggle_sign(self):
        if self.current_expression:
            try:
                val = float(self.current_expression)
                val = -val
                self.current_expression = str(int(val) if val.is_integer() else val)
                self.waiting_for_operand = True
            except ValueError:
                pass

    def apply_percentage(self):
        if self.current_expression:
            try:
                val = float(self.current_expression)
                val /= 100
                self.current_expression = str(int(val) if val.is_integer() else val)
                self.waiting_for_operand = True
            except ValueError:
                pass

    def keyPressEvent(self, event):
        key = event.key()
        text = event.text()

        if key == Qt.Key_Backspace:
            self.current_expression = self.current_expression[:-1]
            self.display.setText(self.current_expression or "0")
        elif key == Qt.Key_Return or key == Qt.Key_Enter:
            self.evaluate_expression()
            self.display.setText(self.current_expression)
        elif key == Qt.Key_Escape:
            self.clear_all()
            self.display.setText("0")
        elif text.isdigit() or text == '.':
            self.append_digit(text)
            self.display.setText(self.current_expression)
        elif text in '+-*/':
            # Map * and / to × and ÷
            if text == '*':
                text = '×'
            elif text == '/':
                text = '÷'
            self.append_operator(text)
            self.display.setText(self.current_expression)
        else:
            super().keyPressEvent(event)


if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Set application-wide dark palette (optional, but complements the style)
    app.setStyle("Fusion")
    palette = app.palette()
    palette.setColor(QPalette.Window, QColor(25, 25, 35))
    palette.setColor(QPalette.WindowText, Qt.white)
    palette.setColor(QPalette.Base, QColor(30, 30, 47))
    palette.setColor(QPalette.AlternateBase, QColor(45, 45, 60))
    palette.setColor(QPalette.ToolTipBase, Qt.white)
    palette.setColor(QPalette.ToolTipText, Qt.white)
    palette.setColor(QPalette.Text, Qt.white)
    palette.setColor(QPalette.Button, QColor(44, 47, 54))
    palette.setColor(QPalette.ButtonText, Qt.white)
    palette.setColor(QPalette.BrightText, Qt.red)
    palette.setColor(QPalette.Highlight, QColor(255, 152, 0))
    palette.setColor(QPalette.HighlightedText, Qt.black)
    app.setPalette(palette)

    window = ModernCalculator()
    window.show()
    sys.exit(app.exec())
