import sys
import types
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "runtime" / "starter"))

from lib.kit.buttons import (
    AnalogNavigation,
    ButtonManager,
    ButtonState,
    PRESS,
    RELEASE,
    SHORT,
    LONG,
    REPEAT,
)
from lib.kit.report import Reporter, PASS, FAIL, SKIP
from lib.kit.ble_modes import EasyBLE
from lib.kit.display import CompetitionDisplay


class FakeAdc:
    def __init__(self, value):
        self.value = value
        self.reads = 0

    def read_u16(self):
        self.reads += 1
        return self.value


class ButtonStateTests(unittest.TestCase):
    def test_short_press(self):
        state = ButtonState(debounce_ms=40, long_ms=800, repeat_delay_ms=600, repeat_ms=150)
        self.assertEqual(state.update(True, 0), [])
        self.assertEqual(state.update(True, 50), [PRESS])
        self.assertEqual(state.update(False, 100), [])
        self.assertEqual(state.update(False, 150), [RELEASE, SHORT])

    def test_long_and_repeat(self):
        state = ButtonState(debounce_ms=10, long_ms=100, repeat_delay_ms=120, repeat_ms=50)
        state.update(True, 0)
        self.assertEqual(state.update(True, 10), [PRESS])
        self.assertEqual(state.update(True, 120), [LONG])
        self.assertIn(REPEAT, state.update(True, 180))
        self.assertEqual(state.update(False, 200), [])
        self.assertEqual(state.update(False, 220), [RELEASE])

    def test_release_debounce_does_not_emit_long(self):
        state = ButtonState(debounce_ms=40, long_ms=100, repeat_delay_ms=150, repeat_ms=50)
        state.update(True, 0)
        self.assertEqual(state.update(True, 40), [PRESS])
        self.assertEqual(state.update(False, 120), [])
        self.assertEqual(state.update(False, 150), [])
        self.assertEqual(state.update(False, 160), [RELEASE, SHORT])


class NavigationTests(unittest.TestCase):
    def test_thresholds(self):
        thresholds = {
            "left": (28000, 40000),
            "down": (47000, 59000),
            "center": (17000, 26000),
            "right": (0, 5000),
            "up": (7000, 16000),
        }
        nav = AnalogNavigation(FakeAdc(1000), thresholds, 60000)
        self.assertEqual(nav.read_key(), "right")
        for value, expected in ((10000, "up"), (20000, "center"),
                                (30000, "left"), (50000, "down")):
            nav.adc.value = value
            self.assertEqual(nav.read_key(), expected)
        nav.adc.value = 65000
        self.assertIsNone(nav.read_key())

    def test_navigation_samples_once_per_poll(self):
        adc = FakeAdc(8000)
        nav = AnalogNavigation(
            adc,
            {"down": (7000, 16000), "center": (17000, 26000)},
            60000,
        )
        manager = ButtonManager(debounce_ms=0)
        manager.add_poll_hook(nav)
        manager.add("down", nav.source_for("down"))
        manager.add("center", nav.source_for("center"))

        events = manager.poll(0)

        self.assertEqual(adc.reads, 1)
        self.assertEqual(events, [("down", PRESS)])


class LedPwmMappingTests(unittest.TestCase):
    def test_board_pwm_mapping_matches_verified_timer_channels(self):
        import config

        self.assertEqual(config.LED_PWM_CHANNELS, {
            "green": ("B0", 3, 3),
            "blue": ("B7", 4, 2),
            "red": ("B14", 12, 1),
        })

    def test_all_led_channels_create_independent_verified_pyb_outputs(self):
        import easy_api
        import lib.kit.io_tests as io_tests

        class FakeLeds:
            def set(self, _name, _value):
                pass

        class FakeOutput:
            instances = []

            def __init__(self, pin, frequency, duty, **options):
                self.pin = pin
                self.frequency = frequency
                self.duty = duty
                self.options = options
                self.stopped = False
                type(self).instances.append(self)

            def start(self):
                return "pyb.Timer.PWM"

            def set_duty(self, duty):
                self.duty = duty
                return True

            def stop(self):
                self.stopped = True

        original_output = io_tests.PwmOutput
        original_leds = easy_api._leds
        original_pwm = easy_api._led_pwm
        original_breathe = easy_api._led_breathe_state
        original_enabled = easy_api.config.FEATURES["leds"]
        try:
            io_tests.PwmOutput = FakeOutput
            easy_api.config.FEATURES["leds"] = True
            easy_api._leds = FakeLeds()
            easy_api._led_pwm = {}
            easy_api._led_breathe_state = {}

            for channel in ("green", "blue", "red"):
                self.assertTrue(easy_api.ledbrightness(channel, 40, 1000))

            self.assertEqual(set(easy_api._led_pwm), {"green", "blue", "red"})
            self.assertEqual(
                [(item.pin, item.options["timer_id"], item.options["timer_channel"])
                 for item in FakeOutput.instances],
                [("B0", 3, 3), ("B7", 4, 2), ("B14", 12, 1)],
            )
            self.assertTrue(all(item.options["prefer_pyb"] for item in FakeOutput.instances))

            easy_api.led2(0)
            self.assertEqual(set(easy_api._led_pwm), {"green", "red"})
            self.assertTrue(FakeOutput.instances[1].stopped)
            self.assertFalse(FakeOutput.instances[0].stopped)
            self.assertFalse(FakeOutput.instances[2].stopped)
        finally:
            io_tests.PwmOutput = original_output
            easy_api._leds = original_leds
            easy_api._led_pwm = original_pwm
            easy_api._led_breathe_state = original_breathe
            easy_api.config.FEATURES["leds"] = original_enabled


