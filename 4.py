import sys
import math
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QRect, QPoint
from PySide6.QtGui import QFont, QColor, QLinearGradient, QAction
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                               QHBoxLayout, QGridLayout, QPushButton, QLineEdit,
                               QLabel, QGraphicsDropShadowEffect, QSizePolicy,
                               QScrollArea, QFrame)


class ExpressionEvaluator:
    """
    Advanced evaluator supporting:
    - Operators: + - * / ^ % (binary)
    - Functions: sin, cos, tan, asin, acos, atan, log (base 10), ln (natural log),
                 sqrt, exp (e^x), abs, factorial
    - Constants: pi, e
    - Parentheses
    - Unary minus
    """
    def __init__(self):
        # Precedence and associativity for operators and functions
        self.precedence = {
            '+': 1, '-': 1,
            '*': 2, '/': 2,
            '^': 3,
            '%': 2,          # modulo
            '!': 4,          # factorial (postfix, but treat as unary with high precedence)
            '√': 4,          # square root (unary)
            '±': 4,          # unary minus
            'sin': 4, 'cos': 4, 'tan': 4,
            'asin': 4, 'acos': 4, 'atan': 4,
            'log': 4, 'ln': 4,
            'exp': 4, 'sqrt': 4, 'abs': 4,
        }
        self.associativity = {
            '+': 'L', '-': 'L',
            '*': 'L', '/': 'L',
            '^': 'R',
            '%': 'L',
            '!': 'R',
            '√': 'R',
            '±': 'R',
            'sin': 'R', 'cos': 'R', 'tan': 'R',
            'asin': 'R', 'acos': 'R', 'atan': 'R',
            'log': 'R', 'ln': 'R',
            'exp': 'R', 'sqrt': 'R', 'abs': 'R',
        }
        # Constants
        self.constants = {
            'pi': math.pi,
            'e': math.e,
        }

    def tokenize(self, expression):
        """
        Convert expression string into a list of tokens:
        numbers, operators, functions, parentheses, constants.
        """
        tokens = []
        i = 0
        n = len(expression)
        while i < n:
            ch = expression[i]
            if ch.isdigit() or ch == '.':
                # Number
                j = i
                while j < n and (expression[j].isdigit() or expression[j] == '.'):
                    j += 1
                tokens.append(expression[i:j])
                i = j
            elif ch.isalpha():
                # Function name or constant
                j = i
                while j < n and expression[j].isalpha():
                    j += 1
                name = expression[i:j]
                if name in self.constants:
                    tokens.append(name)       # constant
                else:
                    tokens.append(name)       # function name (to be handled later)
                i = j
            elif ch in '+-*/^%()!√':   # √ is a special character; we'll treat it as a function
                # Operators and parentheses
                if ch == '√':
                    tokens.append('sqrt')   # map √ to sqrt function
                else:
                    tokens.append(ch)
                i += 1
            else:
                # Skip whitespace or unknown characters
                i += 1
        return tokens

    def apply_operator(self, operators, values):
        """Apply the top operator from the stack to the values stack."""
        op = operators.pop()
        # Handle unary operators/functions first
        if op in ('√', '±', 'sin', 'cos', 'tan', 'asin', 'acos', 'atan',
                  'log', 'ln', 'exp', 'sqrt', 'abs', '!'):
            # Unary: pop one value, apply function, push result
            val = values.pop()
            if op == '√':
                res = math.sqrt(val)
            elif op == '±':
                res = -val
            elif op == 'sin':
                res = math.sin(math.radians(val)) if val != 0 else 0  # assume degrees
            elif op == 'cos':
                res = math.cos(math.radians(val))
            elif op == 'tan':
                res = math.tan(math.radians(val))
            elif op == 'asin':
                res = math.degrees(math.asin(val)) if -1 <= val <= 1 else float('nan')
            elif op == 'acos':
                res = math.degrees(math.acos(val)) if -1 <= val <= 1 else float('nan')
            elif op == 'atan':
                res = math.degrees(math.atan(val))
            elif op == 'log':
                res = math.log10(val) if val > 0 else float('nan')
            elif op == 'ln':
                res = math.log(val) if val > 0 else float('nan')
            elif op == 'exp':
                res = math.exp(val)
            elif op == 'sqrt':
                res = math.sqrt(val) if val >= 0 else float('nan')
            elif op == 'abs':
                res = abs(val)
            elif op == '!':
                # factorial: only for non-negative integers
                if val < 0 or val != int(val):
                    raise ValueError("Factorial of non-integer or negative")
                res = math.factorial(int(val))
            else:
                raise ValueError(f"Unknown unary operator: {op}")
            values.append(res)
        else:
            # Binary operator
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
                values.append(left % right)
            else:
                raise ValueError(f"Unknown binary operator: {op}")

    def evaluate(self, expression):
        """Evaluate the given expression and return a numeric result."""
        tokens = self.tokenize(expression)
        values = []
        operators = []

        for token in tokens:
            # Number or constant
            if token.replace('.', '').isdigit():
                values.append(float(token))
            elif token in self.constants:
                values.append(self.constants[token])
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
                    token = '±'
                # While there is an operator on top with greater or equal precedence
                while (operators and operators[-1] != '(' and
                       (self.precedence[operators[-1]] > self.precedence[token] or
                        (self.precedence[operators[-1]] == self.precedence[token] and
                         self.associativity[token] == 'L'))):
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


