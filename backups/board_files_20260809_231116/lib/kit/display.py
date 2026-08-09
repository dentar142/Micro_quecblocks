"""ST7735 LCD 的精简显示适配器。"""

import gc

from .compat import sleep_ms


class CompetitionDisplay:
    def __init__(self, spi_id=1, baudrate=10000000, dc_pin="F12", cs_pin="D14",
                 machine_module=None):
        if machine_module is None:
            import machine as machine_module
        from st7735 import LCD
        spi = machine_module.SPI(spi_id, baudrate=baudrate, polarity=0, phase=0)
        self.lcd = LCD(spi, dc_pin=dc_pin, cs_pin=cs_pin)
        self.lcd.set_rotation(3)
        self.clear()

    def _run_lcd(self, operation, retries=3, delay_ms=20):
        # The ST7735 driver allocates a 5 KiB transfer buffer. BLE, audio and
        # sensor modules can fragment the small MicroPython heap before a
        # refresh, so compact it immediately before that allocation.
        gc.collect()
        last_error = None
        for _ in range(retries):
            try:
                return operation()
            except OSError as exc:
                last_error = exc
                # EBUSY(16) means the LCD/SPI bus is still finishing the
                # previous operation. Retry so high-level examples keep going.
                if not getattr(exc, "args", ()) or exc.args[0] != 16:
                    raise
                sleep_ms(delay_ms)
        if last_error is not None:
            raise last_error
        return None

    def clear(self):
        def operation():
            # The frozen driver uses a 5 KiB transfer allocation for
            # fill_screen(). Clear in short strips so BLE/audio/sensor
            # applications can refresh the LCD under peak memory load.
            strip_height = 8
            for y in range(0, self.lcd.HEIGHT, strip_height):
                height = min(strip_height, self.lcd.HEIGHT - y)
                self.lcd.fill_rectangle(
                    0, y, self.lcd.WIDTH, height, self.lcd.BLACK
                )
            self.lcd.flush()
            return True
        return self._run_lcd(operation)

    def text(self, row, value, color=None):
        if color is None:
            color = self.lcd.WHITE
        y = row * 18
        def operation():
            self.lcd.show_string(0, y, str(value)[:20], color, self.lcd.BLACK, 16)
            self.lcd.flush()
            return True
        return self._run_lcd(operation)

    def show_test(self, name, status, detail=""):
        color = self.lcd.GREEN if status == "PASS" else self.lcd.RED
        if status == "SKIP":
            color = self.lcd.YELLOW
        self.clear()
        self.text(0, name, self.lcd.CYAN)
        self.text(1, status, color)
        if detail:
            self.text(2, detail)

    def show_summary(self, counts):
        self.clear()
        self.text(0, "SUMMARY", self.lcd.CYAN)
        self.text(1, "PASS {}".format(counts["PASS"]), self.lcd.GREEN)
        self.text(2, "FAIL {}".format(counts["FAIL"]), self.lcd.RED)
        self.text(3, "SKIP {}".format(counts["SKIP"]), self.lcd.YELLOW)
