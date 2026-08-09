# GPIO, timer, PWM and buzzer


def gpio(enabled=1):
    _set_feature("gpio", enabled)
    return True


def setgpio(pin, value):
    import machine
    p = machine.Pin(pin, machine.Pin.OUT)
    p.value(1 if value else 0)
    return True


def readgpio(pin):
    import machine
    p = machine.Pin(pin, machine.Pin.IN, machine.Pin.PULL_DOWN)
    return p.value()


def configuregpio(pin, mode="in", pull="none", initial=0):
    """Configure one GPIO pin using stable beginner-facing names."""
    import machine
    name = str(pin).strip()
    mode_name = str(mode or "in").lower()
    pull_name = str(pull or "none").lower()
    pin_mode = machine.Pin.OUT if mode_name in ("out", "output", "输出") else machine.Pin.IN
    pin_pull = None
    if pull_name in ("up", "pull_up", "上拉"):
        pin_pull = machine.Pin.PULL_UP
    elif pull_name in ("down", "pull_down", "下拉"):
        pin_pull = machine.Pin.PULL_DOWN
    try:
        obj = machine.Pin(name, pin_mode, pin_pull) if pin_pull is not None else machine.Pin(name, pin_mode)
    except TypeError:
        obj = machine.Pin(name, pin_mode)
    if pin_mode == machine.Pin.OUT:
        obj.value(1 if int(initial) else 0)
    _gpio_objects[name] = obj
    return True


def readadc(pin):
    """Read any ADC-capable pin as a 16-bit value."""
    import machine
    name = str(pin).strip()
    adc = _adc_channels.get(name)
    if adc is None:
        adc = machine.ADC(machine.Pin(name))
        _adc_channels[name] = adc
    return adc.read_u16()


def readadcvoltage(pin, reference_voltage=3.3):
    """Read an ADC pin and convert the raw 16-bit result to volts."""
    raw = readadc(pin)
    return raw * float(reference_voltage) / 65535.0


def readadcpercent(pin):
    """Read an ADC pin and convert the raw 16-bit result to 0-100 percent."""
    return readadc(pin) * 100.0 / 65535.0


def readadc_all(pin, reference_voltage=3.3):
    """Return raw ADC, voltage, and percentage in one small dictionary."""
    raw = readadc(pin)
    voltage = raw * float(reference_voltage) / 65535.0
    return {"raw_u16": raw, "voltage": voltage, "percent": raw * 100.0 / 65535.0}


def highpins(pins, *extra_pins):
    """Return the requested pin names that currently read high."""
    import machine
    if extra_pins:
        names = (pins,) + extra_pins
    elif isinstance(pins, str):
        names = tuple(item.strip() for item in pins.split(",") if item.strip())
    else:
        names = tuple(pins or ())
    active = []
    for name in names:
        label = str(name).strip()
        if not label:
            continue
        candidates = (label, label[1:]) if len(label) > 2 and label[0].upper() == "P" else (label,)
        for candidate in candidates:
            try:
                # Do not change the mode of shared LCD pins PF12/PD14.
                if machine.Pin(candidate).value():
                    active.append(label)
                break
            except Exception:
                continue
    return " ".join(active)


def testgpio(out_pin=None, in_pin=None):
    out_pin = out_pin or config.GPIO_LOOP_OUT_PIN
    in_pin = in_pin or config.GPIO_LOOP_IN_PIN
    if not out_pin or not in_pin:
        return _skip("GPIO", "set output/input pins")
    from lib.kit.io_tests import GpioLoopback
    ok, detail = GpioLoopback(out_pin, in_pin).run()
    return _pass("GPIO", detail) if ok else _fail("GPIO", detail)


def timer(enabled=1):
    _set_feature("timer", enabled)
    return True


dingshiqi = timer


def after(ms, func):
    sleep_ms(ms)
    func()
    return True


def every(ms, func, count=5):
    for _ in range(count):
        sleep_ms(ms)
        func()
    return True


def testtimer():
    from lib.kit.io_tests import TimerProbe
    ok, detail = TimerProbe().run()
    return _pass("TIMER", detail) if ok else _fail("TIMER", detail)


