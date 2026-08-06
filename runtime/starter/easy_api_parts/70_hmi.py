# HMI


def hmi(enabled=1):
    _set_feature("lcd", enabled)
    _set_feature("buttons", enabled)
    if enabled:
        display_ok = _ensure_display() is not None
        buttons_ok = _ensure_buttons() is not None
        return display_ok and buttons_ok
    lcd(0)
    anjian(0)
    return True


def menu():
    return runhmi()


def runhmi(timeout=30000):
    display = _ensure_display()
    buttons = _ensure_buttons()
    if not display or not buttons:
        return _skip("HMI", "display/buttons not initialized")
    from lib.kit.menu import Menu
    items = (
        ("led", testled),
        ("adc", testguangmin),
        ("i2c", testi2c),
        ("sensors", lambda: testwenhumi() and testjiasudu()),
        ("timer", testtimer),
        ("storage", teststorage),
    )
    m = Menu(display, items)
    m.bind(buttons)
    print("[PROMPT] Use up/down/center on LCD shield")
    start = ticks_ms()
    while ticks_diff(ticks_ms(), start) < timeout:
        buttons.poll(ticks_ms())
        sleep_ms(20)
    return _pass("HMI", "menu loop ended")


def testhmi():
    return runhmi(10000)

