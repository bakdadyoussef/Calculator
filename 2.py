import sys
import math
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QRect, QPoint
from PySide6.QtGui import QFont, QPalette, QColor, QLinearGradient, QAction, QKeySequence
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                               QHBoxLayout, QGridLayout, QPushButton, QLineEdit,
                               QLabel, QFrame, QGraphicsDropShadowEffect, QSizePolicy)


class ExpressionEvaluator:
    """A simple shunting-yard algorithm to evaluate arithmetic expressions."""
    def __init__(self):
        self.precedence = {
            '+': 1, '-': 1,
            '*': 2, '/': 2,
            '^': 3,
            '√': 4,      # unary square root
            '±': 4,      # unary minus (sign)
        }
        self.associativity = {
            '+': 'L', '-': 'L',
            '*': 'L', '/': 'L',
            '^': 'R',
            '√': 'R',
            '±': 'R',
        }

    def tokenize(self, expression):
        """Convert expression string into a list of tokens (numbers, operators, parentheses)."""
        tokens = []
        i = 0
        n = len(expression)
        while i < n:
            ch = expression[i]
            if ch.isdigit() or ch == '.':
                # Read number
                j = i
                while j < n and (expression[j].isdigit() or expression[j] == '.'):
                    j += 1
                tokens.append(expression[i:j])
                i = j
            elif ch in '+-*/^√%()':
                tokens.append(ch)
                i += 1
            else:
                # Skip whitespace
                i += 1
        return tokens

    def apply_operator(self, operators, values):
        op = operators.pop()
        if op == '√':
            # Unary square root
            val = values.pop()
            values.append(math.sqrt(val))
        elif op == '±':
            # Unary minus (toggle sign)
            val = values.pop()
            values.append(-val)
        else:
            right = values.pop()
            left = values.pop()
            if op == '+':
                values.append(left + right)
            elif op == '-':
                values.append(left - right)
            elif op == '*':
                values.append(left * right)
            elif op == '/':
                if right == 0:
                    raise ZeroDivisionError("Division by zero")
                values.append(left / right)
            elif op == '^':
                values.append(left ** right)
            elif op == '%':
                # Modulo (remainder)
                values.append(left % right)

    def evaluate(self, expression):
        """Evaluate the given expression and return a numeric result."""
        tokens = self.tokenize(expression)
        values = []
        operators = []

        for token in tokens:
            if token.replace('.', '').isdigit():
                # Number
                values.append(float(token))
            elif token == '(':
                operators.append(token)
            elif token == ')':
                while operators and operators[-1] != '(':
                    self.apply_operator(operators, values)
                if operators and operators[-1] == '(':
                    operators.pop()
                else:
                    raise ValueError("Mismatched parentheses")
            elif token in self.precedence:
                # Handle unary minus
                if token == '-' and (not values or (operators and operators[-1] == '(')):
                    token = '±'  # treat as unary sign
                while (operators and operators[-1] != '(' and
                       (self.precedence[operators[-1]] > self.precedence[token] or
                        (self.precedence[operators[-1]] == self.precedence[token] and
                         self.associativity[token] == 'L'))):
                    self.apply_operator(operators, values)
                operators.append(token)
            elif token == '%':
                # Modulo operator (binary)
                # We treat it as binary, but need to handle it like other operators
                # For simplicity, we add to operators
                while (operators and operators[-1] != '(' and
                       self.precedence[operators[-1]] >= self.precedence[token]):
                    self.apply_operator(operators, values)
                operators.append(token)
            else:
                raise ValueError(f"Unknown token: {token}")

        while operators:
            self.apply_operator(operators, values)

        if len(values) != 1:
            raise ValueError("Invalid expression")

        result = values[0]
        # Round to avoid floating point artifacts
        if isinstance(result, float):
            result = round(result, 12)
        return result


