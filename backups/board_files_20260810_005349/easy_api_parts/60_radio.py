# LTE / 4G, GNSS and BLE


def _call_optional(obj, name, *args):
    fn = getattr(obj, name, None)
    if not fn:
        return None
    return fn(*args)


def _try_lte_snapshot(net):
    data = {}
    for name in ("query_usim", "status", "get_status", "get_signal", "query_signal", "attached", "is_attached"):
        try:
            value = _call_optional(net, name)
            if value is not None:
                data[name] = value
        except Exception as exc:
            data[name] = "error:" + str(exc)
    return data


def _ensure_lte(report=True):
    global _lte
    if not _feature("lte"):
        if report:
            _skip("LTE", "disabled")
        return None
    if _lte is None:
        try:
            from quectel import Network
            net = Network()
            init_result = _call_optional(net, "init")
            if init_result is False:
                _remember_error("lte", "init failed")
                if report:
                    _fail("LTE", "init failed")
                return None
            _call_optional(net, "query_usim")
            attach_result = _call_optional(net, "attach")
            if attach_result is False:
                _remember_error("lte", "attach failed")
                if report:
                    _fail("LTE", "attach failed")
                return None
            _lte = net
            _clear_error("lte")
        except Exception as exc:
            _lte = None
            _remember_error("lte", exc)
            if report:
                _fail("LTE", exc)
            return None
    return _lte


def lte(enabled=1):
    global _lte
    _set_feature("lte", enabled)
    _set_feature("network", enabled)
    if enabled:
        return _ensure_lte() is not None
    if _lte:
        try:
            _call_optional(_lte, "detach")
            _call_optional(_lte, "stop")
            _call_optional(_lte, "deinit")
        except Exception:
            pass
    _lte = None
    return True


g4 = lte
network4g = lte


def _read_lte(report=True):
    net = _ensure_lte(report)
    if not net:
        return None
    try:
        data = _try_lte_snapshot(net)
        _clear_error("lte")
        return data
    except Exception as exc:
        _remember_error("lte", exc)
        if report:
            _fail("LTE", exc)
        return None


def readlte():
    return _read_lte()


readg4 = readlte


def networkstatus():
    """Return a bounded LTE diagnostic snapshot using only supported optional APIs."""
    data = _read_lte()
    if not data:
        return {}
    result = {}
    sim = data.get("query_usim")
    result["sim"] = sim
    for key in ("status", "get_status"):
        if data.get(key) is not None:
            result["status"] = data.get(key)
            break
    for key in ("get_signal", "query_signal"):
        if data.get(key) is not None:
            result["signal"] = data.get(key)
            break
    result["registered"] = result.get("status")
    result["attached"] = data.get("attached")
    if result["attached"] is None:
        result["attached"] = data.get("is_attached")
    return result


def testlte():
    if not _feature("lte"):
        return _skip("LTE", "disabled")
    data = _read_lte()
    if data is None:
        return False
    return _pass("LTE", str(data))


def _ensure_gnss(report=True):
    global _gnss
    if not _feature("gnss"):
        if report:
            _skip("GNSS", "disabled")
        return None
    if _gnss is None:
        try:
            from quectel import GNSS as QuectelGNSS
            obj = QuectelGNSS()
            start = getattr(obj, "start", None)
            if start and start() is False:
                _remember_error("gnss", "start failed")
                if report:
                    _fail("GNSS", "start failed")
                return None
            _gnss = obj
            _clear_error("gnss")
        except Exception as exc:
            _gnss = None
            _remember_error("gnss", exc)
            if report:
                _fail("GNSS", exc)
            return None
    return _gnss


def gnss(enabled=1):
    global _gnss
    _set_feature("gnss", enabled)
    if enabled:
        return _ensure_gnss() is not None
    if _gnss:
        try:
            _call_optional(_gnss, "stop")
            _call_optional(_gnss, "deinit")
        except Exception:
            pass
    _gnss = None
    return True


GNSS = gnss


