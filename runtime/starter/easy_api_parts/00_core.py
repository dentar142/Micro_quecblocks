"""Fast beginner-friendly API for the offline competition kit.

This module is the public zero-beginner surface documented by
easy_api接口文档.md.  The backend is intentionally lazy: importing this file
does not initialize hardware, and each feature initializes only when the user
enables, reads, controls, or tests that feature.
"""

import gc
import sys

import config

from lib.kit.compat import sleep_ms, ticks_diff, ticks_ms


_reporter = None
_errors = {}

_display = None
_lcd_temp_active = False
_lcd_temp_until = 0
_lcd_row_temp_until = {}
_leds = None
_buttons = None
_nav = None
_button_events = []
_light = None
_i2c_bus = None
_climate = None
_motion = None
_pwm = None
_uart = None
_uart_id = config.UART_ID
_uart_baudrate = config.UART_BAUDRATE
_uart_timeout = config.UART_TIMEOUT_MS
_rs232 = None
_rs485 = None
_audio = None
_audio_events = []
_audio_current_record_file = config.AUDIO_RECORD_FILE
_audio_record_until = None
_audio_volume = config.AUDIO_VOLUME
_audio_tts_speed = config.AUDIO_TTS_SPEED
_audio_tts_pitch = config.AUDIO_TTS_PITCH
_lte = None
_gnss = None
_lbs = None
_lbs_last_data = None
_lbs_last_attempt_ms = -30000
_ble = None
_ble_mode = getattr(config, "BLE_MODE", "server")
_ble_active_mode = None
_ble_target_name = getattr(config, "BLE_CLIENT_TARGET_NAME", config.BLE_NAME)
_ble_last_attempt_ms = -30000
_ble_addr = None
_ble_connected = False
_ble_notify_enabled = False
_ble_last_event = None
_ble_last_value = None
_ble_client_target_addr = None
_ble_client_target_addr_type = None
_ble_client_scan_results = []
_ble_client_conn_id = -1
_ble_client_mtu = 0
_ble_client_services = []
_ble_client_chars = []
_ble_client_current_desc_char = None


def _bool(value):
    return bool(value)


def _feature(name):
    return bool(config.FEATURES.get(name))


def _set_feature(name, enabled):
    config.FEATURES[name] = _bool(enabled)


def _remember_error(name, exc):
    detail = str(exc) or repr(exc)
    _errors[name] = detail
    return detail


def _clear_error(name):
    if name in _errors:
        del _errors[name]


def _drop_report_display():
    global _display
    _display = None
    if _reporter is not None:
        _reporter.display = None


def _get_reporter():
    global _reporter
    if _reporter is None:
        from lib.kit.report import Reporter
        _reporter = Reporter(_display)
    return _reporter


def _lcd_operation_failed(stage, exc):
    """Report a runtime LCD failure without recursively drawing the report."""
    _remember_error("lcd", exc)
    try:
        print("[TEST][LCD][FAIL] {} {}".format(stage, repr(exc)))
    except Exception:
        print("[TEST][LCD][FAIL] {}".format(stage))
    gc.collect()


def _safe_report(method_name, name, detail=""):
    try:
        getattr(_get_reporter(), method_name)(name, detail)
    except Exception as exc:
        _remember_error("report", exc)
        _drop_report_display()
        try:
            getattr(_get_reporter(), method_name)(name, detail)
        except Exception as retry_exc:
            _remember_error("report", retry_exc)


def _pass(name, detail=""):
    _safe_report("passed", name, detail)
    return True


def _fail(name, detail=""):
    _safe_report("failed", name, detail)
    return False


def _skip(name, detail=""):
    _safe_report("skipped", name, detail)
    return None


def _payload(data):
    if isinstance(data, bytes):
        return data
    if isinstance(data, bytearray):
        return bytes(data)
    return str(data).encode()


def _mirror_uart_to_pc(data):
    if not getattr(config, "UART_MIRROR_TO_PC", True):
        return
    try:
        if isinstance(data, bytes):
            try:
                text = data.decode()
            except Exception:
                text = str(data)
        elif isinstance(data, bytearray):
            try:
                text = bytes(data).decode()
            except Exception:
                text = str(data)
        else:
            text = str(data)
        sys.stdout.write(text)
    except Exception:
        pass


def _close_deinit(obj):
    if not obj:
        return
    deinit = getattr(obj, "deinit", None)
    if deinit:
        try:
            deinit()
        except Exception:
            pass


def _close_uart_port(port):
    if not port:
        return
    uart_obj = getattr(port, "uart", None)
    _close_deinit(uart_obj)


def delay(ms):
    sleep_ms(ms)
    return True


def millis():
    """Return the current monotonic millisecond counter."""
    return ticks_ms()


def _algorithm_func(module_name, func_name):
    module = __import__("lib.alg." + module_name, None, None, (func_name,))
    return getattr(module, func_name)


def baoliuxiaoshu(value, digits):
    """保留小数：api.baoliuxiaoshu(初始变量, 保留小数位数)。"""
    return _algorithm_func("text_format", "baoliuxiaoshu")(value, digits)


