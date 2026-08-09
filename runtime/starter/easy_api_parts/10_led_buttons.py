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
    global _leds, _led_pwm, _led_breathe_state
    _set_feature("leds", enabled)
    if enabled:
        return _ensure_leds() is not None
    if _leds:
        try:
            _leds.all_off()
        except Exception:
            pass
    _stop_led_pwm()
    _led_pwm = {}
    _led_breathe_state = {}
    _leds = None
    return True


def setled(name, value):
    global _led_breathe_state
    leds = _ensure_leds()
    if not leds:
        return None
    try:
        channel = str(name).lower()
        _stop_led_pwm(channel)
        if not isinstance(_led_breathe_state, dict):
            _led_breathe_state = {}
        _led_breathe_state.pop(channel, None)
        leds.set(channel, bool(value))
        return True
    except Exception as exc:
        _remember_error("leds", exc)
        return _fail("LED", exc)


def ledoff():
    global _led_breathe_state
    _stop_led_pwm()
    _led_breathe_state = {}
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


def _stop_led_pwm(name=None):
    global _led_pwm
    if not isinstance(_led_pwm, dict):
        try:
            _led_pwm.stop()
        except Exception:
            pass
        _led_pwm = {}
        return
    names = tuple(_led_pwm.keys()) if name is None else (str(name).lower(),)
    for channel in names:
        output = _led_pwm.pop(channel, None)
        if output:
            try:
                output.stop()
            except Exception:
                pass


def _stop_led_pwm_if_needed(name):
    _stop_led_pwm(str(name).lower())


def ledbrightness(name="green", duty=100, freq=None):
    """Set independent hardware-PWM brightness for any of the three LEDs."""
    global _led_pwm, _led_breathe_state
    leds = _ensure_leds()
    if not leds:
        return None
    channel = str(name or "green").lower()
    pwm_spec = config.LED_PWM_CHANNELS.get(channel)
    if pwm_spec is None:
        return _fail("LED_PWM", "unknown LED channel: " + channel)
    duty = max(0, min(100, float(duty)))
    try:
        if not isinstance(_led_pwm, dict):
            _stop_led_pwm()
        if not isinstance(_led_breathe_state, dict):
            _led_breathe_state = {}
        _led_breathe_state.pop(channel, None)
        output = _led_pwm.get(channel)
        if output is None:
            from lib.kit.io_tests import PwmOutput
            output = PwmOutput(
                pwm_spec[0], freq or config.LED_PWM_FREQ, duty,
                timer_id=pwm_spec[1], timer_channel=pwm_spec[2],
                prefer_pyb=True,
            )
            output.start()
            _led_pwm[channel] = output
        else:
            output.set_duty(duty)
        return True
    except Exception as exc:
        _stop_led_pwm(channel)
        _remember_error("leds", exc)
        return _fail("LED_PWM", exc)


def ledbreathe(name="green", period_ms=None, min_duty=0, max_duty=100, steps=32):
    """Start one LED's non-blocking breathe cycle; call updateled() often."""
    global _led_breathe_state
    channel = str(name or "green").lower()
    if channel not in config.LED_PWM_CHANNELS:
        return _fail("LED_BREATHE", "unknown LED channel: " + channel)
    period = max(200, int(period_ms or config.LED_BREATHE_DEFAULT_PERIOD_MS))
    low = max(0, min(100, int(min_duty)))
    high = max(low, min(100, int(max_duty)))
    count = max(4, min(128, int(steps)))
    if not isinstance(_led_breathe_state, dict):
        _led_breathe_state = {}
    current = _led_breathe_state.get(channel)
    if current and current.get("period") == period and current.get("low") == low and current.get("high") == high and current.get("steps") == count:
        # Repeated calls from a user loop must not restart the animation.
        return updateled()
    result = ledbrightness(channel, low)
    if result:
        _led_breathe_state[channel] = {
            "name": channel, "period": period, "low": low, "high": high,
            "steps": count, "index": 0, "last": ticks_ms(),
        }
    return result


def updateled():
    """Advance all active non-blocking LED breathe animations."""
    global _led_breathe_state
    if not isinstance(_led_breathe_state, dict) or not _led_breathe_state:
        return False
    now = ticks_ms()
    for channel in tuple(_led_breathe_state.keys()):
        state = _led_breathe_state.get(channel)
        if not state:
            continue
        interval = max(10, int(state["period"] / (state["steps"] * 2)))
        if ticks_diff(now, state["last"]) < interval:
            continue
        state["last"] = now
        state["index"] = (state["index"] + 1) % (state["steps"] * 2)
        phase = state["index"]
        if phase > state["steps"]:
            phase = state["steps"] * 2 - phase
        span = state["high"] - state["low"]
        output = _led_pwm.get(channel) if isinstance(_led_pwm, dict) else None
        if output:
            output.set_duty(state["low"] + span * phase / state["steps"])
    return True


def led1(value=1):
    """LED1 green PB0 digital on/off."""
    return setled("green", value)


def led2(value=1):
    """LED2 blue PB7 digital on/off."""
    return setled("blue", value)


def led3(value=1):
    """LED3 red PB14 digital on/off."""
    return setled("red", value)


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
    global _buttons, _nav, _button_events, _last_button_event
    _set_feature("buttons", enabled)
    if enabled:
        return _ensure_buttons() is not None
    _buttons = None
    _nav = None
    _button_events = []
    _last_button_event = None
    return True


button = anjian


def readanjian():
    global _button_events, _last_button_event
    buttons = _ensure_buttons()
    if not buttons:
        return None
    if _button_events:
        _last_button_event = _button_events.pop(0)
        return _last_button_event
    events = buttons.poll(ticks_ms())
    if not events:
        return None
    _button_events.extend(events)
    _last_button_event = _button_events.pop(0)
    return _last_button_event


readbutton = readanjian


def lastanjian():
    """Return the most recently returned event without consuming another one."""
    return _last_button_event


lastbutton = lastanjian


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


def readanjian_direction():
    """Return the current five-way direction name from the configured ADC pin.

    The mapping is defined by config.NAV_THRESHOLDS and therefore follows the
    UniKnect LCD Shield calibration rather than assuming ADC value order.
    Returns ``None`` while released or outside calibrated ranges.
    """
    buttons = _ensure_buttons()
    if not buttons or _nav is None:
        return None
    try:
        return _nav.read_key()
    except Exception as exc:
        _remember_error("buttons", exc)
        return None


readkeydirection = readanjian_direction
buttondirection = readanjian_direction


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
    global _last_button_event
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
            _last_button_event = (name, event)
            return _last_button_event
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



