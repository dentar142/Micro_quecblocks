# UART, RS232 and RS485


def _ensure_uart(report=True):
    global _uart
    if not _feature("uart"):
        if report:
            _skip("UART", "disabled")
        return None
    if _uart is None:
        try:
            from lib.kit.serial_tests import UartPort
            _uart = UartPort(_uart_id, _uart_baudrate, _uart_timeout)
            _clear_error("uart")
        except Exception as exc:
            _remember_error("uart", exc)
            if report:
                _fail("UART", exc)
            return None
    return _uart


def uart(enabled=1, uart_id=None, baudrate=None, timeout=None):
    global _uart, _uart_id, _uart_baudrate, _uart_timeout
    changed = False
    if uart_id is not None and uart_id != _uart_id:
        _uart_id = uart_id
        config.UART_ID = uart_id
        changed = True
    if baudrate is not None and baudrate != _uart_baudrate:
        _uart_baudrate = baudrate
        config.UART_BAUDRATE = baudrate
        changed = True
    if timeout is not None and timeout != _uart_timeout:
        _uart_timeout = timeout
        config.UART_TIMEOUT_MS = timeout
        changed = True
    _set_feature("uart", enabled)
    if changed and _uart is not None:
        _close_uart_port(_uart)
        _uart = None
    if enabled:
        return _ensure_uart() is not None
    _close_uart_port(_uart)
    _uart = None
    return True


def setuart(uart_id, baudrate=115200, timeout=1000):
    return uart(1, uart_id, baudrate, timeout)


def configureuart(uart_id=2, baudrate=115200, bits=8, parity=None, stop=1, timeout=1000, tx=None, rx=None):
    """Configure UART framing and optional TX/RX pin overrides."""
    global _uart, _uart_id, _uart_baudrate, _uart_timeout
    import machine
    _close_uart_port(_uart)
    _uart = None
    _uart_id = int(uart_id)
    _uart_baudrate = int(baudrate)
    _uart_timeout = int(timeout)
    config.UART_ID = _uart_id
    config.UART_BAUDRATE = _uart_baudrate
    config.UART_TIMEOUT_MS = _uart_timeout
    kwargs = {"bits": int(bits), "parity": parity, "stop": int(stop), "timeout": _uart_timeout}
    if tx:
        kwargs["tx"] = machine.Pin(str(tx))
    if rx:
        kwargs["rx"] = machine.Pin(str(rx))
    try:
        obj = machine.UART(_uart_id, _uart_baudrate, **kwargs)
    except Exception:
        obj = machine.UART(_uart_id, _uart_baudrate, timeout=_uart_timeout)
    from lib.kit.serial_tests import UartPort
    port = UartPort.__new__(UartPort)
    port.uart = obj
    _uart = port
    _set_feature("uart", 1)
    return True


def senduart(data):
    port = _ensure_uart()
    if not port:
        return None
    port.write(_payload(data))
    _mirror_uart_to_pc(data)
    return True


def readuart():
    port = _ensure_uart()
    return port.read_available() if port else None


def readuarttext():
    """Read currently available UART2 data as display-ready text."""
    data = readuart()
    if not data:
        return None
    if isinstance(data, (bytes, bytearray)):
        try:
            return bytes(data).decode("utf-8")
        except Exception:
            return str(bytes(data))
    return str(data)


def waituart(timeout=10000):
    start = ticks_ms()
    while ticks_diff(ticks_ms(), start) < timeout:
        data = readuart()
        if data:
            return data
        sleep_ms(20)
    return None


def testuart(data=b"hello"):
    port = _ensure_uart()
    if not port:
        return None
    ok, detail = port.loopback(_payload(data))
    return _pass("UART", detail) if ok else _fail("UART", detail)


def rs232(enabled=1):
    global _rs232
    _set_feature("rs232", enabled)
    if enabled:
        if not config.RS232_TRANSCEIVER_CONFIRMED:
            return _skip("RS232", "RS232_TRANSCEIVER_CONFIRMED=False")
        if _rs232 is None:
            try:
                from lib.kit.serial_tests import UartPort
                _rs232 = UartPort(config.UART_ID, config.UART_BAUDRATE, config.UART_TIMEOUT_MS)
            except Exception as exc:
                return _fail("RS232", exc)
        return True
    _close_uart_port(_rs232)
    _rs232 = None
    return True


def _rs232_port():
    if _rs232 is None:
        result = rs232(1)
        if result is None or result is False:
            return None
    return _rs232


def sendrs232(data=b"RS232"):
    port = _rs232_port()
    if not port:
        return None
    port.write(_payload(data))
    return True


def readrs232():
    port = _rs232_port()
    return port.read_available() if port else None


def readrs232text():
    data = readrs232()
    if not data:
        return None
    if isinstance(data, (bytes, bytearray)):
        try:
            return bytes(data).decode("utf-8")
        except Exception:
            return str(bytes(data))
    return str(data)


def testrs232(data=b"RS232"):
    port = _rs232_port()
    if not port:
        return None
    ok, detail = port.loopback(_payload(data))
    return _pass("RS232", detail) if ok else _fail("RS232", detail)


def rs485(enabled=1):
    global _rs485
    _set_feature("rs485", enabled)
    if enabled:
        if not config.RS485_DIRECTION_PIN:
            return _skip("RS485", "set RS485_DIRECTION_PIN")
        if _rs485 is None:
            try:
                from lib.kit.serial_tests import Rs485Port
                _rs485 = Rs485Port(
                    config.UART_ID,
                    config.UART_BAUDRATE,
                    config.UART_TIMEOUT_MS,
                    config.RS485_DIRECTION_PIN,
                )
            except Exception as exc:
                return _fail("RS485", exc)
        return True
    _close_uart_port(_rs485)
    _rs485 = None
    return True


def _rs485_port():
    if _rs485 is None:
        result = rs485(1)
        if result is None or result is False:
            return None
    return _rs485


def setrs485tx(enabled):
    port = _rs485_port()
    if not port:
        return None
    port.set_tx(bool(enabled))
    return True


def sendrs485(data=b"RS485"):
    port = _rs485_port()
    if not port:
        return None
    port.set_tx(True)
    port.write(_payload(data))
    sleep_ms(20)
    port.set_tx(False)
    return True


def readrs485():
    port = _rs485_port()
    return port.read_available() if port else None


def readrs485text():
    data = readrs485()
    if not data:
        return None
    if isinstance(data, (bytes, bytearray)):
        try:
            return bytes(data).decode("utf-8")
        except Exception:
            return str(bytes(data))
    return str(data)


def testrs485(data=b"RS485"):
    port = _rs485_port()
    if not port:
        return None
    ok, detail = port.loopback(_payload(data))
    return _pass("RS485", detail) if ok else _fail("RS485", detail)