class ReporterTests(unittest.TestCase):
    def test_counts(self):
        lines = []
        reporter = Reporter(printer=lines.append)
        reporter.passed("A")
        reporter.failed("B", "bad")
        reporter.skipped("C")
        self.assertEqual(reporter.counts(), {PASS: 1, FAIL: 1, SKIP: 1})
        reporter.summary()
        self.assertEqual(lines[-1], "[SUMMARY] PASS=1 FAIL=1 SKIP=1")


class DisplayRetryTests(unittest.TestCase):
    def test_heap_is_compacted_before_lcd_transfer(self):
        display = CompetitionDisplay.__new__(CompetitionDisplay)
        with patch("lib.kit.display.gc.collect") as collect:
            self.assertTrue(display._run_lcd(lambda: True, delay_ms=0))
        collect.assert_called_once_with()

    def test_clear_uses_small_strips_covering_the_screen(self):
        class FakeLcd:
            WIDTH = 160
            HEIGHT = 128
            BLACK = 0

            def __init__(self):
                self.rectangles = []
                self.flushes = 0

            def fill_rectangle(self, x, y, width, height, color):
                self.rectangles.append((x, y, width, height, color))

            def flush(self):
                self.flushes += 1

        display = CompetitionDisplay.__new__(CompetitionDisplay)
        display.lcd = FakeLcd()
        display.clear()

        self.assertEqual(len(display.lcd.rectangles), 16)
        self.assertEqual(display.lcd.rectangles[0], (0, 0, 160, 8, 0))
        self.assertEqual(display.lcd.rectangles[-1], (0, 120, 160, 8, 0))
        self.assertEqual(display.lcd.flushes, 1)


class BleReceiveQueueTests(unittest.TestCase):
    def setUp(self):
        self.original_quectel = sys.modules.get("quectel")
        fake_quectel = types.ModuleType("quectel")

        class FakeBLE:
            EVT_CONNECTED = 1
            EVT_DISCONNECTED = 2
            EVT_VAL_DATA = 3
            EVT_DESCDATA = 4

        fake_quectel.BLE = FakeBLE
        sys.modules["quectel"] = fake_quectel
        config = types.SimpleNamespace(
            BLE_NAME="test",
            BLE_CLIENT_TARGET_NAME="test",
            BLE_CCCD_UUID=0x2902,
            BLE_CHAR_UUID=0xFFF1,
            BLE_RX_QUEUE_MAX=2,
        )
        self.backend = EasyBLE(config, lambda _ms: None, lambda: 0, lambda a, b: a - b, str)

    def tearDown(self):
        if self.original_quectel is None:
            sys.modules.pop("quectel", None)
        else:
            sys.modules["quectel"] = self.original_quectel

    def test_server_send_skips_modem_write_until_a_client_is_connected(self):
        class FakeServer:
            def set_character_value(self, *args):
                raise AssertionError("must not write before a BLE client connects")

        self.backend.obj = FakeServer()
        self.backend.active_mode = "server"
        self.backend.mode = "server"
        self.backend.connected = False

        self.assertFalse(self.backend.send("sensor data"))
        self.assertEqual(self.backend.error, "server not connected")

    def test_server_value_is_consumed_once(self):
        self.backend.server_cb({"event": 3, "value": "hello"})

        self.assertEqual(self.backend.read_received(), "hello")
        self.assertIsNone(self.backend.read_received())

    def test_cccd_write_is_not_application_data(self):
        self.backend.server_cb({"event": 4, "uuid": 0xFFF1, "desc_uuid": 0x2902, "value": "0100"})

        self.assertTrue(self.backend.notify_enabled)
        self.assertIsNone(self.backend.read_received())

    def test_receive_queue_discards_oldest_when_full(self):
        for value in ("one", "two", "three"):
            self.backend.server_cb({"event": 3, "value": value})

        self.assertEqual(self.backend.read_received(), "two")
        self.assertEqual(self.backend.read_received(), "three")