class ScientificCalculator(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SciCalc Pro")
        self.setMinimumSize(650, 750)
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        # State variables
        self.current_input = ""
        self.memory = 0.0
        self.last_result = None
        self.history = []           # (expression, result)
        self.evaluator = ExpressionEvaluator()
        self.dark_mode = True
        self.scientific_mode = False   # start in basic mode

        self.setup_ui()
        self.apply_theme()
        self.setFocusPolicy(Qt.StrongFocus)

    # ----------------------------- UI Setup ---------------------------------
    def setup_ui(self):
        central = QWidget()
        central.setObjectName("centralWidget")
        self.setCentralWidget(central)

        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(12)

        # Title bar
        self.title_bar = QWidget()
        self.title_bar.setObjectName("titleBar")
        title_layout = QHBoxLayout(self.title_bar)
        title_layout.setContentsMargins(10, 5, 10, 5)

        self.title_label = QLabel("SciCalc Pro")
        self.title_label.setObjectName("titleLabel")

        self.min_btn = QPushButton("—")
        self.min_btn.setFixedSize(30, 30)
        self.min_btn.setObjectName("titleButton")
        self.min_btn.clicked.connect(self.showMinimized)

        self.close_btn = QPushButton("✕")
        self.close_btn.setFixedSize(30, 30)
        self.close_btn.setObjectName("titleButton")
        self.close_btn.clicked.connect(self.close)

        title_layout.addWidget(self.title_label)
        title_layout.addStretch()
        title_layout.addWidget(self.min_btn)
        title_layout.addWidget(self.close_btn)

        main_layout.addWidget(self.title_bar)

        # History display (clickable)
        self.history_label = QLabel()
        self.history_label.setObjectName("historyLabel")
        self.history_label.setAlignment(Qt.AlignRight)
        self.history_label.setWordWrap(True)
        self.history_label.setMaximumHeight(80)
        self.history_label.setOpenExternalLinks(False)
        self.history_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        main_layout.addWidget(self.history_label)

        # Main display
        self.display = QLineEdit()
        self.display.setObjectName("display")
        self.display.setAlignment(Qt.AlignRight)
        self.display.setReadOnly(True)
        self.display.setMinimumHeight(90)
        self.display.setFont(QFont("Segoe UI", 32, QFont.Bold))

        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 80))
        shadow.setOffset(0, 4)
        self.display.setGraphicsEffect(shadow)

        main_layout.addWidget(self.display)

        # Mode switch button
        mode_btn = QPushButton("Scientific Mode")
        mode_btn.setObjectName("modeButton")
        mode_btn.setToolTip("Switch between Basic and Scientific modes")
        mode_btn.clicked.connect(self.toggle_mode)
        main_layout.addWidget(mode_btn)

        # Scroll area for buttons (allows many buttons without overflow)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        main_layout.addWidget(scroll)

        self.button_container = QWidget()
        self.button_layout = QVBoxLayout(self.button_container)
        self.button_layout.setSpacing(12)
        scroll.setWidget(self.button_container)

        # Create basic and scientific button sets
        self.basic_buttons = self.create_basic_buttons()
        self.scientific_buttons = self.create_scientific_buttons()
        self.current_buttons = self.basic_buttons
        self.button_layout.addWidget(self.current_buttons)

    def create_basic_buttons(self):
        """Grid of basic calculator buttons (no trig/log)"""
        widget = QWidget()
        grid = QGridLayout(widget)
        grid.setSpacing(12)

        # Basic buttons (7x4)
        buttons = [
            ("CE", 0, 0), ("C", 0, 1), ("√", 0, 2), ("÷", 0, 3),
            ("7", 1, 0), ("8", 1, 1), ("9", 1, 2), ("×", 1, 3),
            ("4", 2, 0), ("5", 2, 1), ("6", 2, 2), ("-", 2, 3),
            ("1", 3, 0), ("2", 3, 1), ("3", 3, 2), ("+", 3, 3),
            ("0", 4, 0), (".", 4, 1), ("±", 4, 2), ("=", 4, 3),
            ("%", 5, 0), ("x²", 5, 1), ("xʸ", 5, 2), ("(", 5, 3),
            (")", 6, 0), ("^", 6, 1), ("Theme", 6, 2), ("MC", 6, 3),
            ("M+", 7, 0), ("M-", 7, 1), ("MR", 7, 2),
        ]

        for text, row, col in buttons:
            btn = self.create_button(text, row, col)
            grid.addWidget(btn, row, col)
            if text == "0":
                grid.setColumnStretch(0, 2)  # span two columns? Actually handled by layout
                # Let's manually set span later if needed; for now it's fine.

        # Make rows and columns stretch
        for i in range(8):
            grid.setRowStretch(i, 1)
        for j in range(4):
            grid.setColumnStretch(j, 1)

        return widget

    def create_scientific_buttons(self):
        """Extended grid with scientific functions"""
        widget = QWidget()
        grid = QGridLayout(widget)
        grid.setSpacing(12)

        # Scientific buttons: many rows
        buttons = [
            # Row 0
            ("CE", 0, 0), ("C", 0, 1), ("√", 0, 2), ("÷", 0, 3),
            # Row 1
            ("7", 1, 0), ("8", 1, 1), ("9", 1, 2), ("×", 1, 3),
            # Row 2
            ("4", 2, 0), ("5", 2, 1), ("6", 2, 2), ("-", 2, 3),
            # Row 3
            ("1", 3, 0), ("2", 3, 1), ("3", 3, 2), ("+", 3, 3),
            # Row 4
            ("0", 4, 0), (".", 4, 1), ("±", 4, 2), ("=", 4, 3),
            # Row 5 - scientific
            ("sin", 5, 0), ("cos", 5, 1), ("tan", 5, 2), ("^", 5, 3),
            ("asin", 6, 0), ("acos", 6, 1), ("atan", 6, 2), ("log", 6, 3),
            ("ln", 7, 0), ("exp", 7, 1), ("abs", 7, 2), ("!", 7, 3),
            ("π", 8, 0), ("e", 8, 1), ("x²", 8, 2), ("1/x", 8, 3),
            ("%", 9, 0), ("xʸ", 9, 1), ("(", 9, 2), (")", 9, 3),
            ("Theme", 10, 0), ("MC", 10, 1), ("M+", 10, 2), ("M-", 10, 3),
            ("MR", 11, 0),
        ]

        for text, row, col in buttons:
            btn = self.create_button(text, row, col)
            grid.addWidget(btn, row, col)

        # Stretch
        for i in range(12):
            grid.setRowStretch(i, 1)
        for j in range(4):
            grid.setColumnStretch(j, 1)

        return widget

    def create_button(self, text, row, col):
        """Create a button with appropriate styling and connect to click handler"""
        btn = QPushButton(text)
        btn.setObjectName(self.get_button_type(text))
        btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        btn.setMinimumHeight(55)
        btn.setToolTip(self.get_tooltip(text))
        btn.clicked.connect(self.on_button_click)
        # Animation (scale) will be applied on click in the handler
        return btn

    def get_button_type(self, text):
        """Return a class name for CSS styling based on button text."""
        if text in ("+", "-", "×", "÷", "^", "%", "xʸ"):
            return "operator"
        elif text in ("C", "CE"):
            return "clear"
        elif text == "=":
            return "equals"
        elif text in ("M+", "M-", "MR", "MC"):
            return "memory"
        elif text in ("sin", "cos", "tan", "asin", "acos", "atan", "log", "ln",
                      "exp", "sqrt", "abs", "!", "x²", "1/x", "√", "π", "e"):
            return "func"
        elif text in ("(", ")"):
            return "paren"
        elif text == "Theme":
            return "theme"
        else:
            return "digit"

    def get_tooltip(self, text):
        """Provide informative tooltips for buttons."""
        tooltips = {
            "CE": "Clear Entry (current input)",
            "C": "Clear All",
            "√": "Square root (sqrt)",
            "÷": "Division",
            "×": "Multiplication",
            "-": "Subtraction",
            "+": "Addition",
            "=": "Evaluate expression",
            "±": "Toggle sign",
            "%": "Percent",
            "x²": "Square",
            "xʸ": "Exponentiation (power)",
            "^": "Exponentiation (power)",
            "(": "Open parenthesis",
            ")": "Close parenthesis",
            "Theme": "Switch between light and dark theme",
            "MC": "Memory Clear",
            "M+": "Memory Add",
            "M-": "Memory Subtract",
            "MR": "Memory Recall",
            "sin": "Sine (in degrees)",
            "cos": "Cosine (in degrees)",
            "tan": "Tangent (in degrees)",
            "asin": "Arcsine (result in degrees)",
            "acos": "Arccosine (result in degrees)",
            "atan": "Arctangent (result in degrees)",
            "log": "Base‑10 logarithm",
            "ln": "Natural logarithm",
            "exp": "e^x",
            "abs": "Absolute value",
            "!": "Factorial (n!)",
            "π": "Pi constant",
            "e": "Euler's number",
            "1/x": "Reciprocal",
        }
        return tooltips.get(text, "")

    # ----------------------------- Button Actions ----------------------------
    def on_button_click(self):
        btn = self.sender()
        text = btn.text()

        # Animate button press
        self.animate_button(btn)

        # Handle special actions
        if text == "C":
            self.clear_all()
        elif text == "CE":
            self.clear_entry()
        elif text == "=":
            self.evaluate()
        elif text == "±":
            self.toggle_sign()
        elif text == "Theme":
            self.toggle_theme()
        elif text in ("M+", "M-", "MR", "MC"):
            self.memory_action(text)
        elif text in ("π", "e"):
            self.append_constant(text)
        elif text in ("sin", "cos", "tan", "asin", "acos", "atan",
                      "log", "ln", "exp", "abs", "!"):
            self.append_function(text)
        elif text == "√":
            self.append_function("sqrt")
        elif text == "x²":
            self.append_function("sq")
        elif text == "1/x":
            self.append_function("recip")
        elif text in ("xʸ", "^"):
            self.append_operator("^")
        elif text == "%":
            self.apply_percentage()
        elif text in "0123456789.":
            self.append_digit(text)
        elif text in "+-×÷":
            op_map = {"×": "*", "÷": "/"}
            self.append_operator(op_map.get(text, text))
        elif text in "()":
            self.append_text(text)
        else:
            # Fallback: just append text
            self.append_text(text)

        # Update display
        self.display.setText(self.current_input if self.current_input else "0")
        self.update_history_display()

    def animate_button(self, button):
        """Quick scale animation on button press."""
        anim = QPropertyAnimation(button, b"geometry")
        anim.setDuration(100)
        anim.setEasingCurve(QEasingCurve.OutQuad)
        original = button.geometry()
        scaled = QRect(original.x() + 5, original.y() + 5,
                       original.width() - 10, original.height() - 10)
        anim.setKeyValueAt(0, original)
        anim.setKeyValueAt(0.5, scaled)
        anim.setKeyValueAt(1, original)
        anim.start()

    # ----------------------------- Input Handling ----------------------------
    def clear_all(self):
        self.current_input = ""
        self.last_result = None

    def clear_entry(self):
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

    def append_function(self, func):
        """Append a function name and opening parenthesis."""
        self.current_input += func + "("

    def append_constant(self, const):
        self.current_input += const

    def toggle_sign(self):
        if self.current_input:
            try:
                val = float(self.current_input)
                val = -val
                self.current_input = str(int(val) if val.is_integer() else val)
            except:
                pass

    def apply_percentage(self):
        if self.current_input:
            try:
                val = float(self.current_input)
                result = val / 100.0
                self.current_input = str(result)
                self.last_result = result
            except:
                self.current_input = "Error"

    # ----------------------------- Evaluation -------------------------------
    def evaluate(self):
        if not self.current_input:
            return
        try:
            result = self.evaluator.evaluate(self.current_input)
            # Store in history
            self.history.append((self.current_input, result))
            if len(self.history) > 10:
                self.history.pop(0)
            self.current_input = str(result)
            self.last_result = result
        except ZeroDivisionError:
            self.current_input = "Error: Division by zero"
        except Exception as e:
            self.current_input = f"Error: {str(e)}"
        self.update_history_display()

    # ----------------------------- Memory -----------------------------------
    def memory_action(self, action):
        if action == "M+":
            if self.current_input:
                try:
                    self.memory += float(self.current_input)
                except:
                    pass
        elif action == "M-":
            if self.current_input:
                try:
                    self.memory -= float(self.current_input)
                except:
                    pass
        elif action == "MR":
            self.current_input = str(self.memory)
        elif action == "MC":
            self.memory = 0.0
        self.display.setText(self.current_input)

    # ----------------------------- History ----------------------------------
    def update_history_display(self):
        if not self.history:
            self.history_label.setText("")
            return
        # Create clickable links? We'll use simple HTML and make them selectable.
        # For interaction, we can add a mousePressEvent on the label, but that's more complex.
        # Instead, we'll just show plain text.
        text = "<br>".join([f"{expr} = {res}" for expr, res in self.history[-5:]])
        self.history_label.setText(text)

    # ----------------------------- Mode Toggle ------------------------------
    def toggle_mode(self):
        self.scientific_mode = not self.scientific_mode
        # Remove current button widget
        for i in reversed(range(self.button_layout.count())):
            self.button_layout.itemAt(i).widget().setParent(None)
        # Add new set
        if self.scientific_mode:
            self.current_buttons = self.scientific_buttons
            self.findChild(QPushButton, "modeButton").setText("Basic Mode")
        else:
            self.current_buttons = self.basic_buttons
            self.findChild(QPushButton, "modeButton").setText("Scientific Mode")
        self.button_layout.addWidget(self.current_buttons)

    # ----------------------------- Theme Toggle -----------------------------
    def toggle_theme(self):
        self.dark_mode = not self.dark_mode
        self.apply_theme()

    def apply_theme(self):
        if self.dark_mode:
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
                    font-size: 16px;
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
                QPushButton#func, QPushButton#memory, QPushButton#paren, QPushButton#theme, QPushButton#modeButton {
                    background-color: #3f51b5;
                    color: white;
                }
                QPushButton#func:hover, QPushButton#memory:hover, QPushButton#paren:hover, QPushButton#theme:hover, QPushButton#modeButton:hover {
                    background-color: #5c6bc0;
                }
                QLineEdit#display {
                    background-color: rgba(30, 30, 47, 200);
                    color: #ffffff;
                    border: none;
                    border-radius: 30px;
                    padding: 15px;
                    font-size: 32px;
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
                QScrollArea {
                    background: transparent;
                    border: none;
                }
            """)
        else:
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
                    font-size: 16px;
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
                QPushButton#func, QPushButton#memory, QPushButton#paren, QPushButton#theme, QPushButton#modeButton {
                    background-color: #3f51b5;
                    color: white;
                }
                QPushButton#func:hover, QPushButton#memory:hover, QPushButton#paren:hover, QPushButton#theme:hover, QPushButton#modeButton:hover {
                    background-color: #5c6bc0;
                }
                QLineEdit#display {
                    background-color: white;
                    color: #212121;
                    border: 1px solid #cccccc;
                    border-radius: 30px;
                    padding: 15px;
                    font-size: 32px;
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
                QScrollArea {
                    background: transparent;
                    border: none;
                }
            """)

    # ----------------------------- Window Dragging --------------------------
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and self.title_bar.geometry().contains(event.pos()):
            self.drag_pos = event.globalPosition().toPoint()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton and hasattr(self, 'drag_pos') and self.drag_pos is not None:
            self.move(self.pos() + event.globalPosition().toPoint() - self.drag_pos)
            self.drag_pos = event.globalPosition().toPoint()
            event.accept()

    def mouseReleaseEvent(self, event):
        self.drag_pos = None

    # ----------------------------- Keyboard Handling -------------------------
    def keyPressEvent(self, event):
        key = event.key()
        text = event.text()

        if key == Qt.Key_Backspace or key == Qt.Key_Delete:
            self.current_input = self.current_input[:-1]
        elif key == Qt.Key_Return or key == Qt.Key_Enter:
            self.evaluate()
        elif key == Qt.Key_Escape:
            self.clear_all()
        elif key == Qt.Key_AsciiCircum:   # ^
            self.append_operator('^')
        elif text.isdigit() or text == '.':
            self.append_digit(text)
        elif text in '+-*/':
            op_map = {'*': '*', '/': '/'}
            self.append_operator(op_map.get(text, text))
        elif text == '(' or text == ')':
            self.append_text(text)
        elif text == 's' and event.modifiers() == Qt.NoModifier:
            self.append_function('sin')
        elif text == 'c':
            self.append_function('cos')
        elif text == 't':
            self.append_function('tan')
        elif text == 'l':
            self.append_function('log')
        elif text == 'n':
            self.append_function('ln')
        elif text == 'p':
            self.append_constant('π')
        elif text == 'e':
            self.append_constant('e')
        elif key == Qt.Key_M:
            self.memory_action("MR")
        elif key == Qt.Key_R and event.modifiers() == Qt.ControlModifier:
            self.memory_action("MC")
        else:
            super().keyPressEvent(event)

        self.display.setText(self.current_input if self.current_input else "0")
        self.update_history_display()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = ScientificCalculator()
    window.show()
    sys.exit(app.exec())