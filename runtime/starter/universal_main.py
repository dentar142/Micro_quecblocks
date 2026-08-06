"""Universal offline competition entry point.

Use this file when the exact assessment question is unknown.  It exposes one
small command interface over the existing kit modules:

    from universal_main import UniversalKit
    app = UniversalKit()
    app.help()
    app.run("adc")
    app.run_all()

The code intentionally skips unconfigured or disabled hardware instead of
guessing pins.  Set feature flags and loopback pins in config.py first.
"""

import config

from lib.kit.audio_storage import AudioProbe, StorageProbe
from lib.kit.compat import sleep_ms, ticks_diff, ticks_ms
from lib.kit.io_tests import Buzzer, GpioLoopback, PulseMeter, PwmOutput, SpiLoopback, TimerProbe
from lib.kit.preflight import check_modules
from lib.kit.report import PASS
from lib.kit.runtime import CompetitionRuntime
from lib.kit.serial_tests import Rs485Port, UartPort


COMMANDS = (
    ("preflight", "firmware modules"),
    ("led", "cycle board LEDs"),
    ("button_led", "press buttons to toggle LED"),
    ("adc", "read light ADC"),
    ("i2c", "scan I2C bus"),
    ("sensors", "read AHT20/LIS2DH12"),
    ("gpio", "Dupont GPIO loopback"),
    ("timer", "periodic timer"),
    ("pwm", "PWM output + measurement"),
    ("buzzer", "buzzer beep"),
    ("spi_lcd", "SPI LCD display"),
    ("spi_loopback", "SPI MOSI-MISO loopback"),
    ("uart", "UART TX-RX loopback"),
    ("rs232", "RS232 transceiver loopback"),
    ("rs485", "RS485 loopback"),
    ("storage", "storage card read/write"),
    ("audio", "mic record + speaker/TTS"),
    ("hmi", "LCD + 5-way key menu"),
)