def pwm(enabled=1):
    _set_feature("pwm", enabled)
    if not enabled:
        stoppwm()
    return True


def startpwm(pin=None, freq=1000, duty=50):
    global _pwm
    stoppwm()
    pin = pin or config.PWM_OUTPUT_PIN
    if not pin:
        return _skip("PWM", "set PWM output pin")
    from lib.kit.io_tests import PwmOutput
    try:
        _pwm = PwmOutput(pin, freq, duty, timer_id=config.PWM_TIMER_ID, timer_channel=config.PWM_TIMER_CHANNEL)
        _pwm.start()
        return True
    except Exception as exc:
        _pwm = None
        return _fail("PWM", exc)


def stoppwm():
    global _pwm
    if _pwm:
        _pwm.stop()
        _pwm = None
    return True


def readpwm(pin=None, ms=500):
    pin = pin or config.PWM_MEASURE_PIN
    if not pin:
        _skip("PWM", "set PWM measure pin")
        return None
    from lib.kit.io_tests import PulseMeter
    meter = PulseMeter(pin)
    try:
        ok, detail = meter.sample(ms)
        if ok:
            _pass("PWM_READ", detail)
        else:
            _fail("PWM_READ", detail)
        return detail
    finally:
        meter.close()


def testpwm(out_pin=None, measure_pin=None):
    out_pin = out_pin or config.PWM_OUTPUT_PIN
    measure_pin = measure_pin or config.PWM_MEASURE_PIN
    if not out_pin or not measure_pin:
        return _skip("PWM", "set output/measure pins")
    from lib.kit.io_tests import PulseMeter, PwmOutput
    local_pwm = None
    meter = None
    try:
        local_pwm = PwmOutput(out_pin, 1000, 50, timer_id=config.PWM_TIMER_ID, timer_channel=config.PWM_TIMER_CHANNEL)
        mode = local_pwm.start()
        meter = PulseMeter(measure_pin)
        ok, detail = meter.sample(500)
        detail = "mode={} {}".format(mode, detail)
        return _pass("PWM", detail) if ok else _fail("PWM", detail)
    finally:
        if meter:
            meter.close()
        if local_pwm:
            local_pwm.stop()


def fengmingqi(enabled=1):
    _set_feature("buzzer", enabled)
    return True


buzzer = fengmingqi


def beep(ms=300, freq=2000):
    if not config.BUZZER_PIN:
        return _skip("BUZZER", "set BUZZER_PIN")
    from lib.kit.io_tests import Buzzer
    Buzzer(config.BUZZER_PIN, config.BUZZER_ACTIVE).beep(ms, freq)
    return True


def testbuzzer():
    result = beep(300)
    if result is None:
        return None
    return _pass("BUZZER", "beep")


# LCD and SPI


def _ensure_display(report=True):
    global _display
    if not _feature("lcd"):
        if report:
            _skip("LCD", "disabled")
        return None
    if _display is None:
        try:
            from lib.kit.display import CompetitionDisplay
            _display = CompetitionDisplay(
                config.SPI_ID,
                config.SPI_BAUDRATE,
                config.LCD_DC_PIN,
                config.LCD_CS_PIN,
            )
            if _reporter is not None:
                _reporter.display = _display
            _clear_error("lcd")
        except Exception as exc:
            _remember_error("lcd", exc)
            if report:
                _fail("LCD", exc)
            return None
    return _display


def lcd(enabled=1):
    global _display
    _set_feature("lcd", enabled)
    if enabled:
        return _ensure_display() is not None
    _display = None
    if _reporter is not None:
        _reporter.display = None
    return True


def lcdrotation(rotation=1):
    """Official ST7735 set_rotation wrapper."""
    display = _ensure_display()
    if not display:
        return None
    value = max(0, min(3, int(rotation)))
    def operation():
        display.lcd.set_rotation(value)
        display.lcd.flush()
        return True
    return _lcd_draw(operation, "rotation")