def shuzipaixu(values, reverse=False):
    """数字排序：api.shuzipaixu(数字列表或变量, 是否倒序)。"""
    return _algorithm_func("number_algorithms", "shuzipaixu")(values, reverse)


def zuidazhi(values):
    """最大值：api.zuidazhi(数字列表或变量)。"""
    return _algorithm_func("number_algorithms", "zuidazhi")(values)


def zuixiao(values):
    """最小值：api.zuixiao(数字列表或变量)。"""
    return _algorithm_func("number_algorithms", "zuixiao")(values)


def pingjunzhi(values):
    """平均值：api.pingjunzhi(数字列表或变量)。"""
    return _algorithm_func("number_algorithms", "pingjunzhi")(values)


def pin_jie(*items):
    """文字拼接：api.pin_jie(文字或变量, ...)。"""
    return _algorithm_func("text_join", "pin_jie")(*items)


def yunsuan(left, operator, right):
    """数字运算：api.yunsuan(左值, 运算符, 右值)。"""
    return _algorithm_func("operators", "yunsuan")(left, operator, right)


def suijishu(start, end):
    """范围随机数：整数边界返回整数，否则返回小数。"""
    return _algorithm_func("operators", "suijishu")(start, end)


def shuxue(operator, value):
    """单值数学函数：api.shuxue(函数名, 数值)。"""
    return _algorithm_func("operators", "shuxue")(operator, value)


def bijiao(left, operator, right):
    """通用比较：api.bijiao(左值, 比较符, 右值)。"""
    return _algorithm_func("operators", "bijiao")(left, operator, right)


def luoji(left, operator, right=None):
    """逻辑运算：api.luoji(左值, and/or/not, 右值)。"""
    return _algorithm_func("operators", "luoji")(left, operator, right)


def wenbenchangdu(text):
    return _algorithm_func("operators", "wenbenchangdu")(text)


def wenbenzifu(text, index):
    return _algorithm_func("operators", "wenbenzifu")(text, index)


def wenbenbaohan(text, part):
    return _algorithm_func("operators", "wenbenbaohan")(text, part)


def zhuanshuzi(value):
    return _algorithm_func("operators", "zhuanshuzi")(value)


def zhuanwenzi(value):
    return _algorithm_func("operators", "zhuanwenzi")(value)


def init():
    """Warm up enabled, safe devices without taking sensor snapshots."""
    ok = True
    if _feature("leds") and _ensure_leds(False) is None:
        ok = False
    if _feature("buttons") and _ensure_buttons(False) is None:
        ok = False
    if _feature("lcd") and _ensure_display(False) is None:
        ok = False
    if _feature("adc") and _ensure_light(False) is None:
        ok = False
    if _feature("i2c") and _ensure_i2c(False) is None:
        ok = False
    if _feature("uart") and _ensure_uart(False) is None:
        ok = False
    return ok


def status():
    data = {
        "time_ms": ticks_ms(),
        "features": dict(config.FEATURES),
        "errors": dict(_errors),
        "sensors": {},
    }
    if _feature("adc"):
        light_data = _read_light(False)
        if light_data is not None:
            data["sensors"]["light"] = light_data
    if _feature("i2c"):
        addresses = _scan_i2c(False)
        if addresses is not None:
            data["sensors"]["i2c"] = {"addresses": addresses}
        climate_data = _read_climate(False)
        if climate_data is not None:
            data["sensors"]["climate"] = climate_data
        motion_data = _read_motion(False)
        if motion_data is not None:
            data["sensors"]["motion"] = motion_data
    if _feature("lte"):
        lte_data = _read_lte(False)
        if lte_data is not None:
            data["sensors"]["lte"] = lte_data
    if _feature("gnss"):
        gnss_data = _read_gnss(False)
        if gnss_data is not None:
            data["sensors"]["gnss"] = gnss_data
    if _feature("lbs"):
        lbs_data = _read_lbs(False)
        if lbs_data is not None:
            data["sensors"]["lbs"] = lbs_data
    if _feature("ble"):
        ble_data = readble()
        if ble_data is not None:
            data["sensors"]["ble"] = ble_data
    data["errors"] = dict(_errors)
    print(data)
    return data


def ready():
    return testyujian()


def yujian():
    return preflight()


def preflight():
    try:
        from lib.kit.preflight import check_modules
        result = check_modules(config.REQUIRED_FROZEN_MODULES)
    except Exception as exc:
        return _fail("PREFLIGHT", exc)
    missing = [name for name, ok in result.items() if ok is not True]
    if missing:
        return _fail("PREFLIGHT", "missing=" + ",".join(missing))
    return _pass("PREFLIGHT", "all required modules import")


def testyujian():
    return preflight()


def testall():
    tests = (
        testyujian,
        testled,
        testguangmin,
        testi2c,
        testwenhumi,
        testjiasudu,
        testtimer,
        testlcd,
        teststorage,
        testlte,
        testgnss,
        testlbs,
        testble,
    )
    ok = True
    for fn in tests:
        result = fn()
        if result is False:
            ok = False
    _get_reporter().summary()
    return ok



