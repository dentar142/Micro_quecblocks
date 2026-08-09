"""NUCLEO-F413ZH 三个用户 LED 的安全封装。"""


class LedBank:
    def __init__(self, pins, machine_module=None):
        if machine_module is None:
            import machine as machine_module
        self.machine = machine_module
        self.leds = {}
        self.errors = {}
        for name, pin_name in pins.items():
            try:
                self.leds[name] = self.machine.Pin(pin_name, self.machine.Pin.OUT, value=0)
            except Exception as exc:
                self.errors[name] = str(exc)

    def names(self):
        return tuple(self.leds.keys())

    def set(self, name, enabled):
        self.leds[name].value(1 if enabled else 0)

    def on(self, name):
        self.set(name, True)

    def off(self, name):
        self.set(name, False)

    def all_off(self):
        for name in self.leds:
            self.off(name)

    def cycle(self, delay_ms=250):
        from .compat import sleep_ms
        for name in self.leds:
            self.all_off()
            self.on(name)
            sleep_ms(delay_ms)
        self.all_off()