def clearlcd():
    global _display, _lcd_row_temp_until
    display = _ensure_display()
    if not display:
        return None
    try:
        display.clear()
        _lcd_row_temp_until = {}
        _clear_error("lcd")
        return True
    except Exception as exc:
        # A drawing/allocation failure does not invalidate the SPI/LCD object.
        # Keeping it lets a later refresh recover after garbage collection.
        _lcd_operation_failed("clear", exc)
        return False


def lcdfillscreen(color="black"):
    """Official fill_screen wrapper using bounded strips."""
    return lcdfill(color)


def lcdflush():
    """Flush the current ST7735 framebuffer."""
    display = _ensure_display()
    if not display:
        return None
    def operation():
        display.lcd.flush()
        return True
    return _lcd_draw(operation, "flush")


def _lcd_xy(row=0, col=0):
    return int(col) * 8, int(row) * 18


def _lcd_clamp(value, lower, upper):
    """Convert a coordinate to an inclusive LCD bound."""
    value = int(value)
    return max(lower, min(value, upper))


def _lcd_is_number(value):
    """Recognize numeric pixel-line arguments without CPython helpers."""
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _lcd_color_value(display, color):
    if isinstance(color, str):
        return getattr(display.lcd, color.strip().upper(), display.lcd.WHITE)
    if color is None:
        return display.lcd.WHITE
    return color


