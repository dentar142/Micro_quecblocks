# ADC and I2C sensors


def _ensure_light(report=True):
    global _light
    if not _feature("adc"):
        if report:
            _skip("LIGHT", "disabled")
        return None
    if _light is None:
        try:
            from lib.kit.sensors import LightSensor
            _light = LightSensor(config.LIGHT_ADC_PIN)
            _clear_error("light")
        except Exception as exc:
            _remember_error("light", exc)
            if report:
                _fail("LIGHT", exc)
            return None
    return _light


def _read_light(report=True):
    sensor = _ensure_light(report)
    if not sensor:
        return None
    try:
        data = sensor.read()
        _clear_error("light")
        return data
    except Exception as exc:
        _remember_error("light", exc)
        if report:
            _fail("LIGHT", exc)
        return None


def guangmin(enabled=1):
    global _light
    _set_feature("adc", enabled)
    if enabled:
        return _ensure_light() is not None
    _light = None
    return True


guangming = guangmin
light = guangmin


def readguangmin():
    data = _read_light()
    return data.get("raw_u16") if data else None


def readguangmin_percent():
    data = _read_light()
    return data.get("percent") if data else None


def readguangmin_all():
    data = _read_light()
    if not data:
        return None
    return {
        "raw": data.get("raw_u16"),
        "voltage": data.get("voltage"),
        "percent": data.get("percent"),
    }


def testguangmin():
    data = readguangmin_all()
    if not data:
        return False
    return _pass("LIGHT", "raw={} voltage={:.2f} percent={:.1f}".format(
        data["raw"], data["voltage"], data["percent"]
    ))


def _ensure_i2c(report=True):
    global _i2c_bus
    if not _feature("i2c"):
        if report:
            _skip("I2C", "disabled")
        return None
    if _i2c_bus is None:
        try:
            from lib.kit.sensors import I2CBus
            _i2c_bus = I2CBus(config.I2C_ID, config.I2C_FREQ)
            _clear_error("i2c")
        except Exception as exc:
            _remember_error("i2c", exc)
            if report:
                _fail("I2C", exc)
            return None
    return _i2c_bus


def _scan_i2c(report=True):
    bus = _ensure_i2c(report)
    if not bus:
        return None
    try:
        addresses = bus.scan()
        _clear_error("i2c")
        return addresses
    except Exception as exc:
        _remember_error("i2c", exc)
        if report:
            _fail("I2C", exc)
        return None


def i2c(enabled=1):
    global _i2c_bus, _climate, _motion
    _set_feature("i2c", enabled)
    if enabled:
        return _ensure_i2c() is not None
    _i2c_bus = None
    _climate = None
    _motion = None
    return True


def scani2c():
    return _scan_i2c()


def testi2c():
    addresses = scani2c()
    if addresses is None:
        return False
    return _pass("I2C", ",".join(hex(x) for x in addresses))


def _ensure_climate(report=True):
    global _climate
    bus = _ensure_i2c(report)
    if not bus:
        return None
    if _climate is None:
        try:
            from lib.kit.sensors import ClimateSensor
            _climate = ClimateSensor(bus.bus)
            _clear_error("climate")
        except Exception as exc:
            _remember_error("climate", exc)
            if report:
                _fail("AHT20", exc)
            return None
    return _climate


def _read_climate(report=True):
    sensor = _ensure_climate(report)
    if not sensor:
        return None
    try:
        data = sensor.read()
        _clear_error("climate")
        return data
    except Exception as exc:
        _remember_error("climate", exc)
        if report:
            _fail("AHT20", exc)
        return None


def wenhumi(enabled=1):
    global _climate
    _set_feature("i2c", enabled)
    if enabled:
        return _ensure_climate() is not None
    _climate = None
    return True


aht20 = wenhumi


def readwenhumi():
    data = _read_climate()
    if not data:
        return None
    return (data.get("temperature_c"), data.get("humidity_percent"))


def readwendu():
    data = readwenhumi()
    return data[0] if data else None


def readshidu():
    data = readwenhumi()
    return data[1] if data else None


def testwenhumi():
    data = readwenhumi()
    if not data:
        return False
    return _pass("AHT20", "temperature={:.2f} humidity={:.2f}".format(data[0], data[1]))


def _ensure_motion(report=True):
    global _motion
    bus = _ensure_i2c(report)
    if not bus:
        return None
    if _motion is None:
        try:
            from lib.kit.sensors import MotionSensor
            _motion = MotionSensor(bus.bus)
            _clear_error("motion")
        except Exception as exc:
            _remember_error("motion", exc)
            if report:
                _fail("LIS2DH12", exc)
            return None
    return _motion


def _read_motion(report=True):
    sensor = _ensure_motion(report)
    if not sensor:
        return None
    try:
        data = sensor.read()
        _clear_error("motion")
        return data
    except Exception as exc:
        _remember_error("motion", exc)
        if report:
            _fail("LIS2DH12", exc)
        return None


def jiasudu(enabled=1):
    global _motion
    _set_feature("i2c", enabled)
    if enabled:
        return _ensure_motion() is not None
    _motion = None
    return True


motion = jiasudu


def readjiasudu():
    data = _read_motion()
    if not data:
        return None
    return (data.get("x"), data.get("y"), data.get("z"))


def readx():
    data = readjiasudu()
    return data[0] if data else None


def readyaxis():
    data = readjiasudu()
    return data[1] if data else None


def readz():
    data = readjiasudu()
    return data[2] if data else None


def testjiasudu():
    data = readjiasudu()
    if not data:
        return False
    return _pass("LIS2DH12", "x={} y={} z={}".format(data[0], data[1], data[2]))