class UniversalKit:
    """One object with one public command API for expected contest tasks."""

    def __init__(self, cfg=config):
        self.config = cfg
        self.runtime = CompetitionRuntime(cfg).init_all()
        self.reporter = self.runtime.reporter

    def feature(self, name):
        return bool(self.config.FEATURES.get(name))

    def help(self):
        print("Commands:")
        for name, detail in COMMANDS:
            print("  {:12s} - {}".format(name, detail))
        print("  {:12s} - run all commands above".format("all"))
        print("  {:12s} - show this help".format("help"))

    def run(self, name):
        name = (name or "").strip().lower()
        if name == "help":
            self.help()
            return PASS
        if name == "all":
            return self.run_all()
        method = getattr(self, "cmd_" + name, None)
        if not method:
            self.reporter.skipped("COMMAND", "unknown command: {}".format(name))
            self.help()
            return None
        try:
            return method()
        except Exception as exc:
            return self.reporter.failed(name.upper(), exc)

    def run_all(self):
        for name, _detail in COMMANDS:
            self.run(name)
        return self.reporter.summary()

    def interactive(self):
        self.help()
        while True:
            try:
                cmd = input("kit> ").strip().lower()
            except (EOFError, KeyboardInterrupt):
                print("")
                return self.reporter.summary()
            if cmd in ("q", "quit", "exit"):
                return self.reporter.summary()
            if cmd:
                self.run(cmd)

    def cmd_preflight(self):
        result = check_modules(self.config.REQUIRED_FROZEN_MODULES)
        missing = [name for name, ok in result.items() if ok is not True]
        if missing:
            return self.reporter.failed("PREFLIGHT", "missing=" + ",".join(missing))
        return self.reporter.passed("PREFLIGHT", "all required modules import")

    def cmd_led(self):
        if not self.feature("leds"):
            return self.reporter.skipped("LED", "disabled")
        if not self.runtime.leds or not self.runtime.leds.names():
            return self.reporter.failed("LED", self.runtime.errors.get("leds", "not initialized"))
        self.runtime.leds.cycle(200)
        return self.reporter.passed("LED", ",".join(self.runtime.leds.names()))

    def cmd_button_led(self, timeout_ms=15000):
        if not self.runtime.buttons:
            return self.reporter.skipped("BUTTON_LED", "buttons not initialized")
        if not self.runtime.leds or not self.runtime.leds.names():
            return self.reporter.skipped("BUTTON_LED", "LEDs not initialized")
        led_name = self.runtime.leds.names()[0]
        state = False
        seen = []
        print("[PROMPT] Press user/up/down/left/right/center within {} ms".format(timeout_ms))
        start = ticks_ms()
        while ticks_diff(ticks_ms(), start) < timeout_ms:
            for name, event in self.runtime.buttons.poll(ticks_ms()):
                print("[BUTTON][{}][{}]".format(name, event))
                if event == "short":
                    state = not state
                    self.runtime.leds.set(led_name, state)
                    if name not in seen:
                        seen.append(name)
            if len(seen) >= 2:
                break
            sleep_ms(20)
        self.runtime.leds.off(led_name)
        if seen:
            return self.reporter.passed("BUTTON_LED", "seen=" + ",".join(seen))
        return self.reporter.failed("BUTTON_LED", "no short press detected")

    def cmd_adc(self):
        if not self.feature("adc"):
            return self.reporter.skipped("ADC", "disabled")
        light = self.runtime.snapshot().get("sensors", {}).get("light")
        if not light:
            return self.reporter.failed("ADC", self.runtime.errors.get("sensors", "light missing"))
        return self.reporter.passed(
            "ADC",
            "raw={} voltage={:.2f} percent={:.1f}".format(
                light["raw_u16"], light["voltage"], light["percent"]
            ),
        )

    def cmd_i2c(self):
        if not self.feature("i2c"):
            return self.reporter.skipped("I2C", "disabled")
        data = self.runtime.snapshot().get("sensors", {}).get("i2c")
        if not data:
            return self.reporter.failed("I2C", self.runtime.errors.get("sensors", "scan missing"))
        return self.reporter.passed("I2C", ",".join(hex(x) for x in data.get("addresses", [])))

    def cmd_sensors(self):
        if not self.feature("i2c"):
            return self.reporter.skipped("SENSORS", "i2c disabled")
        sensors = self.runtime.snapshot().get("sensors", {})
        ok = []
        for name in ("climate", "motion"):
            if name in sensors:
                ok.append("{}={}".format(name, sensors[name]))
        if ok:
            return self.reporter.passed("SENSORS", "; ".join(ok))
        return self.reporter.failed("SENSORS", self.runtime.errors.get("sensors", "no sensor data"))

    def cmd_gpio(self):
        if not self.feature("gpio"):
            return self.reporter.skipped("GPIO", "disabled")
        if not self.config.GPIO_LOOP_OUT_PIN or not self.config.GPIO_LOOP_IN_PIN:
            return self.reporter.skipped("GPIO", "set GPIO_LOOP_OUT_PIN/GPIO_LOOP_IN_PIN")
        ok, detail = GpioLoopback(self.config.GPIO_LOOP_OUT_PIN, self.config.GPIO_LOOP_IN_PIN).run()
        return self.reporter.passed("GPIO", detail) if ok else self.reporter.failed("GPIO", detail)

    def cmd_timer(self):
        if not self.feature("timer"):
            return self.reporter.skipped("TIMER", "disabled")
        ok, detail = TimerProbe().run()
        return self.reporter.passed("TIMER", detail) if ok else self.reporter.failed("TIMER", detail)

    def cmd_pwm(self):
        if not self.feature("pwm"):
            return self.reporter.skipped("PWM", "disabled")
        if not self.config.PWM_OUTPUT_PIN or not self.config.PWM_MEASURE_PIN:
            return self.reporter.skipped("PWM", "set PWM_OUTPUT_PIN/PWM_MEASURE_PIN")
        pwm = None
        meter = None
        try:
            pwm = PwmOutput(
                self.config.PWM_OUTPUT_PIN,
                1000,
                50,
                timer_id=self.config.PWM_TIMER_ID,
                timer_channel=self.config.PWM_TIMER_CHANNEL,
            )
            mode = pwm.start()
            meter = PulseMeter(self.config.PWM_MEASURE_PIN)
            ok, detail = meter.sample(500)
            detail = "mode={} {}".format(mode, detail)
            return self.reporter.passed("PWM", detail) if ok else self.reporter.failed("PWM", detail)
        finally:
            if meter:
                meter.close()
            if pwm:
                pwm.stop()

    def cmd_buzzer(self):
        if not self.feature("buzzer"):
            return self.reporter.skipped("BUZZER", "disabled")
        if not self.config.BUZZER_PIN:
            return self.reporter.skipped("BUZZER", "set BUZZER_PIN")
        mode = Buzzer(self.config.BUZZER_PIN, self.config.BUZZER_ACTIVE).beep(300)
        return self.reporter.passed("BUZZER", mode)

    def cmd_spi_lcd(self):
        if not self.feature("lcd"):
            return self.reporter.skipped("SPI_LCD", "lcd disabled")
        if not self.runtime.display:
            return self.reporter.failed("SPI_LCD", self.runtime.errors.get("lcd", "not initialized"))
        self.runtime.display.show_test("SPI_LCD", "PASS", "display ready")
        return self.reporter.passed("SPI_LCD", "display ready")

    def cmd_spi_loopback(self):
        if not self.feature("spi_loopback"):
            return self.reporter.skipped("SPI_LOOPBACK", "disabled; wire MOSI to MISO")
        ok, detail = SpiLoopback(self.config.SPI_ID, self.config.SPI_LOOPBACK_BAUDRATE).run()
        return self.reporter.passed("SPI_LOOPBACK", detail) if ok else self.reporter.failed("SPI_LOOPBACK", detail)

    def cmd_uart(self):
        if not self.feature("uart"):
            return self.reporter.skipped("UART", "disabled")
        ok, detail = UartPort(self.config.UART_ID, self.config.UART_BAUDRATE, self.config.UART_TIMEOUT_MS).loopback()
        return self.reporter.passed("UART", detail) if ok else self.reporter.failed("UART", detail)

    def cmd_rs232(self):
        if not self.feature("rs232") or not self.config.RS232_TRANSCEIVER_CONFIRMED:
            return self.reporter.skipped("RS232", "enable only with real RS232 transceiver")
        ok, detail = UartPort(self.config.UART_ID, self.config.UART_BAUDRATE, self.config.UART_TIMEOUT_MS).loopback(b"RS232")
        return self.reporter.passed("RS232", detail) if ok else self.reporter.failed("RS232", detail)

    def cmd_rs485(self):
        if not self.feature("rs485") or not self.config.RS485_DIRECTION_PIN:
            return self.reporter.skipped("RS485", "set RS485_DIRECTION_PIN")
        ok, detail = Rs485Port(
            self.config.UART_ID,
            self.config.UART_BAUDRATE,
            self.config.UART_TIMEOUT_MS,
            self.config.RS485_DIRECTION_PIN,
        ).loopback()
        return self.reporter.passed("RS485", detail) if ok else self.reporter.failed("RS485", detail)

    def cmd_storage(self):
        if not self.feature("storage"):
            return self.reporter.skipped("STORAGE", "disabled")
        ok, detail = StorageProbe(self.config.STORAGE_TEST_DIR).run()
        return self.reporter.passed("STORAGE", detail) if ok else self.reporter.failed("STORAGE", detail)

    def cmd_audio(self):
        if not self.feature("audio"):
            return self.reporter.skipped("AUDIO", "disabled")
        probe = AudioProbe(self.config.AUDIO_RECORD_FILE)
        ok, detail = probe.record_and_play(1500)
        if not ok:
            return self.reporter.failed("AUDIO", detail)
        ok, detail2 = AudioProbe(self.config.AUDIO_RECORD_FILE).tts("Quectel test")
        if not ok:
            return self.reporter.failed("AUDIO", detail2)
        return self.reporter.passed("AUDIO", detail + "; " + detail2)

    def cmd_hmi(self, timeout_ms=30000):
        if not self.runtime.display or not self.runtime.buttons:
            return self.reporter.skipped("HMI", "display/buttons not initialized")
        from lib.kit.menu import Menu

        menu_items = []
        for name, _detail in COMMANDS[:8]:
            menu_items.append((name, lambda selected=name: self.run(selected)))
        menu = Menu(self.runtime.display, menu_items)
        menu.bind(self.runtime.buttons)
        print("[PROMPT] Use up/down/center on LCD shield; timeout={} ms".format(timeout_ms))
        start = ticks_ms()
        while ticks_diff(ticks_ms(), start) < timeout_ms:
            self.runtime.buttons.poll(ticks_ms())
            sleep_ms(20)
        return self.reporter.passed("HMI", "menu loop ended")


def main():
    app = UniversalKit()
    app.interactive()


if __name__ == "__main__":
    main()