class EasyApiTextReceiveTests(unittest.TestCase):
    def setUp(self):
        import easy_api

        self.api = easy_api
        self.original_uart = easy_api._uart
        self.original_uart_text_buffer = easy_api._uart_text_buffer
        self.original_ble = easy_api._ble
        self.original_features = dict(easy_api.config.FEATURES)

    def tearDown(self):
        self.api._uart = self.original_uart
        self.api._uart_text_buffer = self.original_uart_text_buffer
        self.api._ble = self.original_ble
        self.api.config.FEATURES.clear()
        self.api.config.FEATURES.update(self.original_features)

    def test_readuarttext_decodes_bytes_and_uses_none_for_no_data(self):
        class FakePort:
            values = [b"hello", b""]

            def read_available(self):
                return self.values.pop(0)

        self.api.config.FEATURES["uart"] = True
        self.api._uart = FakePort()

        self.assertEqual(self.api.readuarttext(), "hello")
        self.assertIsNone(self.api.readuarttext())

    def test_readuarttext_removes_only_line_terminators_for_commands(self):
        class FakePort:
            def read_available(self):
                return b"LED_ON\r\n"

        self.api.config.FEATURES["uart"] = True
        self.api._uart = FakePort()
        self.assertEqual(self.api.readuarttext(), "LED_ON")

    def test_readuarttext_reassembles_split_command_line(self):
        class FakePort:
            values = [b"LED_", b"ON\r\n"]
            def read_available(self):
                return self.values.pop(0)

        self.api.config.FEATURES["uart"] = True
        self.api._uart = FakePort()
        self.assertIsNone(self.api.readuarttext())
        self.assertEqual(self.api.readuarttext(), "LED_ON")

    def test_senduart_ignores_none_sentinel(self):
        class FakePort:
            def __init__(self):
                self.writes = []
            def write(self, value):
                self.writes.append(value)

        port = FakePort()
        self.api.config.FEATURES["uart"] = True
        self.api._uart = port
        self.assertFalse(self.api.senduart(None))
        self.assertEqual(port.writes, [])

    def test_senduart_line_frames_legacy_command_ack(self):
        class FakePort:
            def __init__(self):
                self.writes = []
            def write(self, value):
                self.writes.append(value)

        port = FakePort()
        self.api.config.FEATURES["uart"] = True
        self.api.config.UART_AUTO_LINE_COMMANDS = True
        self.api._uart = port
        self.assertTrue(self.api.senduart("ON"))
        self.assertEqual(port.writes, [b"ON\r\n"])
        self.assertTrue(self.api.senduart("payload"))
        self.assertEqual(port.writes[-1], b"payload")

    def test_readbledata_consumes_backend_value(self):
        class FakeBackend:
            obj = object()

            def read_received(self):
                return b"world"

        self.api.config.FEATURES["ble"] = True
        self.api._ble = FakeBackend()

        self.assertEqual(self.api.readbledata(), "world")

    def test_readbledata_decodes_firmware_hex_text(self):
        class FakeBackend:
            obj = object()

            def read_received(self):
                return "50435f54455354"

        self.api.config.FEATURES["ble"] = True
        self.api._ble = FakeBackend()

        self.assertEqual(self.api.readbledata(), "PC_TEST")


