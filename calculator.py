"""Safe mathematical expression parser and evaluator.

Implements a tokenizer + shunting-yard algorithm to convert infix expressions
to Reverse Polish Notation (RPN), then evaluates the RPN stack.

Security: no ``eval``/``exec`` is used. Only a fixed whitelist of operators,
functions and constants is supported. Arbitrary code execution is impossible
because the parser never compiles or executes user-supplied strings.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum
from typing import Callable


class TokenType(Enum):
    NUMBER = "number"
    OPERATOR = "operator"
    FUNCTION = "function"
    CONSTANT = "constant"
    LPAREN = "lparen"
    RPAREN = "rparen"
    COMMA = "comma"


@dataclass
class Token:
    type: TokenType
    value: str


# Operator precedence (higher = binds tighter) and associativity.
OPERATORS: dict[str, dict] = {
    "+": {"precedence": 1, "assoc": "left", "arity": 2},
    "-": {"precedence": 1, "assoc": "left", "arity": 2},
    "*": {"precedence": 2, "assoc": "left", "arity": 2},
    "/": {"precedence": 2, "assoc": "left", "arity": 2},
    "%": {"precedence": 2, "assoc": "left", "arity": 2},
    "^": {"precedence": 4, "assoc": "right", "arity": 2},
    "u-": {"precedence": 3, "assoc": "right", "arity": 1},  # unary minus
}

# Supported mathematical constants.
CONSTANTS: dict[str, float] = {
    "pi": math.pi,
    "e": math.e,
    "tau": math.tau,
}

# Supported single-argument functions.
FUNCTIONS: dict[str, Callable[[float], float]] = {
    "sin": math.sin,
    "cos": math.cos,
    "tan": math.tan,
    "asin": math.asin,
    "acos": math.acos,
    "atan": math.atan,
    "sinh": math.sinh,
    "cosh": math.cosh,
    "tanh": math.tanh,
    "sqrt": math.sqrt,
    "cbrt": lambda x: math.copysign(abs(x) ** (1 / 3), x),
    "exp": math.exp,
    "ln": math.log,
    "log": math.log10,
    "log2": math.log2,
    "abs": abs,
    "floor": math.floor,
    "ceil": math.ceil,
    "round": round,
    "fact": lambda x: math.factorial(int(x)) if float(x).is_integer() and x >= 0 else float("nan"),
}

# Two-argument functions (e.g. pow, log with custom base).
FUNCTIONS_2: dict[str, Callable[[float, float], float]] = {
    "pow": math.pow,
    "log": math.log,  # log(x, base)
    "min": min,
    "max": max,
}

MAX_EXPRESSION_LENGTH = 512
ALLOWED_CHARS = set("0123456789.+-*/^%(), abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_")


class CalculatorError(Exception):
    """Raised when an expression cannot be parsed or evaluated."""


def tokenize(expression: str) -> list[Token]:
    """Convert an expression string into a list of tokens."""
    if len(expression) > MAX_EXPRESSION_LENGTH:
        raise CalculatorError(f"表达式过长（最多 {MAX_EXPRESSION_LENGTH} 个字符）")

    expression = expression.strip()
    if not expression:
        raise CalculatorError("表达式不能为空")

    # Reject any character outside the allowed set (defense in depth).
    for ch in expression:
        if ch not in ALLOWED_CHARS:
            raise CalculatorError(f"非法字符: '{ch}'")

    tokens: list[Token] = []
    i = 0
    n = len(expression)
    while i < n:
        ch = expression[i]

        if ch.isspace():
            i += 1
            continue

        # Number (integer or decimal, optionally with exponent).
        if ch.isdigit() or ch == ".":
            j = i
            has_dot = False
            has_exp = False
            while j < n and (expression[j].isdigit() or expression[j] in ".eE"):
                if expression[j] == ".":
                    if has_dot or has_exp:
                        break
                    has_dot = True
                elif expression[j] in "eE":
                    if has_exp:
                        break
                    has_exp = True
                    # optional sign after exponent
                    if j + 1 < n and expression[j + 1] in "+-":
                        j += 1
                j += 1
            num_str = expression[i:j]
            # Validate the number is well-formed.
            try:
                float(num_str)
            except ValueError as exc:
                raise CalculatorError(f"无效数字: '{num_str}'") from exc
            tokens.append(Token(TokenType.NUMBER, num_str))
            i = j
            continue

        # Identifier (function or constant).
        if ch.isalpha() or ch == "_":
            j = i
            while j < n and (expression[j].isalnum() or expression[j] == "_"):
                j += 1
            name = expression[i:j].lower()
            if name in FUNCTIONS or name in FUNCTIONS_2:
                tokens.append(Token(TokenType.FUNCTION, name))
            elif name in CONSTANTS:
                tokens.append(Token(TokenType.CONSTANT, name))
            else:
                raise CalculatorError(f"未知标识符: '{name}'")
            i = j
            continue

        # Operators and punctuation.
        if ch in "+-*/%^":
            # Detect unary minus/plus: at start, after an operator, or after '(' / ','.
            if ch in "+-" and (
                not tokens
                or tokens[-1].type in (TokenType.OPERATOR, TokenType.LPAREN, TokenType.COMMA)
            ):
                if ch == "-":
                    tokens.append(Token(TokenType.OPERATOR, "u-"))
                # unary plus is a no-op, skip it
                i += 1
                continue
            tokens.append(Token(TokenType.OPERATOR, ch))
            i += 1
            continue

        if ch == "(":
            tokens.append(Token(TokenType.LPAREN, ch))
            i += 1
            continue

        if ch == ")":
            tokens.append(Token(TokenType.RPAREN, ch))
            i += 1
            continue

        if ch == ",":
            tokens.append(Token(TokenType.COMMA, ch))
            i += 1
            continue

        raise CalculatorError(f"无法解析的字符: '{ch}'")

    return tokens


def to_rpn(tokens: list[Token]) -> list[Token]:
    """Shunting-yard algorithm: convert infix token list to RPN."""
    output: list[Token] = []
    stack: list[Token] = []

    for token in tokens:
        if token.type in (TokenType.NUMBER, TokenType.CONSTANT):
            output.append(token)

        elif token.type == TokenType.FUNCTION:
            stack.append(token)

        elif token.type == TokenType.OPERATOR:
            op = token.value
            op_info = OPERATORS[op]
            while stack and stack[-1].type in (TokenType.OPERATOR, TokenType.FUNCTION):
                top = stack[-1]
                if top.type == TokenType.FUNCTION:
                    output.append(stack.pop())
                    continue
                top_info = OPERATORS[top.value]
                if (
                    top_info["precedence"] > op_info["precedence"]
                    or (
                        top_info["precedence"] == op_info["precedence"]
                        and op_info["assoc"] == "left"
                    )
                ):
                    output.append(stack.pop())
                else:
                    break
            stack.append(token)

        elif token.type == TokenType.LPAREN:
            stack.append(token)

        elif token.type == TokenType.RPAREN:
            while stack and stack[-1].type != TokenType.LPAREN:
                output.append(stack.pop())
            if not stack:
                raise CalculatorError("括号不匹配：缺少左括号")
            stack.pop()  # discard the left paren
            if stack and stack[-1].type == TokenType.FUNCTION:
                output.append(stack.pop())

        elif token.type == TokenType.COMMA:
            while stack and stack[-1].type != TokenType.LPAREN:
                output.append(stack.pop())
            if not stack:
                raise CalculatorError("逗号使用错误")

    while stack:
        top = stack.pop()
        if top.type in (TokenType.LPAREN, TokenType.RPAREN):
            raise CalculatorError("括号不匹配")
        output.append(top)

    return output


def _apply_operator(op: str, args: list[float]) -> float:
    if op == "+":
        return args[1] + args[0]
    if op == "-":
        return args[1] - args[0]
    if op == "*":
        return args[1] * args[0]
    if op == "/":
        if args[0] == 0:
            raise CalculatorError("除数不能为零")
        return args[1] / args[0]
    if op == "%":
        if args[0] == 0:
            raise CalculatorError("取模运算除数不能为零")
        return math.fmod(args[1], args[0])
    if op == "^":
        return args[1] ** args[0]
    if op == "u-":
        return -args[0]
    raise CalculatorError(f"未知运算符: {op}")


def evaluate_rpn(rpn: list[Token]) -> float:
    """Evaluate an RPN token list and return the numeric result."""
    stack: list[float] = []

    for token in rpn:
        if token.type == TokenType.NUMBER:
            stack.append(float(token.value))
        elif token.type == TokenType.CONSTANT:
            stack.append(CONSTANTS[token.value])
        elif token.type == TokenType.OPERATOR:
            arity = OPERATORS[token.value]["arity"]
            if len(stack) < arity:
                raise CalculatorError("表达式不完整：缺少操作数")
            args = [stack.pop() for _ in range(arity)]
            try:
                result = _apply_operator(token.value, args)
            except (OverflowError, ValueError) as exc:
                raise CalculatorError(f"计算溢出或无效运算: {exc}") from exc
            stack.append(result)
        elif token.type == TokenType.FUNCTION:
            name = token.value
            if name in FUNCTIONS_2:
                if len(stack) < 2:
                    raise CalculatorError(f"函数 {name} 需要两个参数")
                b = stack.pop()
                a = stack.pop()
                try:
                    result = FUNCTIONS_2[name](a, b)
                except (ValueError, ZeroDivisionError, OverflowError) as exc:
                    raise CalculatorError(f"函数 {name} 计算失败: {exc}") from exc
                stack.append(result)
            else:
                if len(stack) < 1:
                    raise CalculatorError(f"函数 {name} 需要一个参数")
                arg = stack.pop()
                try:
                    result = FUNCTIONS[name](arg)
                except (ValueError, ZeroDivisionError, OverflowError) as exc:
                    raise CalculatorError(f"函数 {name} 计算失败: {exc}") from exc
                stack.append(result)

    if len(stack) != 1:
        raise CalculatorError("表达式无效：结果不唯一")
    return stack[0]


def calculate(expression: str) -> float:
    """Parse and evaluate a mathematical expression safely.

    Args:
        expression: A math expression such as ``"2 + 3 * sin(pi/2)"``.

    Returns:
        The numeric result as a float.

    Raises:
        CalculatorError: If the expression is invalid or evaluation fails.
    """
    tokens = tokenize(expression)
    rpn = to_rpn(tokens)
    return evaluate_rpn(rpn)


def format_result(value: float) -> str:
    """Format a float result into a clean string."""
    if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
        raise CalculatorError("计算结果无效（NaN 或 Infinity）")
    # Use 12 significant digits, strip trailing zeros.
    rounded = round(value, 12)
    if rounded == int(rounded):
        return str(int(rounded))
    return f"{rounded:.12g}"
