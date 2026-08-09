"""Scratch-style operators for generated competition programs."""


def _number(value):
    if value is None:
        return 0
    if isinstance(value, bool):
        return 1 if value else 0
    if isinstance(value, (int, float)):
        return value
    try:
        number = float(str(value).strip())
        return int(number) if number == int(number) else number
    except Exception:
        return 0


def _boolean(value):
    if isinstance(value, str):
        return value.strip().lower() not in ("", "0", "false", "none")
    return bool(value)


def _random_unit():
    # The target firmware's ``random`` module may initialize modem-backed
    # services.  ``urandom`` is the lightweight MicroPython source.
    try:
        import urandom
        return urandom.getrandbits(24) / float(1 << 24)
    except Exception:
        try:
            import random
            return random.random()
        except Exception:
            try:
                import time
                return (time.ticks_ms() % 1000000) / 1000000.0
            except Exception:
                return 0.5


def yunsuan(left, operator, right):
    """Run a numeric binary operator; zero divisors return None."""
    left = _number(left)
    right = _number(right)
    operator = str(operator).strip().lower()
    if operator in ("+", "add", "plus"):
        return left + right
    if operator in ("-", "subtract", "minus"):
        return left - right
    if operator in ("*", "multiply", "times"):
        return left * right
    if operator in ("/", "divide"):
        return None if right == 0 else left / right
    if operator in ("//", "floor_divide"):
        return None if right == 0 else left // right
    if operator in ("%", "mod", "modulo"):
        return None if right == 0 else left % right
    if operator in ("**", "power"):
        try:
            return left ** right
        except Exception:
            return None
    return None


def suijishu(start, end):
    """Return an inclusive integer or a floating-point value in the range."""
    start = _number(start)
    end = _number(end)
    low = min(start, end)
    high = max(start, end)
    if low == high:
        return low
    unit = _random_unit()
    if isinstance(start, int) and isinstance(end, int):
        return low + int(unit * (high - low + 1))
    return low + unit * (high - low)


def shuxue(operator, value):
    """Run a Scratch-compatible one-value math function."""
    import math

    value = _number(value)
    operator = str(operator).strip().lower()
    try:
        if operator == "round":
            return int(math.floor(value + 0.5))
        if operator == "abs":
            return abs(value)
        if operator == "floor":
            return math.floor(value)
        if operator in ("ceil", "ceiling"):
            return math.ceil(value)
        if operator == "sqrt":
            return math.sqrt(value)
        if operator in ("sin", "cos", "tan"):
            radians = value * math.pi / 180
            return getattr(math, operator)(radians)
        if operator in ("asin", "acos", "atan"):
            return getattr(math, operator)(value) * 180 / math.pi
        if operator == "ln":
            return math.log(value)
        if operator in ("log", "log10"):
            return math.log(value) / math.log(10)
        if operator in ("exp", "e^"):
            return math.exp(value)
        if operator in ("pow10", "10^"):
            return 10 ** value
    except Exception:
        return None
    return None


def bijiao(left, operator, right):
    """Compare numbers when possible, otherwise compare lowercase text."""
    operator = str(operator).strip().lower()
    try:
        left_number = float(str(left).strip())
        right_number = float(str(right).strip())
        left_value, right_value = left_number, right_number
    except Exception:
        left_value = str(left).lower()
        right_value = str(right).lower()
    if operator in ("==", "eq", "equals"):
        return left_value == right_value
    if operator in ("!=", "ne", "not_equals"):
        return left_value != right_value
    if operator in (">", "gt"):
        return left_value > right_value
    if operator in (">=", "gte"):
        return left_value >= right_value
    if operator in ("<", "lt"):
        return left_value < right_value
    if operator in ("<=", "lte"):
        return left_value <= right_value
    return False


def luoji(left, operator, right=None):
    """Run and/or/not and return a Boolean result."""
    operator = str(operator).strip().lower()
    if operator in ("not", "!"):
        return not _boolean(left)
    if operator in ("and", "&&"):
        return _boolean(left) and _boolean(right)
    if operator in ("or", "||"):
        return _boolean(left) or _boolean(right)
    return False


def wenbenchangdu(text):
    return len(str(text))


def wenbenzifu(text, index):
    """Return a character using Scratch's one-based index."""
    text = str(text)
    index = int(_number(index)) - 1
    return text[index] if 0 <= index < len(text) else ""


def wenbenbaohan(text, part):
    return str(part).lower() in str(text).lower()


def zhuanshuzi(value):
    return _number(value)


def zhuanwenzi(value):
    return str(value)
