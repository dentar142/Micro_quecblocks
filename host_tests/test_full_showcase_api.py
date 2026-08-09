import sys
import types
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "runtime" / "starter"))

import easy_api
from lib.kit.io_tests import PwmOutput


class FakeLcd:
    WIDTH = 160
    HEIGHT = 128
    BLACK = 0x0000
    WHITE = 0xFFFF
    RED = 0xF800
    GREEN = 0x07E0
    YELLOW = 0xFFE0
    BLUE = 0x001F

    def __init__(self):
        self.rotations = []
        self.strings = []
        self.rectangles = []
        self.images = []
        self.flushes = 0

    def set_rotation(self, rotation):
        self.rotations.append(rotation)

    def show_string(self, x, y, text, color, background, size):
        self.strings.append((x, y, text, color, background, size))

    def fill_rectangle(self, x, y, width, height, color):
        self.rectangles.append((x, y, width, height, color))

    def show_image(self, x, y, width, height, data):
        self.images.append((x, y, width, height, data))

    def flush(self):
        self.flushes += 1


class FakeDisplay:
    def __init__(self):
        self.lcd = FakeLcd()

    def _run_lcd(self, operation, retries=3, delay_ms=20):
        return operation()


class EasyApiFullShowcaseLcdTests(unittest.TestCase):
    def setUp(self):
        self.api = easy_api
        self.original_display = easy_api._display
        self.original_features = dict(easy_api.config.FEATURES)
        self.original_temp_active = easy_api._lcd_temp_active
        self.original_temp_until = easy_api._lcd_temp_until
        self.original_ticks_ms = easy_api.ticks_ms
        self.original_ticks_diff = easy_api.ticks_diff
        self.original_row_temp_until = dict(getattr(easy_api, "_lcd_row_temp_until", {}))
        easy_api.config.FEATURES["lcd"] = True
        easy_api.config.FEATURES["storage"] = True
        easy_api._display = FakeDisplay()
        easy_api._lcd_temp_active = False
        easy_api._lcd_temp_until = 0
        easy_api._lcd_row_temp_until = {}

    def tearDown(self):
        self.api._display = self.original_display
        self.api.config.FEATURES.clear()
        self.api.config.FEATURES.update(self.original_features)
        self.api._lcd_temp_active = self.original_temp_active
        self.api._lcd_temp_until = self.original_temp_until
        self.api.ticks_ms = self.original_ticks_ms
        self.api.ticks_diff = self.original_ticks_diff
        self.api._lcd_row_temp_until = self.original_row_temp_until

    def _require_api(self, name):
        function = getattr(self.api, name, None)
        self.assertTrue(callable(function), "easy_api.{} must exist and be callable".format(name))
        return function

    def test_showlcdcolor_draws_text_with_named_foreground_color(self):
        showlcdcolor = self._require_api("showlcdcolor")

        result = showlcdcolor("OK", 1, 2, "red")

        self.assertTrue(result)
        self.assertEqual(
            self.api._display.lcd.strings,
            [(16, 18, "OK", FakeLcd.RED, FakeLcd.BLACK, 16)],
        )
        self.assertEqual(self.api._display.lcd.flushes, 1)

    def test_clearlcdline_clears_only_the_requested_text_row(self):
        clearlcdline = self._require_api("clearlcdline")

        result = clearlcdline(3)

        self.assertTrue(result)
        self.assertEqual(
            self.api._display.lcd.rectangles,
            [(0, 54, FakeLcd.WIDTH, 18, FakeLcd.BLACK)],
        )
        self.assertEqual(self.api._display.lcd.flushes, 1)

    def test_lcdrect_draws_configurable_outline_thickness(self):
        lcdrect = self._require_api("lcdrect")

        self.assertTrue(lcdrect(10, 20, 30, 12, "green", False, 4))

        self.assertEqual(
            self.api._display.lcd.rectangles,
            [
                (10, 20, 30, 4, FakeLcd.GREEN),
                (10, 28, 30, 4, FakeLcd.GREEN),
                (10, 20, 4, 12, FakeLcd.GREEN),
                (36, 20, 4, 12, FakeLcd.GREEN),
            ],
        )

    def test_lcdline_keeps_text_call_and_supports_bounded_thickness(self):
        lcdline = self._require_api("lcdline")

        self.assertTrue(lcdline(2, "Legacy", 3))
        self.assertEqual(
            self.api._display.lcd.strings,
            [(24, 36, "Legacy", FakeLcd.WHITE, FakeLcd.BLACK, 16)],
        )

        self.api._display.lcd.rectangles.clear()
        self.assertTrue(lcdline(0, 0, 2, 0, "red", 3))
        self.assertTrue(self.api._display.lcd.rectangles)
        for x, y, width, height, color in self.api._display.lcd.rectangles:
            self.assertGreaterEqual(x, 0)
            self.assertGreaterEqual(y, 0)
            self.assertLessEqual(x + width, FakeLcd.WIDTH)
            self.assertLessEqual(y + height, FakeLcd.HEIGHT)
            self.assertEqual((width, height, color), (3, 3, FakeLcd.RED))

        self.api._display.lcd.rectangles.clear()
        self.assertTrue(lcdline(5, 5, 6, 5, "green"))
        self.assertTrue(all(rect[2:4] == (1, 1) for rect in self.api._display.lcd.rectangles))

    def test_lcdimage_uses_bounded_rgb565_frame(self):
        class FakeFile:
            def __enter__(self):
                return self
            def __exit__(self, *args):
                return False
            def read(self, size):
                return bytes(range(size))

        class FakeFileApi:
            @staticmethod
            def open(path, mode):
                return FakeFile()

        old_file = sys.modules.get("quectel")
        sys.modules["quectel"] = types.SimpleNamespace(File=FakeFileApi)
        try:
            self.assertTrue(self.api.lcdimage("SD:logo.rgb565", 2, 3, 4, 5))
        finally:
            if old_file is None:
                sys.modules.pop("quectel", None)
            else:
                sys.modules["quectel"] = old_file
        self.assertEqual(len(self.api._display.lcd.images), 1)
        x, y, width, height, data = self.api._display.lcd.images[0]
        self.assertEqual((x, y, width, height), (2, 3, 4, 5))
        self.assertEqual(len(data), 40)

    def test_updatelcdtemp_clears_expired_temporary_row(self):
        showlcdrowtemp = self._require_api("showlcdrowtemp")
        updatelcdtemp = self._require_api("updatelcdtemp")
        now = {"value": 1000}
        self.api.ticks_ms = lambda: now["value"]
        self.api.ticks_diff = lambda end, start: end - start

        self.assertTrue(showlcdrowtemp("Busy", 50, 2))
        self.api._display.lcd.rectangles.clear()
        self.api._display.lcd.strings.clear()
        self.api._display.lcd.flushes = 0
        now["value"] = 1060

        self.assertFalse(updatelcdtemp())
        self.assertEqual(
            self.api._display.lcd.rectangles,
            [(0, 36, FakeLcd.WIDTH, 18, FakeLcd.BLACK)],
        )
        self.assertEqual(self.api._display.lcd.strings, [])
        self.assertEqual(self.api._display.lcd.flushes, 1)

    def test_lcdrowtempactive_reserves_a_row_until_its_deadline(self):
        showlcdrowtemp = self._require_api("showlcdrowtemp")
        lcdrowtempactive = self._require_api("lcdrowtempactive")
        now = {"value": 1000}
        self.api.ticks_ms = lambda: now["value"]
        self.api.ticks_diff = lambda end, start: end - start

        self.assertTrue(showlcdrowtemp("Playing...", 50, 5))
        self.assertTrue(lcdrowtempactive(5))
        now["value"] = 1050
        self.assertFalse(lcdrowtempactive(5))

    def test_official_lcd_wrappers_use_pixel_coordinates_and_rgb565(self):
        self.assertEqual(self.api.lcdcolor565(255, 0, 0), FakeLcd.RED)
        self.assertTrue(self.api.lcdrotation(1))
        self.assertTrue(self.api.lcddrawpoint(2, 3, "red"))
        self.assertTrue(self.api.lcdshowstring(4, 5, "Hello", "green", "black", 12))
        self.assertTrue(self.api.lcddrawrect(10, 20, 20, 30, "blue"))
        self.assertTrue(self.api.lcdfillrect(30, 40, 12, 8, "yellow"))
        self.assertTrue(self.api.lcddrawline(0, 0, 5, 5, "white"))
        self.assertTrue(self.api.lcdcircle(80, 64, 12, "red", False))
        self.assertTrue(self.api.lcdflush())
        self.assertGreaterEqual(self.api._display.lcd.flushes, 7)


