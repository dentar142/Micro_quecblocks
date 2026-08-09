"""数字按键和模拟五向键的统一事件接口。"""

from .compat import ticks_diff

PRESS = "press"
RELEASE = "release"
SHORT = "short"
LONG = "long"
REPEAT = "repeat"


class ButtonState:
    """纯状态机，便于在 PC 上单元测试。"""

    def __init__(self, debounce_ms=40, long_ms=800, repeat_delay_ms=600,
                 repeat_ms=150):
        self.debounce_ms = debounce_ms
        self.long_ms = long_ms
        self.repeat_delay_ms = repeat_delay_ms
        self.repeat_ms = repeat_ms
        self.raw = False
        self.stable = False
        self.raw_changed_at = 0
        self.pressed_at = 0
        self.repeated_at = 0
        self.long_sent = False

    def update(self, pressed, now_ms):
        events = []
        pressed = bool(pressed)
        if pressed != self.raw:
            self.raw = pressed
            self.raw_changed_at = now_ms

        if self.raw != self.stable and ticks_diff(now_ms, self.raw_changed_at) >= self.debounce_ms:
            self.stable = self.raw
            if self.stable:
                self.pressed_at = now_ms
                self.repeated_at = now_ms
                self.long_sent = False
                events.append(PRESS)
            else:
                events.append(RELEASE)
                if not self.long_sent:
                    events.append(SHORT)

        # During release debounce stable is still True, but the physical input
        # is already released. Do not turn that release window into LONG/REPEAT.
        if self.stable and self.raw:
            held = ticks_diff(now_ms, self.pressed_at)
            if not self.long_sent and held >= self.long_ms:
                self.long_sent = True
                self.repeated_at = now_ms
                events.append(LONG)
            if self.long_sent and held >= self.repeat_delay_ms and ticks_diff(now_ms, self.repeated_at) >= self.repeat_ms:
                self.repeated_at = now_ms
                events.append(REPEAT)
        return events


class ButtonManager:
    def __init__(self, debounce_ms=40, long_ms=800, repeat_delay_ms=600,
                 repeat_ms=150):
        self.settings = (debounce_ms, long_ms, repeat_delay_ms, repeat_ms)
        self.sources = {}
        self.states = {}
        self.callbacks = {}
        self.poll_hooks = []

    def add(self, name, read_pressed):
        self.sources[name] = read_pressed
        self.states[name] = ButtonState(*self.settings)

    def on(self, name, event, callback):
        self.callbacks.setdefault((name, event), []).append(callback)

    def add_poll_hook(self, hook):
        """Run a shared input sampler once before each poll."""
        self.poll_hooks.append(hook)

    def poll(self, now_ms):
        emitted = []
        for hook in self.poll_hooks:
            prepare = getattr(hook, "prepare_poll", None)
            if prepare:
                prepare(now_ms)
        try:
            for name, source in self.sources.items():
                for event in self.states[name].update(source(), now_ms):
                    emitted.append((name, event))
                    for callback in self.callbacks.get((name, event), ()):
                        callback(name, event)
        finally:
            for hook in self.poll_hooks:
                finish = getattr(hook, "finish_poll", None)
                if finish:
                    finish()
        return emitted


class AnalogNavigation:
    def __init__(self, adc, thresholds, release_min=60000):
        self.adc = adc
        self.thresholds = thresholds
        self.release_min = release_min
        self._cached_key = None
        self._cache_valid = False

    def read_raw(self):
        return self.adc.read_u16()

    def read_key(self):
        value = self.read_raw()
        return self.key_for_value(value)

    def key_for_value(self, value):
        if value >= self.release_min:
            return None
        for name, bounds in self.thresholds.items():
            if bounds[0] <= value <= bounds[1]:
                return name
        return None

    def prepare_poll(self, _now_ms=None):
        """Sample the ladder once; all key sources share this result."""
        self._cached_key = self.key_for_value(self.read_raw())
        self._cache_valid = True

    def finish_poll(self):
        self._cache_valid = False

    def current_key(self):
        if self._cache_valid:
            return self._cached_key
        return self.read_key()

    def source_for(self, name):
        return lambda: self.current_key() == name