def _read_gnss(report=True, timeout=None):
    obj = _ensure_gnss(report)
    if not obj:
        return None
    timeout = config.GNSS_TIMEOUT_MS if timeout is None else timeout
    try:
        if int(timeout) <= 0:
            timeout = 15000
    except Exception:
        timeout = 15000
    start = ticks_ms()
    while True:
        try:
            loc = _call_optional(obj, "get_location")
            if loc:
                _clear_error("gnss")
                return loc
        except Exception as exc:
            _remember_error("gnss", exc)
            if report:
                _fail("GNSS", exc)
            return None
        if not timeout or ticks_diff(ticks_ms(), start) >= timeout:
            return None
        sleep_ms(200)


def readgnss():
    return _read_gnss()


def readgnsslat():
    data = readgnss()
    return data.get("latitude") if data else None


def readgnsslon():
    data = readgnss()
    return data.get("longitude") if data else None


readgnss_lat = readgnsslat
readgnss_lon = readgnsslon
GNSSread = readgnss
GNSSreadLat = readgnsslat
GNSSreadLon = readgnsslon


def testgnss():
    if not _feature("gnss"):
        return _skip("GNSS", "disabled")
    obj = _ensure_gnss()
    if not obj:
        return False
    data = readgnss()
    if not data:
        return _skip("GNSS", "started; no fix yet")
    return _pass("GNSS", "lat={} lon={}".format(
        data.get("latitude"),
        data.get("longitude"),
    ))


def _location_with_source(data, source):
    if not data:
        return None
    try:
        lat = data.get("latitude")
        lon = data.get("longitude")
    except Exception:
        return None
    if lat is None or lon is None:
        return None
    result = {}
    try:
        result.update(data)
    except Exception:
        pass
    result["latitude"] = lat
    result["longitude"] = lon
    result["source"] = source
    return result


def _ensure_lbs(report=True):
    global _lbs
    if not _feature("lbs"):
        if report:
            _skip("LBS", "disabled")
        return None
    if _lbs is None:
        try:
            from quectel import LBS as QuectelLBS
            _lbs = QuectelLBS()
            _clear_error("lbs")
        except Exception as exc:
            _lbs = None
            _remember_error("lbs", exc)
            if report:
                _fail("LBS", exc)
            return None
    return _lbs


def lbs(enabled=1):
    global _lbs, _lbs_last_data, _lbs_last_attempt_ms
    _set_feature("lbs", enabled)
    _set_feature("network", enabled)
    if enabled:
        # 只初始化对象，不在启用时立即定位；定位可能需要 SIM/网络并会阻塞。
        return _ensure_lbs(False) is not None
    if _lbs:
        try:
            _call_optional(_lbs, "deinit")
        except Exception:
            pass
    _lbs = None
    _lbs_last_data = None
    _lbs_last_attempt_ms = -30000
    return True


LBS = lbs


def _read_lbs(report=True, timeout=None):
    global _lbs_last_data, _lbs_last_attempt_ms
    obj = _ensure_lbs(report)
    if not obj:
        return None
    timeout = config.LBS_TIMEOUT_MS if timeout is None else timeout
    try:
        if timeout < 10000:
            timeout = 10000
    except Exception:
        timeout = 10000
    now = ticks_ms()
    retry_ms = getattr(config, "LBS_RETRY_INTERVAL_MS", 30000)
    if retry_ms and ticks_diff(now, _lbs_last_attempt_ms) < retry_ms:
        return _lbs_last_data
    _lbs_last_attempt_ms = now
    try:
        loc = obj.get_location(timeout)
        data = _location_with_source(loc, "LBS")
        if data:
            _lbs_last_data = data
            _clear_error("lbs")
            return data
        _lbs_last_data = None
        return None
    except Exception as exc:
        _lbs_last_data = None
        _remember_error("lbs", exc)
        if report:
            _fail("LBS", exc)
        return None


def readlbs():
    return _read_lbs()


def readlbslat():
    data = readlbs()
    return data.get("latitude") if data else None


def readlbslon():
    data = readlbs()
    return data.get("longitude") if data else None


def readlocation():
    gnss_data = _location_with_source(_read_gnss(False), "GNSS")
    if gnss_data:
        return gnss_data
    return _read_lbs(False)


def readlocationlat():
    data = readlocation()
    return data.get("latitude") if data else None


