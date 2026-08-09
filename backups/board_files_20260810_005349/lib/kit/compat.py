"""MicroPython/CPython 的最小兼容层。"""

try:
    import utime as _time
except ImportError:
    import time as _time


def ticks_ms():
    fn = getattr(_time, "ticks_ms", None)
    if fn:
        return fn()
    return int(_time.monotonic() * 1000)


def ticks_us():
    fn = getattr(_time, "ticks_us", None)
    if fn:
        return fn()
    return int(_time.monotonic() * 1000000)


def ticks_diff(new, old):
    fn = getattr(_time, "ticks_diff", None)
    if fn:
        return fn(new, old)
    return new - old


def sleep_ms(value):
    fn = getattr(_time, "sleep_ms", None)
    if fn:
        fn(value)
    else:
        _time.sleep(value / 1000.0)


def import_optional(name):
    try:
        return __import__(name)
    except ImportError:
        return None