class ScratchOperatorTests(unittest.TestCase):
    def setUp(self):
        import easy_api

        self.api = easy_api

    def test_numeric_operators(self):
        self.assertEqual(self.api.yunsuan(7, "+", 5), 12)
        self.assertEqual(self.api.yunsuan(7, "-", 5), 2)
        self.assertEqual(self.api.yunsuan(7, "*", 5), 35)
        self.assertEqual(self.api.yunsuan(7, "/", 2), 3.5)
        self.assertEqual(self.api.yunsuan(7, "//", 2), 3)
        self.assertEqual(self.api.yunsuan(7, "%", 5), 2)
        self.assertEqual(self.api.yunsuan(2, "**", 3), 8)
        self.assertIsNone(self.api.yunsuan(1, "/", 0))

    def test_math_operators(self):
        self.assertEqual(self.api.shuxue("round", 2.5), 3)
        self.assertEqual(self.api.shuxue("round", -1.5), -1)
        self.assertEqual(self.api.shuxue("abs", -8), 8)
        self.assertEqual(self.api.shuxue("floor", 2.9), 2)
        self.assertEqual(self.api.shuxue("ceil", 2.1), 3)
        self.assertEqual(self.api.shuxue("sqrt", 81), 9)
        self.assertAlmostEqual(self.api.shuxue("sin", 30), 0.5, places=7)
        self.assertAlmostEqual(self.api.shuxue("cos", 60), 0.5, places=7)
        self.assertAlmostEqual(self.api.shuxue("tan", 45), 1.0, places=7)
        self.assertAlmostEqual(self.api.shuxue("asin", 0.5), 30.0, places=7)
        self.assertAlmostEqual(self.api.shuxue("acos", 0.5), 60.0, places=7)
        self.assertAlmostEqual(self.api.shuxue("atan", 1), 45.0, places=7)
        self.assertAlmostEqual(self.api.shuxue("ln", 1), 0.0, places=7)
        self.assertAlmostEqual(self.api.shuxue("log10", 100), 2.0, places=7)
        self.assertAlmostEqual(self.api.shuxue("exp", 1), 2.718281828, places=7)
        self.assertEqual(self.api.shuxue("pow10", 3), 1000)
        self.assertIsNone(self.api.shuxue("sqrt", -1))

    def test_compare_and_logic_operators(self):
        self.assertTrue(self.api.bijiao("10", ">", 2))
        self.assertTrue(self.api.bijiao("HELLO", "==", "hello"))
        self.assertTrue(self.api.bijiao(2, "!=", 3))
        self.assertTrue(self.api.bijiao(3, ">=", 3))
        self.assertTrue(self.api.bijiao(2, "<", 3))
        self.assertTrue(self.api.bijiao(3, "<=", 3))
        self.assertTrue(self.api.luoji(True, "and", 1))
        self.assertTrue(self.api.luoji(False, "or", "yes"))
        self.assertTrue(self.api.luoji(False, "not"))

    def test_text_operators_and_conversion(self):
        self.assertEqual(self.api.wenbenchangdu("Quectel"), 7)
        self.assertEqual(self.api.wenbenzifu("ABC", 2), "B")
        self.assertEqual(self.api.wenbenzifu("ABC", 0), "")
        self.assertTrue(self.api.wenbenbaohan("UniKnect", "knect"))
        self.assertEqual(self.api.zhuanshuzi("12.5"), 12.5)
        self.assertEqual(self.api.zhuanshuzi("bad"), 0)
        self.assertEqual(self.api.zhuanwenzi(12), "12")

    def test_random_operator_range(self):
        for _index in range(50):
            value = self.api.suijishu(3, 7)
            self.assertIsInstance(value, int)
            self.assertGreaterEqual(value, 3)
            self.assertLessEqual(value, 7)
        float_value = self.api.suijishu(0.5, 1.5)
        self.assertIsInstance(float_value, float)
        self.assertGreaterEqual(float_value, 0.5)
        self.assertLess(float_value, 1.5)


class EasyApiLocationTests(unittest.TestCase):
    def setUp(self):
        import easy_api

        self.api = easy_api
        self.original_quectel = sys.modules.get("quectel")
        self.original_features = dict(easy_api.config.FEATURES)
        self.original_gnss = easy_api._gnss
        self.original_lbs = easy_api._lbs

        class FakeGNSS:
            location = None

            def start(self):
                return True

            def get_location(self):
                return type(self).location

        class FakeLBS:
            location = None
            last_timeout = None

            def get_location(self, timeout):
                type(self).last_timeout = timeout
                return type(self).location

            def deinit(self):
                pass

        self.FakeGNSS = FakeGNSS
        self.FakeLBS = FakeLBS
        fake_quectel = types.ModuleType("quectel")
        fake_quectel.GNSS = FakeGNSS
        fake_quectel.LBS = FakeLBS
        sys.modules["quectel"] = fake_quectel

        easy_api._gnss = None
        easy_api._lbs = None
        easy_api._errors.clear()
        easy_api.config.FEATURES["gnss"] = True
        easy_api.config.FEATURES["lbs"] = True

    def tearDown(self):
        if self.original_quectel is None:
            sys.modules.pop("quectel", None)
        else:
            sys.modules["quectel"] = self.original_quectel
        self.api.config.FEATURES.clear()
        self.api.config.FEATURES.update(self.original_features)
        self.api._gnss = self.original_gnss
        self.api._lbs = self.original_lbs
        self.api._errors.clear()

    def test_readlocation_prefers_gnss(self):
        self.FakeGNSS.location = {"latitude": 31.230416, "longitude": 121.473701}
        self.FakeLBS.location = {"latitude": 30.0, "longitude": 120.0}

        data = self.api.readlocation()

        self.assertEqual(data["source"], "GNSS")
        self.assertEqual(data["latitude"], 31.230416)
        self.assertIsNone(self.FakeLBS.last_timeout)

    def test_readlocation_falls_back_to_lbs(self):
        self.FakeGNSS.location = None
        self.FakeLBS.location = {"latitude": 30.123456, "longitude": 120.654321}

        data = self.api.readlocation()

        self.assertEqual(data["source"], "LBS")
        self.assertEqual(data["longitude"], 120.654321)
        self.assertEqual(self.FakeLBS.last_timeout, self.api.config.LBS_TIMEOUT_MS)


if __name__ == "__main__":
    unittest.main()