class FakeMachinePwm:
    instances = []

    def __init__(self, pin):
        self.pin = pin
        self.frequency = None
        self.duty_values = []
        self.deinitialized = False
        type(self).instances.append(self)

    def freq(self, value):
        self.frequency = value

    def duty_u16(self, value):
        self.duty_values.append(value)

    def deinit(self):
        self.deinitialized = True


class FakeMachinePin:
    OUT = object()
    IN = object()
    PULL_DOWN = object()
    writes = []
    levels = {}

    def __init__(self, pin, mode=None, pull=None, value=None):
        self.pin = pin
        self.mode = mode
        self.pull = pull
        if value is not None:
            type(self).writes.append((pin, value))

    def value(self, value=None):
        if value is None:
            return type(self).levels.get(self.pin, 0)
        type(self).writes.append((self.pin, value))
        return value


class FakeMachineModule:
    Pin = FakeMachinePin
    PWM = FakeMachinePwm


class PwmOutputDutyTests(unittest.TestCase):
    def setUp(self):
        FakeMachinePwm.instances = []

    def test_set_duty_updates_running_machine_pwm_duty(self):
        output = PwmOutput("D3", frequency=2000, duty_percent=25, machine_module=FakeMachineModule)
        output.start()
        self.assertTrue(callable(getattr(output, "set_duty", None)), "PwmOutput.set_duty must exist")

        result = output.set_duty(75)

        self.assertTrue(result)
        self.assertEqual(output.duty_percent, 75)
        self.assertEqual(FakeMachinePwm.instances[0].duty_values[-1], int(65535 * 75 / 100))


