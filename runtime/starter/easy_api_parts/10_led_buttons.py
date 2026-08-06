# LED


def _ensure_leds(report=True):
    global _leds
    if not _feature("leds"):
        if report:
            _skip("LED", "disabled")
        return None
    if _leds is None:
        try:
            from lib.kit.leds import LedBank
            _leds = LedBank(config.LED_PINS)
            if _leds.errors:
                _errors["leds"] = _leds.errors
            else:
                _clear_error("leds")
        except Exception as exc:
            _remember_error("leds", exc)
            if report:
                _fail("LED", exc)
            return None
    return _leds


def led(enabled=1):
    global _leds
    _set_feature("leds", enabled)
    if enabled:
        return _ensure_leds() is not None
    if _leds:
        try:
            _leds.all_off()
        except Exception:
            pass
    _leds = None
    return True


def setled(name, value):
    leds = _ensure_leds()
    if not leds:
        return None
    try:
        leds.set(name, bool(value))
        return True
    except Exception as exc:
        _remember_error("leds", exc)
        return _fail("LED", exc)


def ledoff():
    if _leds:
        _leds.all_off()
    return True


def ledrun(delay_ms=250):
    leds = _ensure_leds()
    if not leds:
        return None
    leds.cycle(delay_ms)
    return True


def testled():
    leds = _ensure_leds()
    if not leds:
        return None if not _feature("leds") else False
    if not leds.names():
        return _fail("LED", _errors.get("leds", "not initialized"))
    leds.cycle(200)
    return _pass("LED", ",".join(leds.names()))


# Buttons


def _ensure_buttons(report=True):
    global _buttons, _nav
    if not _feature("buttons"):
        if report:
            _skip("BUTTON", "disabled")
        return None
    if _buttons is None:
        try:
            import machine
            from lib.kit.buttons import AnalogNavigation, ButtonManager
            manager = ButtonManager(
                config.BUTTON_DEBOUNCE_MS,
                config.BUTTON_LONG_MS,
                config.BUTTON_REPEAT_DELAY_MS,
                config.BUTTON_REPEAT_MS,
            )
            user = machine.Pin(config.USER_BUTTON_PIN, machine.Pin.IN, machine.Pin.PULL_DOWN)
            manager.add("user", lambda: user.value() == 1)
            nav_adc = machine.ADC(machine.Pin(config.NAV_ADC_PIN))
            nav = AnalogNavigation(nav_adc, config.NAV_THRESHOLDS, config.NAV_RELEASE_MIN)
            manager.add_poll_hook(nav)
            for key in ("up", "down", "left", "right", "center"):
                manager.add(key, nav.source_for(key))
            _buttons = manager
            _nav = nav
            _clear_error("buttons")
        except Exception as exc:
            _remember_error("buttons", exc)
            if report:
                _fail("BUTTON", exc)
            return None
    return _buttons


def anjian(enabled=1):
    global _buttons, _nav, _button_events
    _set_feature("buttons", enabled)
    if enabled:
        return _ensure_buttons() is not None
    _buttons = None
    _nav = None
    _button_events = []
    return True


button = anjian


def readanjian():
    global _button_events
    buttons = _ensure_buttons()
    if not buttons:
        return None
    if _button_events:
        return _button_events.pop(0)
    events = buttons.poll(ticks_ms())
    if not events:
        return None
    _button_events.extend(events)
    return _button_events.pop(0)


readbutton = readanjian


def keytext(event):
    """Return a compact SHORT/LONG label for a button event, else None."""
    if not event or len(event) < 2 or event[1] not in ("short", "long"):
        return None
    return "{} {}".format(event[0], event[1]).upper()


def readanjianadc():
    """Read the raw ADC value used by the five-way analog navigation key."""
    buttons = _ensure_buttons()
    if not buttons or _nav is None:
        return None
    try:
        return _nav.read_raw()
    except Exception as exc:
        _remember_error("buttons", exc)
        return None


readbuttonadc = readanjianadc
readkeyadc = readanjianadc


def waitanjian(timeout=10000):
    return _wait_button(None, None, timeout)


waitbutton = waitanjian


def waitkey(name, timeout=10000, event="short"):
    return _wait_button(name, event, timeout)


def waitshort(timeout=10000):
    return _wait_button(None, "short", timeout)


def waitlong(timeout=10000):
    return _wait_button(None, "long", timeout)


def _wait_button(match_name=None, match_event=None, timeout=10000):
    buttons = _ensure_buttons()
    if not buttons:
        return None
    start = ticks_ms()
    while ticks_diff(ticks_ms(), start) < timeout:
        for name, event in buttons.poll(ticks_ms()):
            if match_name is not None and name != match_name:
                continue
            if match_event is not None and event != match_event:
                continue
            return (name, event)
        sleep_ms(20)
    return None


def iskey(name):
    buttons = _ensure_buttons()
    if not buttons:
        return False
    source = buttons.sources.get(name)
    return bool(source()) if source else False


def testanjian(timeout=15000):
    buttons = _ensure_buttons()
    if not buttons:
        return None if not _feature("buttons") else False
    needed = ("user", "up", "down", "left", "right", "center")
    seen = []
    print("[PROMPT] Press keys: " + ",".join(needed))
    start = ticks_ms()
    while ticks_diff(ticks_ms(), start) < timeout and len(seen) < len(needed):
        for name, event in buttons.poll(ticks_ms()):
            print("[BUTTON][{}][{}]".format(name, event))
            if event == "short" and name in needed and name not in seen:
                seen.append(name)
        sleep_ms(20)
    missing = [name for name in needed if name not in seen]
    if missing:
        return _fail("BUTTON", "missing=" + ",".join(missing))
    return _pass("BUTTON", "all keys detected")


testbutton = testanjian


def testanjianled(timeout=15000):
    leds = _ensure_leds()
    if not leds:
        return None
    buttons = _ensure_buttons()
    if not buttons:
        return None
    led_name = leds.names()[0] if leds.names() else None
    if not led_name:
        return _fail("BUTTON_LED", "no LED")
    state = False
    print("[PROMPT] Press any key to toggle LED")
    start = ticks_ms()
    while ticks_diff(ticks_ms(), start) < timeout:
        for name, event in buttons.poll(ticks_ms()):
            if event == "short":
                state = not state
                leds.set(led_name, state)
                return _pass("BUTTON_LED", "{} {}".format(name, event))
        sleep_ms(20)
    return _fail("BUTTON_LED", "timeout")


testbuttonled = testanjianled