class ModernCalculator(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AdvancedCalc")
        self.setMinimumSize(450, 600)
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        # Variables
        self.current_input = ""        # What the user is typing
        self.memory = 0.0
        self.last_result = None
        self.history = []               # List of (expression, result) tuples
        self.evaluator = ExpressionEvaluator()
        self.dark_mode = True

        # Setup UI
        self.init_ui()

        # Apply initial theme
        self.apply_theme()

        # Enable keyboard focus
        self.setFocusPolicy(Qt.StrongFocus)

    def init_ui(self):
        """Create the main layout and all widgets."""
        # Central widget with rounded corners and shadow
        self.central_widget = QWidget()
        self.central_widget.setObjectName("centralWidget")
        self.setCentralWidget(self.central_widget)

        # Main layout
        main_layout = QVBoxLayout(self.central_widget)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(12)

        # --- Custom Title Bar ---
        title_bar = QWidget()
        title_bar.setObjectName("titleBar")
        title_bar_layout = QHBoxLayout(title_bar)
        title_bar_layout.setContentsMargins(10, 5, 10, 5)

        self.title_label = QLabel("AdvancedCalc")
        self.title_label.setObjectName("titleLabel")

        # Minimize button
        self.min_btn = QPushButton("—")
        self.min_btn.setFixedSize(30, 30)
        self.min_btn.setObjectName("titleButton")
        self.min_btn.clicked.connect(self.showMinimized)

        # Close button
        self.close_btn = QPushButton("✕")
        self.close_btn.setFixedSize(30, 30)
        self.close_btn.setObjectName("titleButton")
        self.close_btn.clicked.connect(self.close)

        title_bar_layout.addWidget(self.title_label)
        title_bar_layout.addStretch()
        title_bar_layout.addWidget(self.min_btn)
        title_bar_layout.addWidget(self.close_btn)

        main_layout.addWidget(title_bar)

        # --- History Display ---
        self.history_label = QLabel()
        self.history_label.setObjectName("historyLabel")
        self.history_label.setAlignment(Qt.AlignRight)
        self.history_label.setWordWrap(True)
        self.history_label.setMaximumHeight(60)
        main_layout.addWidget(self.history_label)

        # --- Main Display ---
        self.display = QLineEdit()
        self.display.setObjectName("display")
        self.display.setAlignment(Qt.AlignRight)
        self.display.setReadOnly(True)
        self.display.setMinimumHeight(80)
        self.display.setFont(QFont("Segoe UI", 28, QFont.Bold))

        # Shadow effect
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 80))
        shadow.setOffset(0, 4)
        self.display.setGraphicsEffect(shadow)

        main_layout.addWidget(self.display)

        # --- Buttons Grid ---
        button_grid = QGridLayout()
        button_grid.setSpacing(12)

        # Define buttons: (text, row, col, rowspan, colspan, special_class)
        buttons = [
            ("CE", 0, 0, 1, 1, "clear_entry"),
            ("C", 0, 1, 1, 1, "clear"),
            ("√", 0, 2, 1, 1, "func"),
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
            ("x²", 4, 3, 1, 1, "func"),
            ("1/x", 5, 0, 1, 1, "func"),
            ("xʸ", 5, 1, 1, 1, "func"),
            ("%", 5, 2, 1, 1, "func"),
            ("=", 5, 3, 1, 1, "equals"),
            ("M+", 6, 0, 1, 1, "memory"),
            ("M-", 6, 1, 1, 1, "memory"),
            ("MR", 6, 2, 1, 1, "memory"),
            ("MC", 6, 3, 1, 1, "memory"),
            ("(", 7, 0, 1, 1, "paren"),
            (")", 7, 1, 1, 1, "paren"),
            ("^", 7, 2, 1, 1, "func"),
            ("Theme", 7, 3, 1, 1, "theme"),
        ]

        # Create buttons
        for text, row, col, rowspan, colspan, btn_type in buttons:
            btn = QPushButton(text)
            btn.setObjectName(btn_type)
            btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            if text == "0":
                btn.setFixedHeight(70)
            else:
                btn.setMinimumHeight(60)
            btn.clicked.connect(self.on_button_clicked)
            button_grid.addWidget(btn, row, col, rowspan, colspan)

        main_layout.addLayout(button_grid)

        # Make the grid stretch proportionally
        for i in range(8):
            button_grid.setRowStretch(i, 1)
        for j in range(4):
            button_grid.setColumnStretch(j, 1)

        # Enable mouse dragging for the title bar
        self.title_bar = title_bar
        self.drag_pos = None

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and self.title_bar.geometry().contains(event.pos()):
            self.drag_pos = event.globalPosition().toPoint()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton and self.drag_pos is not None:
            self.move(self.pos() + event.globalPosition().toPoint() - self.drag_pos)
            self.drag_pos = event.globalPosition().toPoint()
            event.accept()

    def mouseReleaseEvent(self, event):
        self.drag_pos = None

    def on_button_clicked(self):
        btn = self.sender()
        text = btn.text()

        # Handle special buttons
        if text == "C":
            self.clear_all()
        elif text == "CE":
            self.clear_entry()
        elif text == "=":
            self.evaluate_expression()
        elif text == "√":
            self.apply_unary_function(math.sqrt)
        elif text == "x²":
            self.apply_unary_function(lambda x: x ** 2)
        elif text == "1/x":
            self.apply_unary_function(lambda x: 1 / x if x != 0 else float('inf'))
        elif text == "xʸ":
            # Will be handled as binary operator: we add '^' to input
            self.append_operator('^')
        elif text == "%":
            self.apply_percentage()
        elif text == "M+":
            self.memory_add()
        elif text == "M-":
            self.memory_subtract()
        elif text == "MR":
            self.memory_recall()
        elif text == "MC":
            self.memory_clear()
        elif text == "Theme":
            self.toggle_theme()
        elif text in "()":
            self.append_text(text)
        elif text in "0123456789.":
            self.append_digit(text)
        elif text in "+-×÷":
            op_map = {"×": "*", "÷": "/"}
            self.append_operator(op_map.get(text, text))
        elif text == "^":
            self.append_operator('^')
        else:
            # Fallback: just append text
            self.append_text(text)

        # Update display
        self.display.setText(self.current_input if self.current_input else "0")
        self.update_history_display()

    def clear_all(self):
        self.current_input = ""
        self.last_result = None

    def clear_entry(self):
        # Remove the last number/operator? We'll just clear the current input.
        self.current_input = ""

    def append_digit(self, digit):
        if digit == "." and self.current_input.count(".") > 0:
            return
        self.current_input += digit

    def append_operator(self, op):
        # Prevent consecutive operators
        if self.current_input and self.current_input[-1] in "+-*/^":
            self.current_input = self.current_input[:-1] + op
        else:
            self.current_input += op

    def append_text(self, text):
        self.current_input += text

    def evaluate_expression(self):
        if not self.current_input:
            return
        try:
            result = self.evaluator.evaluate(self.current_input)
            # Store history
            self.history.append((self.current_input, result))
            if len(self.history) > 5:
                self.history.pop(0)
            self.current_input = str(result)
            self.last_result = result
        except ZeroDivisionError:
            self.current_input = "Error: Division by zero"
        except Exception as e:
            self.current_input = "Error"
        self.update_history_display()

    def apply_unary_function(self, func):
        if self.current_input:
            try:
                val = float(self.current_input)
                result = func(val)
                self.current_input = str(result)
                self.last_result = result
            except Exception:
                self.current_input = "Error"

    def apply_percentage(self):
        if self.current_input:
            try:
                val = float(self.current_input)
                result = val / 100.0
                self.current_input = str(result)
                self.last_result = result
            except Exception:
                self.current_input = "Error"

    def memory_add(self):
        if self.current_input:
            try:
                val = float(self.current_input)
                self.memory += val
            except:
                pass

    def memory_subtract(self):
        if self.current_input:
            try:
                val = float(self.current_input)
                self.memory -= val
            except:
                pass

    def memory_recall(self):
        self.current_input = str(self.memory)

    def memory_clear(self):
        self.memory = 0.0

    def update_history_display(self):
        if not self.history:
            self.history_label.setText("")
            return
        text = "<br>".join([f"{expr} = {res}" for expr, res in self.history])
        self.history_label.setText(text)

    def toggle_theme(self):
        self.dark_mode = not self.dark_mode
        self.apply_theme()

    def apply_theme(self):
        if self.dark_mode:
            # Dark theme
            self.setStyleSheet("""
                QWidget#centralWidget {
                    background-color: #1e1e2f;
                    border-radius: 20px;
                }
                QPushButton {
                    background-color: #2c2f36;
                    color: #ffffff;
                    border: none;
                    border-radius: 20px;
                    font-weight: bold;
                    font-size: 20px;
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
                QPushButton#clear, QPushButton#clear_entry {
                    background-color: #f44336;
                    color: white;
                }
                QPushButton#clear:hover, QPushButton#clear_entry:hover {
                    background-color: #ff6659;
                }
                QPushButton#equals {
                    background-color: #4caf50;
                    color: white;
                }
                QPushButton#equals:hover {
                    background-color: #6fbf73;
                }
                QPushButton#func, QPushButton#memory, QPushButton#paren, QPushButton#theme {
                    background-color: #3f51b5;
                    color: white;
                }
                QPushButton#func:hover, QPushButton#memory:hover, QPushButton#paren:hover, QPushButton#theme:hover {
                    background-color: #5c6bc0;
                }
                QLineEdit#display {
                    background-color: rgba(30, 30, 47, 200);
                    color: #ffffff;
                    border: none;
                    border-radius: 30px;
                    padding: 15px;
                }
                QLabel#historyLabel {
                    color: #aaaaaa;
                    font-size: 12px;
                }
                QWidget#titleBar {
                    background-color: rgba(30, 30, 47, 150);
                    border-top-left-radius: 20px;
                    border-top-right-radius: 20px;
                }
                QLabel#titleLabel {
                    color: #ffffff;
                    font-size: 16px;
                }
                QPushButton#titleButton {
                    background-color: transparent;
                    color: #ffffff;
                    font-size: 16px;
                    border-radius: 15px;
                }
                QPushButton#titleButton:hover {
                    background-color: #3e424b;
                }
            """)
        else:
            # Light theme
            self.setStyleSheet("""
                QWidget#centralWidget {
                    background-color: #f5f5f5;
                    border-radius: 20px;
                }
                QPushButton {
                    background-color: #e0e0e0;
                    color: #212121;
                    border: none;
                    border-radius: 20px;
                    font-weight: bold;
                    font-size: 20px;
                }
                QPushButton:hover {
                    background-color: #d5d5d5;
                }
                QPushButton:pressed {
                    background-color: #c0c0c0;
                }
                QPushButton#operator {
                    background-color: #ff9800;
                    color: white;
                }
                QPushButton#operator:hover {
                    background-color: #ffb74d;
                }
                QPushButton#clear, QPushButton#clear_entry {
                    background-color: #f44336;
                    color: white;
                }
                QPushButton#clear:hover, QPushButton#clear_entry:hover {
                    background-color: #ff6659;
                }
                QPushButton#equals {
                    background-color: #4caf50;
                    color: white;
                }
                QPushButton#equals:hover {
                    background-color: #6fbf73;
                }
                QPushButton#func, QPushButton#memory, QPushButton#paren, QPushButton#theme {
                    background-color: #3f51b5;
                    color: white;
                }
                QPushButton#func:hover, QPushButton#memory:hover, QPushButton#paren:hover, QPushButton#theme:hover {
                    background-color: #5c6bc0;
                }
                QLineEdit#display {
                    background-color: white;
                    color: #212121;
                    border: 1px solid #cccccc;
                    border-radius: 30px;
                    padding: 15px;
                }
                QLabel#historyLabel {
                    color: #666666;
                    font-size: 12px;
                }
                QWidget#titleBar {
                    background-color: rgba(245, 245, 245, 200);
                    border-top-left-radius: 20px;
                    border-top-right-radius: 20px;
                }
                QLabel#titleLabel {
                    color: #212121;
                    font-size: 16px;
                }
                QPushButton#titleButton {
                    background-color: transparent;
                    color: #212121;
                    font-size: 16px;
                    border-radius: 15px;
                }
                QPushButton#titleButton:hover {
                    background-color: #c0c0c0;
                }
            """)

    def keyPressEvent(self, event):
        key = event.key()
        text = event.text()

        # Handle special keys
        if key == Qt.Key_Backspace or key == Qt.Key_Delete:
            self.current_input = self.current_input[:-1]
            self.display.setText(self.current_input or "0")
        elif key == Qt.Key_Return or key == Qt.Key_Enter:
            self.evaluate_expression()
            self.display.setText(self.current_input)
        elif key == Qt.Key_Escape:
            self.clear_all()
            self.display.setText("0")
        elif key == Qt.Key_AsciiCircum:   # ^ key
            self.append_operator('^')
            self.display.setText(self.current_input)
        elif text.isdigit() or text == '.':
            self.append_digit(text)
            self.display.setText(self.current_input)
        elif text in '+-*/':
            op_map = {'*': '*', '/': '/'}
            self.append_operator(op_map.get(text, text))
            self.display.setText(self.current_input)
        elif text == '(' or text == ')':
            self.append_text(text)
            self.display.setText(self.current_input)
        elif text == 'm' or text == 'M':
            # Memory recall? But we have specific keys; we'll do MR if M is pressed
            # Simpler: just handle MR with a custom key
            pass
        else:
            super().keyPressEvent(event)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = ModernCalculator()
    window.show()
    sys.exit(app.exec())