def _lcd_write(text, row=0, col=0, flush=True, color="white"):
    global _display
    display = _ensure_display()
    if not display:
        return None
    row = _lcd_clamp(row, 0, max(0, (display.lcd.HEIGHT - 16) // 18))
    col = _lcd_clamp(col, 0, max(0, (display.lcd.WIDTH - 1) // 8))
    x, y = _lcd_xy(row, col)
    value = str(text)
    # The frozen ST7735 driver rejects an empty string with ValueError.
    # Drawing one blank character preserves the expected "clear this text"
    # behavior and keeps beginner-generated variables safe before assignment.
    if not value:
        value = " "
    max_chars = 20 - int(col)
    if max_chars < 1:
        max_chars = 1
    def operation():
        display.lcd.show_string(
            x, y, value[:max_chars], _lcd_color_value(display, color), display.lcd.BLACK, 16
        )
        if flush:
            display.lcd.flush()
        return True
    try:
        if hasattr(display, "_run_lcd"):
            result = display._run_lcd(operation)
        else:
            result = operation()
        _clear_error("lcd")
        return result
    except Exception as exc:
        _lcd_operation_failed("write", exc)
        return False


def showlcd(text, row=0, col=0):
    return _lcd_write(text, row, col, True)


def showlcdcolor(text, row=0, col=0, color="white"):
    """Show text at a row/column using a named foreground color."""
    return _lcd_write(text, row, col, True, color)


def _lcd_draw(operation, stage="draw"):
    display = _ensure_display()
    if not display:
        return None
    try:
        result = display._run_lcd(operation) if hasattr(display, "_run_lcd") else operation()
        _clear_error("lcd")
        return result
    except Exception as exc:
        _lcd_operation_failed(stage, exc)
        return False


def lcdfill(color="black"):
    """Fill the ST7735 canvas in short strips to bound transfer allocation."""
    display = _ensure_display()
    if not display:
        return None
    value = _lcd_color_value(display, color)
    def operation():
        strip_height = 8
        for top in range(0, display.lcd.HEIGHT, strip_height):
            height = min(strip_height, display.lcd.HEIGHT - top)
            display.lcd.fill_rectangle(0, top, display.lcd.WIDTH, height, value)
        display.lcd.flush()
        return True
    return _lcd_draw(operation, "fill")


def lcdrect(x, y, width, height, color="white", filled=True, thickness=1):
    """Draw a bounded rectangle using the official fill_rectangle primitive."""
    display = _ensure_display()
    if not display:
        return None
    x = _lcd_clamp(x, 0, display.lcd.WIDTH - 1)
    y = _lcd_clamp(y, 0, display.lcd.HEIGHT - 1)
    width = max(1, min(int(width), display.lcd.WIDTH - x))
    height = max(1, min(int(height), display.lcd.HEIGHT - y))
    thickness = max(1, min(int(thickness), min(width, height)))
    value = _lcd_color_value(display, color)
    def operation():
        if filled:
            display.lcd.fill_rectangle(x, y, width, height, value)
        else:
            display.lcd.fill_rectangle(x, y, width, thickness, value)
            display.lcd.fill_rectangle(x, y + height - thickness, width, thickness, value)
            display.lcd.fill_rectangle(x, y, thickness, height, value)
            display.lcd.fill_rectangle(x + width - thickness, y, thickness, height, value)
        display.lcd.flush()
        return True
    return _lcd_draw(operation, "rect")


def _lcd_pixel_line(x1, y1, x2, y2, color="white", thickness=1):
    """Draw a line with integer raster steps and bounded square thickness."""
    display = _ensure_display()
    if not display:
        return None
    value = _lcd_color_value(display, color)
    x1 = _lcd_clamp(x1, 0, display.lcd.WIDTH - 1)
    y1 = _lcd_clamp(y1, 0, display.lcd.HEIGHT - 1)
    x2 = _lcd_clamp(x2, 0, display.lcd.WIDTH - 1)
    y2 = _lcd_clamp(y2, 0, display.lcd.HEIGHT - 1)
    thickness = max(1, min(int(thickness), 8))
    def operation():
        line_x, line_y = x1, y1
        dx, sx = abs(x2 - line_x), 1 if line_x < x2 else -1
        dy, sy = -abs(y2 - line_y), 1 if line_y < y2 else -1
        err = dx + dy
        while True:
            if 0 <= line_x < display.lcd.WIDTH and 0 <= line_y < display.lcd.HEIGHT:
                half = thickness // 2
                left = max(0, min(display.lcd.WIDTH - 1, line_x - half))
                top = max(0, min(display.lcd.HEIGHT - 1, line_y - half))
                draw_width = min(thickness, display.lcd.WIDTH - left)
                draw_height = min(thickness, display.lcd.HEIGHT - top)
                display.lcd.fill_rectangle(left, top, draw_width, draw_height, value)
            if line_x == x2 and line_y == y2:
                break
            twice = 2 * err
            if twice >= dy:
                err += dy
                line_x += sx
            if twice <= dx:
                err += dx
                line_y += sy
        display.lcd.flush()
        return True
    return _lcd_draw(operation, "line")


def lcdcircle(cx, cy, radius, color="white", filled=False):
    """Draw a circle using the confirmed rectangle primitive."""
    display = _ensure_display()
    if not display:
        return None
    value = _lcd_color_value(display, color)
    cx = _lcd_clamp(cx, 0, display.lcd.WIDTH - 1)
    cy = _lcd_clamp(cy, 0, display.lcd.HEIGHT - 1)
    radius = max(1, min(int(radius), max(display.lcd.WIDTH, display.lcd.HEIGHT)))
    def operation():
        x, y, err = radius, 0, 1 - radius
        while x >= y:
            points = ((cx + x, cy + y), (cx + y, cy + x), (cx - y, cy + x), (cx - x, cy + y),
                      (cx - x, cy - y), (cx - y, cy - x), (cx + y, cy - x), (cx + x, cy - y))
            if filled:
                for py in (cy + y, cy - y):
                    left = max(0, cx - x)
                    right = min(display.lcd.WIDTH - 1, cx + x)
                    if 0 <= py < display.lcd.HEIGHT and left <= right:
                        display.lcd.fill_rectangle(left, py, right - left + 1, 1, value)
                for py in (cy + x, cy - x):
                    left = max(0, cx - y)
                    right = min(display.lcd.WIDTH - 1, cx + y)
                    if 0 <= py < display.lcd.HEIGHT and left <= right:
                        display.lcd.fill_rectangle(left, py, right - left + 1, 1, value)
            else:
                for px, py in points:
                    if 0 <= px < display.lcd.WIDTH and 0 <= py < display.lcd.HEIGHT:
                        display.lcd.fill_rectangle(px, py, 1, 1, value)
            y += 1
            if err <= 0:
                err += 2 * y + 1
            else:
                x -= 1
                err += 2 * (y - x) + 1
        display.lcd.flush()
        return True
    return _lcd_draw(operation, "circle")


def lcddrawpoint(x=0, y=0, color="white"):
    """Official draw_point wrapper."""
    display = _ensure_display()
    if not display:
        return None
    x = _lcd_clamp(x, 0, display.lcd.WIDTH - 1)
    y = _lcd_clamp(y, 0, display.lcd.HEIGHT - 1)
    value = _lcd_color_value(display, color)
    def operation():
        display.lcd.fill_rectangle(x, y, 1, 1, value)
        display.lcd.flush()
        return True
    return _lcd_draw(operation, "draw-point")


def lcddrawline(x0=0, y0=0, x1=0, y1=0, color="white"):
    """Official draw_line wrapper with endpoint coordinates."""
    return _lcd_pixel_line(x0, y0, x1, y1, color, 1)


def lcddrawrect(x0=0, y0=0, x1=10, y1=10, color="white"):
    """Official draw_rectangle wrapper using two corner points."""
    left = min(int(x0), int(x1))
    top = min(int(y0), int(y1))
    width = abs(int(x1) - int(x0)) + 1
    height = abs(int(y1) - int(y0)) + 1
    return lcdrect(left, top, width, height, color, False, 1)


def lcdfillrect(x=0, y=0, width=10, height=10, color="white"):
    """Official fill_rectangle wrapper."""
    return lcdrect(x, y, width, height, color, True, 1)


def lcdshowstring(x=0, y=0, text="Hello", color="white", background="black", size=16):
    """Official pixel-coordinate show_string wrapper."""
    display = _ensure_display()
    if not display:
        return None
    x = _lcd_clamp(x, 0, display.lcd.WIDTH - 1)
    y = _lcd_clamp(y, 0, display.lcd.HEIGHT - 1)
    size = max(8, min(24, int(size)))
    value = str(text) or " "
    fg = _lcd_color_value(display, color)
    bg = _lcd_color_value(display, background)
    def operation():
        display.lcd.show_string(x, y, value, fg, bg, size)
        display.lcd.flush()
        return True
    return _lcd_draw(operation, "show-string")


def lcdcolor565(red=0, green=0, blue=0):
    """Convert RGB888 components to the official RGB565 integer."""
    red = max(0, min(255, int(red)))
    green = max(0, min(255, int(green)))
    blue = max(0, min(255, int(blue)))
    return ((red & 0xF8) << 8) | ((green & 0xFC) << 3) | (blue >> 3)


def testlcdofficial():
    """Run a bounded official-API showcase and leave the result on LCD."""
    display = _ensure_display()
    if not display:
        return False
    try:
        lcdfillscreen("black")
        lcdrotation(3)
        lcdshowstring(4, 4, "LCD API", "cyan", "black", 16)
        lcddrawpoint(2, 28, "white")
        lcddrawline(4, 32, 40, 52, "green")
        lcddrawrect(48, 28, 96, 58, "yellow")
        lcdfillrect(104, 32, 40, 24, "blue")
        lcdcircle(80, 92, 20, "red", False)
        lcdflush()
        return _pass("LCD_API", "official primitives")
    except Exception as exc:
        return _fail("LCD_API", exc)


def lcdimage(path, x=0, y=0, width=40, height=40):
    """Draw an RGB565 raw image stored through the Quectel File API."""
    if not _feature("lcd"):
        return _skip("LCD_IMAGE", "LCD disabled")
    if not _feature("storage"):
        return _skip("LCD_IMAGE", "storage disabled")
    display = _ensure_display()
    if not display:
        return None
    try:
        x = _lcd_clamp(x, 0, display.lcd.WIDTH - 1)
        y = _lcd_clamp(y, 0, display.lcd.HEIGHT - 1)
        width = max(1, min(int(width), display.lcd.WIDTH - x))
        height = max(1, min(int(height), display.lcd.HEIGHT - y))
        expected = width * height * 2
        if expected > 40960:
            raise ValueError("image frame exceeds 40 KiB")
        from quectel import File
        sleep_ms(250)
        with File.open(_file_target(path), "r") as fp:
            data = fp.read(expected)
        if isinstance(data, str):
            data = data.encode()
        elif not isinstance(data, (bytes, bytearray)):
            data = bytes(data)
        if len(data) < expected:
            raise ValueError("RGB565 file too short: {} < {} bytes".format(len(data), expected))
        payload = bytearray(data[:expected])
        def operation():
            display.lcd.show_image(x, y, width, height, payload)
            display.lcd.flush()
            return True
        result = _lcd_draw(operation, "image")
        if result:
            print("[LCD][IMAGE] {} {}x{} at {},{}".format(_file_target(path), width, height, x, y))
        return result
    except Exception as exc:
        _remember_error("lcd", exc)
        print("[LCD][IMAGE][FAIL] {}".format(repr(exc)))
        return False


def clearlcdline(row):
    """Clear one 18-pixel text row without disturbing other rows."""
    display = _ensure_display()
    if not display:
        return None
    row = _lcd_clamp(row, 0, max(0, (display.lcd.HEIGHT - 18) // 18))
    y = row * 18

    def operation():
        display.lcd.fill_rectangle(0, y, display.lcd.WIDTH, 18, display.lcd.BLACK)
        display.lcd.flush()
        return True

    try:
        result = display._run_lcd(operation) if hasattr(display, "_run_lcd") else operation()
        _lcd_row_temp_until.pop(row, None)
        _clear_error("lcd")
        return result
    except Exception as exc:
        _lcd_operation_failed("clear-line", exc)
        return False


def showlcdrowtemp(text, ms=5000, row=0, col=0, color="white"):
    """Show a non-blocking temporary message on one LCD row."""
    row = int(row)
    clearlcdline(row)
    result = showlcdcolor(text, row, col, color)
    if result:
        _lcd_row_temp_until[row] = ticks_ms() + max(0, int(ms))
    return result


def updatelcdtemp():
    """Expire temporary LCD rows; call this from the fast polling loop."""
    now = ticks_ms()
    for row, deadline in tuple(_lcd_row_temp_until.items()):
        if ticks_diff(now, deadline) >= 0:
            clearlcdline(row)
    return bool(_lcd_row_temp_until)


def lcdrowtempactive(row=0):
    """Return whether a temporary message currently owns one LCD row."""
    row = int(row)
    deadline = _lcd_row_temp_until.get(row)
    if deadline is None:
        return False
    if ticks_diff(ticks_ms(), deadline) >= 0:
        clearlcdline(row)
        return False
    return True


def showlcdtemp(text, ms=10000, row=0, col=0):
    """Show a wrapped temporary LCD message without blocking the main loop."""
    global _lcd_temp_active, _lcd_temp_until
    duration = max(0, int(ms))
    clearlcd()
    value = str(text)
    width = max(1, 20 - int(col))
    chunks = []
    for source_line in value.split("\n"):
        if not source_line:
            chunks.append("")
            continue
        for offset in range(0, len(source_line), width):
            chunks.append(source_line[offset:offset + width])
    result = True
    for line_index, chunk in enumerate(chunks or [""]):
        if not showlcd(chunk, int(row) + line_index, col):
            result = False
            break
    if result:
        _lcd_temp_active = True
        _lcd_temp_until = ticks_ms() + duration
    return result


def lcdtempactive():
    """Return True while a temporary LCD message is active; clear it on expiry."""
    global _lcd_temp_active
    if not _lcd_temp_active:
        return False
    if ticks_diff(ticks_ms(), _lcd_temp_until) >= 0:
        _lcd_temp_active = False
        clearlcd()
        return False
    return True


def setpwmduty(duty):
    """Update the active PWM duty cycle without rebuilding the PWM object."""
    if _pwm is None:
        return False
    try:
        return bool(_pwm.set_duty(duty))
    except Exception as exc:
        return _fail("PWM", exc)


def readpwmduty():
    """Return the active PWM duty cycle, or None when PWM is stopped."""
    if _pwm is None:
        return None
    return getattr(_pwm, "duty_percent", None)


def lcdtext(text, row=0, col=0, color="white"):
    return showlcdcolor(text, row, col, color)


def lcdline(*args):
    """Legacy row text call or pixel line call from the LCD designer."""
    if len(args) >= 4 and all(_lcd_is_number(value) for value in args[:4]):
        return _lcd_pixel_line(args[0], args[1], args[2], args[3], args[4] if len(args) > 4 else "white", args[5] if len(args) > 5 else 1)
    row = args[0] if args else 0
    text = args[1] if len(args) > 1 else ""
    col = args[2] if len(args) > 2 else 0
    color = args[3] if len(args) > 3 else "white"
    return showlcdcolor(text, row, col, color)


def lcdclear():
    return clearlcd()


def lcdvalue(name, value, row=0, col=0):
    return showlcd("{}: {}".format(name, value), row, col)


def showtest(name, status, detail=""):
    display = _ensure_display()
    if not display:
        return None
    display.show_test(name, status, detail)
    return True


def lcdpass(name, detail=""):
    return showtest(name, "PASS", detail)


def lcdfail(name, detail=""):
    return showtest(name, "FAIL", detail)


def lcdskip(name, detail=""):
    return showtest(name, "SKIP", detail)


def showguangmin(row=0, col=0):
    data = readguangmin_all()
    if not data:
        return False
    return showlcd("Light {:.1f}%".format(data["percent"]), row, col)


def showwenhumi(row=0, col=0):
    data = readwenhumi()
    if not data:
        return False
    display = _ensure_display()
    if not display:
        return None
    _lcd_write("Temp {:.1f}C".format(data[0]), row, col, False)
    _lcd_write("Humi {:.1f}%".format(data[1]), row + 1, col, False)
    display.lcd.flush()
    return True


def showjiasudu(row=0, col=0):
    data = readjiasudu()
    if not data:
        return False
    display = _ensure_display()
    if not display:
        return None
    _lcd_write("X {}".format(data[0]), row, col, False)
    _lcd_write("Y {}".format(data[1]), row + 1, col, False)
    _lcd_write("Z {}".format(data[2]), row + 2, col, False)
    display.lcd.flush()
    return True


def showi2c(row=0, col=0):
    addresses = scani2c()
    if addresses is None:
        return False
    return showlcd(",".join(hex(x) for x in addresses), row, col)


def showstatus(row=0, col=0):
    data = status()
    showlcd("PASS ready", row, col)
    return data


def testlcd():
    display = _ensure_display()
    if not display:
        return False
    display.show_test("LCD", "PASS", "display ready")
    return _pass("LCD", "display ready")


def spi(enabled=1):
    _set_feature("spi_loopback", enabled)
    return True


def sendspi(data=b"test"):
    global _display
    import machine
    if not _feature("spi_loopback"):
        return None
    payload = _payload(data)
    spi_bus = machine.SPI(config.SPI_ID, baudrate=config.SPI_LOOPBACK_BAUDRATE, polarity=0, phase=0)
    received = bytearray(len(payload))
    try:
        spi_bus.write_readinto(payload, received)
        return bytes(received)
    finally:
        deinit = getattr(spi_bus, "deinit", None)
        if deinit:
            deinit()
        if _feature("lcd"):
            _drop_report_display()


def configurespi(bus_id=1, baudrate=1000000, polarity=0, phase=0, sck=None, mosi=None, miso=None):
    """Configure an SPI bus, optionally overriding its pins."""
    import machine
    bus_id = int(bus_id)
    kwargs = {"baudrate": int(baudrate), "polarity": int(polarity), "phase": int(phase)}
    if sck:
        kwargs["sck"] = machine.Pin(str(sck))
    if mosi:
        kwargs["mosi"] = machine.Pin(str(mosi))
    if miso:
        kwargs["miso"] = machine.Pin(str(miso))
    try:
        bus = machine.SPI(bus_id, **kwargs)
    except Exception:
        bus = machine.SPI(bus_id, baudrate=int(baudrate), polarity=int(polarity), phase=int(phase))
    _spi_custom_buses[bus_id] = bus
    return True


def testspi(data=b"QUECTEL-SPI"):
    from lib.kit.io_tests import SpiLoopback
    payload = _payload(data)
    ok, detail = SpiLoopback(config.SPI_ID, config.SPI_LOOPBACK_BAUDRATE).run(payload)
    if _feature("lcd"):
        _drop_report_display()
    return _pass("SPI", detail) if ok else _fail("SPI", detail)