class EasyApiFullShowcaseGpioPwmTests(unittest.TestCase):
    def setUp(self):
        self.api = easy_api
        self.original_machine = sys.modules.get("machine")
        self.original_features = dict(easy_api.config.FEATURES)
        self.original_pwm = easy_api._pwm
        FakeMachinePin.writes = []
        FakeMachinePin.levels = {}
        fake_machine = types.ModuleType("machine")
        fake_machine.Pin = FakeMachinePin
        sys.modules["machine"] = fake_machine
        easy_api.config.FEATURES["gpio"] = True
        easy_api.config.FEATURES["pwm"] = True
        easy_api._pwm = None

    def tearDown(self):
        if self.original_machine is None:
            sys.modules.pop("machine", None)
        else:
            sys.modules["machine"] = self.original_machine
        self.api.config.FEATURES.clear()
        self.api.config.FEATURES.update(self.original_features)
        self.api._pwm = self.original_pwm

    def _require_api(self, name):
        function = getattr(self.api, name, None)
        self.assertTrue(callable(function), "easy_api.{} must exist and be callable".format(name))
        return function

    def test_highpins_returns_only_requested_gpio_pins_that_read_high(self):
        highpins = self._require_api("highpins")
        FakeMachinePin.levels = {"D2": 1, "D3": 0, "A5": 1}

        result = highpins(("D2", "D3", "A5"))

        self.assertEqual(result, "D2 A5")
        self.assertEqual(FakeMachinePin.writes, [])

    def test_setpwmduty_updates_active_pwm_output(self):
        class FakeActivePwm:
            def __init__(self):
                self.duty = 25

            def set_duty(self, duty):
                self.duty = duty
                return True

        setpwmduty = self._require_api("setpwmduty")
        self.api._pwm = FakeActivePwm()

        self.assertTrue(setpwmduty(60))
        self.assertEqual(self.api._pwm.duty, 60)

    def test_readpwmduty_returns_active_pwm_duty(self):
        class FakeActivePwm:
            duty_percent = 42

        readpwmduty = self._require_api("readpwmduty")
        self.api._pwm = FakeActivePwm()

        self.assertEqual(readpwmduty(), 42)


class EasyApiAudioOverwriteTests(unittest.TestCase):
    def setUp(self):
        self.api = easy_api
        self.original_audio = easy_api._audio
        self.original_record_file = easy_api._audio_current_record_file
        self.original_quectel = sys.modules.get("quectel")
        self.events = []
        events = self.events

        class FakeFile:
            @staticmethod
            def remove(path):
                events.append(("remove", path))

        fake_quectel = types.ModuleType("quectel")
        fake_quectel.File = FakeFile
        sys.modules["quectel"] = fake_quectel

        class FakeAudio:
            @staticmethod
            def record_start(path):
                events.append(("record_start", path))

        easy_api._audio = FakeAudio()

    def tearDown(self):
        self.api._audio = self.original_audio
        self.api._audio_current_record_file = self.original_record_file
        if self.original_quectel is None:
            sys.modules.pop("quectel", None)
        else:
            sys.modules["quectel"] = self.original_quectel

    def test_recordstart_removes_same_name_before_recording(self):
        self.assertTrue(self.api.recordstart("SD:competition_test.wav"))
        self.assertEqual(
            self.events,
            [("remove", "SD:competition_test.wav"), ("record_start", "SD:competition_test.wav")],
        )


if __name__ == "__main__":
    unittest.main()
