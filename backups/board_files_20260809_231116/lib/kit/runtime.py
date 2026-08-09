"""统一启动、初始化和状态采集。"""

from .compat import ticks_ms, sleep_ms
from .report import Reporter


class CompetitionRuntime:
    def __init__(self, config, reporter=None):
        self.config = config
        self.reporter = reporter or Reporter()
        self.display = None
        self.leds = None
        self.buttons = None
        self.sensors = None
        self.errors = {}

    def _feature(self, name):
        return bool(self.config.FEATURES.get(name))

    def init_display(self):
        if not self._feature("lcd"):
            return None
        try:
            from .display import CompetitionDisplay
            self.display = CompetitionDisplay(
                self.config.SPI_ID,
                self.config.SPI_BAUDRATE,
                self.config.LCD_DC_PIN,
                self.config.LCD_CS_PIN,
            )
            self.reporter.display = self.display
        except Exception as exc:
            self.errors["lcd"] = str(exc)
        return self.display

    def init_leds(self):
        if not self._feature("leds"):
            return None
        try:
            from .leds import LedBank
            self.leds = LedBank(self.config.LED_PINS)
            if self.leds.errors:
                self.errors["leds"] = self.leds.errors
        except Exception as exc:
            self.errors["leds"] = str(exc)
        return self.leds

    def init_buttons(self):
        if not self._feature("buttons"):
            return None
        try:
            import machine
            from .buttons import ButtonManager, AnalogNavigation
            self.buttons = ButtonManager(
                self.config.BUTTON_DEBOUNCE_MS,
                self.config.BUTTON_LONG_MS,
                self.config.BUTTON_REPEAT_DELAY_MS,
                self.config.BUTTON_REPEAT_MS,
            )
            user = machine.Pin(self.config.USER_BUTTON_PIN, machine.Pin.IN, machine.Pin.PULL_DOWN)
            self.buttons.add("user", lambda: user.value() == 1)
            nav_adc = machine.ADC(machine.Pin(self.config.NAV_ADC_PIN))
            nav = AnalogNavigation(nav_adc, self.config.NAV_THRESHOLDS, self.config.NAV_RELEASE_MIN)
            for key in ("up", "down", "left", "right", "center"):
                self.buttons.add(key, nav.source_for(key))
        except Exception as exc:
            self.errors["buttons"] = str(exc)
        return self.buttons

    def init_sensors(self):
        try:
            from .sensors import SensorSuite
            self.sensors = SensorSuite(self.config)
            if self.sensors.errors:
                self.errors["sensors"] = self.sensors.errors
        except Exception as exc:
            self.errors["sensors"] = str(exc)
        return self.sensors

    def init_all(self):
        self.init_display()
        self.init_leds()
        self.init_buttons()
        self.init_sensors()
        return self

    def snapshot(self):
        data = {"time_ms": ticks_ms(), "errors": self.errors}
        if self.sensors:
            data.update(self.sensors.snapshot())
        return data

    def run_snapshot_loop(self, seconds=10):
        stop_at = ticks_ms() + seconds * 1000
        while ticks_ms() < stop_at:
            if self.buttons:
                for name, event in self.buttons.poll(ticks_ms()):
                    print("[BUTTON][{}][{}]".format(name, event))
            print("[SNAPSHOT]", self.snapshot())
            sleep_ms(self.config.SENSOR_INTERVAL_MS)