def readlocationlon():
    data = readlocation()
    return data.get("longitude") if data else None


def testlbs():
    if not _feature("lbs"):
        return _skip("LBS", "disabled")
    data = readlbs()
    if not data:
        return _skip("LBS", "enabled; no location yet")
    return _pass("LBS", "lat={} lon={}".format(
        data.get("latitude"),
        data.get("longitude"),
    ))


def _ascii_hex(value):
    if isinstance(value, bytes):
        raw = value
    elif isinstance(value, bytearray):
        raw = bytes(value)
    else:
        raw = str(value).encode()
    return "".join("{:02X}".format(b) for b in raw)




def _ble_backend_obj():
    global _ble
    if _ble is None:
        from lib.kit.ble_modes import EasyBLE
        _ble = EasyBLE(config, sleep_ms, ticks_ms, ticks_diff, _ascii_hex)
    return _ble


def setblemode(mode="server", target_name=None):
    return _ble_backend_obj().set_mode(mode, target_name)


def ble(enabled=1, mode=None, target_name=None):
    _set_feature("ble", enabled)
    if enabled:
        return _ble_backend_obj().enable(mode, target_name)
    if _ble:
        _ble.stop()
    return True


def bleserver(enabled=1):
    return ble(enabled, "server")


def bleclient(enabled=1, target_name=None):
    return ble(enabled, "client", target_name)


def scanble(timeout=5000, target_name=None):
    _set_feature("ble", 1)
    return _ble_backend_obj().scan(timeout, target_name)


def connectble(target_name=None, timeout=10000):
    _set_feature("ble", 1)
    return _ble_backend_obj().connect(target_name, timeout)


def discoverble(timeout=5000):
    return _ble_backend_obj().discover(timeout)


def readble():
    if not _feature("ble"):
        return {"name": config.BLE_NAME, "mode": getattr(config, "BLE_MODE", "server"), "ready": False, "error": "disabled"}
    backend = _ble_backend_obj()
    if backend.obj is None:
        backend.enable()
    return backend.status()


readbleclient = readble


def readblesent():
    """Return the last successfully transmitted BLE text without consuming RX."""
    if not _feature("ble"):
        return None
    backend = _ble_backend_obj()
    if backend.obj is None:
        backend.enable()
    return backend.last_sent


def readbletext():
    """Return a compact BLE status suitable for one LCD row or UART output."""
    data = readble() or {}
    if not data.get("ready"):
        return "BLE: disabled/" + str(data.get("error") or "not ready")
    mode = str(data.get("mode") or "server")
    connected = 1 if data.get("connected") else 0
    received = data.get("last_value")
    sent = data.get("last_sent")
    return "BLE:{} C{} RX:{} TX:{}".format(mode, connected, received if received is not None else "-", sent if sent is not None else "-")


def readbledata():
    """Consume one newly received BLE value and return display-ready text."""
    if not _feature("ble"):
        return None
    backend = _ble_backend_obj()
    if backend.obj is None:
        backend.enable()
    value = backend.read_received()
    if value is None:
        return None
    if isinstance(value, (bytes, bytearray)):
        try:
            return bytes(value).decode("utf-8")
        except Exception:
            return str(bytes(value))
    text = str(value)
    compact = text.strip()
    if compact and len(compact) % 2 == 0 and all(char in "0123456789abcdefABCDEF" for char in compact):
        try:
            raw = bytes(int(compact[index:index + 2], 16) for index in range(0, len(compact), 2))
            return raw.decode("utf-8")
        except Exception:
            pass
    return text


def readblehandle(handle=None):
    return _ble_backend_obj().read_handle(handle)


def writeblehandle(handle, data):
    return _ble_backend_obj().write_handle(handle, data)


def sendble(data, handle=None):
    if not _feature("ble"):
        return None
    return _ble_backend_obj().send(data, handle)


def testble():
    if not _feature("ble"):
        return _skip("BLE", "disabled")
    data = readble()
    if data.get("ready"):
        return _pass("BLE", "mode={} name={} addr={}".format(data.get("mode"), data.get("name"), data.get("addr") or data.get("target_addr")))
    return _skip("BLE", data.get("error"))



