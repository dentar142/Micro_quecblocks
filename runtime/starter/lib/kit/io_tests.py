"""GPIO、定时器、PWM、蜂鸣器和回环测试工具。"""

from .compat import sleep_ms, ticks_ms, ticks_us, ticks_diff


def require_pin(name, value):
    if not value:
        return "{} not configured".format(name)
    return None


class GpioLoopback:
    def __init__(self, out_pin, in_pin, machine_module=None):
        if machine_module is None:
            import machine as machine_module
        self.machine = machine_module
        self.out = self.machine.Pin(out_pin, self.machine.Pin.OUT, value=0)
        self.input = self.machine.Pin(in_pin, self.machine.Pin.IN, self.machine.Pin.PULL_DOWN)

    def run(self):
        self.out.value(0)
        sleep_ms(20)
        low = self.input.value()
        self.out.value(1)
        sleep_ms(20)
        high = self.input.value()
        self.out.value(0)
        return low == 0 and high == 1, "low={} high={}".format(low, high)


class TimerProbe:
    def __init__(self, interval_ms=100, loops=5):
        self.interval_ms = interval_ms
        self.loops = loops

    def run(self):
        try:
            import machine
            timer = machine.Timer(-1)
            count = {"value": 0}
            def cb(_):
                count["value"] += 1
            timer.init(period=self.interval_ms, mode=machine.Timer.PERIODIC, callback=cb)
            sleep_ms(self.interval_ms * self.loops + 80)
            timer.deinit()
            ok = self.loops - 1 <= count["value"] <= self.loops + 2
            return ok, "machine.Timer count={}".format(count["value"])
        except Exception as machine_exc:
            try:
                import pyb
                count = {"value": 0}
                timer = pyb.Timer(4, freq=max(1, int(1000 / self.interval_ms)))
                def cb(_):
                    count["value"] += 1
                timer.callback(cb)
                sleep_ms(self.interval_ms * self.loops + 80)
                timer.callback(None)
                timer.deinit()
                ok = self.loops - 1 <= count["value"] <= self.loops + 2
                return ok, "pyb.Timer count={}".format(count["value"])
            except Exception as pyb_exc:
                return False, "machine={} pyb={}".format(machine_exc, pyb_exc)


class PwmOutput:
    def __init__(self, pin_name, frequency=1000, duty_percent=50, machine_module=None,
                 timer_id=3, timer_channel=1, prefer_pyb=False):
        self.pin_name = pin_name
        self.frequency = frequency
        self.duty_percent = duty_percent
        self.machine = machine_module
        self.timer_id = timer_id
        self.timer_channel = timer_channel
        self.prefer_pyb = bool(prefer_pyb)
        self.impl = None

    def _pwm_channel(self):
        text = str(self.pin_name).upper()
        digits = "".join(ch for ch in text if ch.isdigit())
        if digits:
            return int(digits)
        try:
            return int(self.pin_name)
        except Exception:
            return None

    def start(self):
        machine_exc = RuntimeError("machine.PWM skipped for verified pyb.Timer mapping")
        if not self.prefer_pyb:
            self.stop()
            try:
                if self.machine is None:
                    import machine as machine_module
                else:
                    machine_module = self.machine
                pin = machine_module.Pin(self.pin_name)
                pwm = machine_module.PWM(pin)
                self.impl = pwm
                if hasattr(pwm, "freq"):
                    pwm.freq(self.frequency)
                if hasattr(pwm, "duty_u16"):
                    pwm.duty_u16(int(65535 * self.duty_percent / 100))
                elif hasattr(pwm, "duty"):
                    pwm.duty(int(1023 * self.duty_percent / 100))
                return "machine.PWM"
            except Exception as exc:
                machine_exc = exc
                self.stop()
        try:
            import pyb
            pin = pyb.Pin(self.pin_name)
            timer = pyb.Timer(self.timer_id, freq=self.frequency)
            try:
                channel = timer.channel(self.timer_channel, pyb.Timer.PWM, pin=pin)
                channel.pulse_width_percent(self.duty_percent)
                self.impl = (timer, channel)
                return "pyb.Timer.PWM"
            except Exception:
                timer.deinit()
                raise
        except Exception as pyb_timer_exc:
            try:
                import pyb
                channel = self._pwm_channel()
                if channel is None:
                    raise ValueError("no numeric PWM channel in {}".format(self.pin_name))
                duty = max(0, min(100, int(self.duty_percent)))
                pyb.pwm(channel, duty)
                self.impl = ("pyb.pwm", channel)
                return "pyb.pwm"
            except Exception as pyb_pwm_exc:
                raise RuntimeError(
                    "PWM unavailable: machine={} pyb_timer={} pyb_pwm={}".format(
                        machine_exc, pyb_timer_exc, pyb_pwm_exc
                    )
                )

    def set_duty(self, duty_percent):
        duty = max(0, min(100, float(duty_percent)))
        self.duty_percent = duty
        if self.impl is None:
            return False
        if isinstance(self.impl, tuple):
            if self.impl[0] == "pyb.pwm":
                import pyb
                pyb.pwm(self.impl[1], int(duty))
            else:
                self.impl[1].pulse_width_percent(duty)
        elif hasattr(self.impl, "duty_u16"):
            self.impl.duty_u16(int(65535 * duty / 100))
        elif hasattr(self.impl, "duty"):
            self.impl.duty(int(1023 * duty / 100))
        else:
            return False
        return True

    def stop(self):
        if self.impl is None:
            return
        try:
            if isinstance(self.impl, tuple):
                if self.impl[0] == "pyb.pwm":
                    try:
                        import pyb
                        pyb.pwm(self.impl[1], 0)
                    except Exception:
                        pass
                else:
                    self.impl[0].deinit()
            else:
                self.impl.deinit()
        finally:
            self.impl = None


class EdgeCounter:
    def __init__(self, pin_name, machine_module=None):
        if machine_module is None:
            import machine as machine_module
        self.count = 0
        self.pin = machine_module.Pin(pin_name, machine_module.Pin.IN, machine_module.Pin.PULL_DOWN)
        self.pin.irq(trigger=machine_module.Pin.IRQ_RISING, handler=self._handler)

    def _handler(self, _pin):
        self.count += 1

    def sample(self, ms=500):
        self.count = 0
        start = ticks_ms()
        sleep_ms(ms)
        elapsed = ticks_diff(ticks_ms(), start)
        return self.count, elapsed


class PulseMeter:
    def __init__(self, pin_name, machine_module=None, max_edges=80):
        if machine_module is None:
            import machine as machine_module
        self.machine = machine_module
        try:
            from array import array
            self.times = array("I", [0] * max_edges)
        except Exception:  # pragma: no cover - fallback for unusual ports
            self.times = [0] * max_edges
        self.levels = bytearray(max_edges)
        self.max_edges = max_edges
        self.count = 0
        self.pin = self.machine.Pin(pin_name, self.machine.Pin.IN, self.machine.Pin.PULL_DOWN)
        self.trigger = self.machine.Pin.IRQ_RISING | self.machine.Pin.IRQ_FALLING

    def _handler(self, pin):
        index = self.count
        if index < self.max_edges:
            self.times[index] = ticks_us()
            self.levels[index] = pin.value()
            self.count = index + 1

    def close(self):
        try:
            self.pin.irq(handler=None)
        except Exception:
            pass

    def sample(self, ms=500):
        self.count = 0
        self.pin.irq(trigger=self.trigger, handler=self._handler)
        try:
            sleep_ms(ms)
        finally:
            self.close()
        edge_count = min(self.count, self.max_edges)
        if edge_count < 4:
            return False, "edges={}".format(edge_count)
        periods = []
        high_times = []
        last_rising = None
        for i in range(edge_count):
            current_t = self.times[i]
            current_level = self.levels[i]
            if current_level == 1:
                if last_rising is not None:
                    periods.append(ticks_diff(current_t, last_rising))
                last_rising = current_t
            if i > 0 and self.levels[i - 1] == 1:
                high_times.append(ticks_diff(current_t, self.times[i - 1]))
        if not periods or not high_times:
            return False, "edges={} insufficient_periods".format(edge_count)
        avg_period = sum(periods) / len(periods)
        avg_high = sum(high_times) / len(high_times)
        frequency = 1000000.0 / avg_period if avg_period else 0
        duty = avg_high * 100.0 / avg_period if avg_period else 0
        ok = 900 <= frequency <= 1100 and 40 <= duty <= 60
        return ok, "freq={:.1f}Hz duty={:.1f}% edges={}".format(frequency, duty, edge_count)


class SpiLoopback:
    def __init__(self, spi_id=1, baudrate=1000000, machine_module=None):
        if machine_module is None:
            import machine as machine_module
        self.spi = machine_module.SPI(spi_id, baudrate=baudrate, polarity=0, phase=0)

    def run(self, payload=b"QUECTEL-SPI"):
        received = bytearray(len(payload))
        try:
            self.spi.write_readinto(payload, received)
            data = bytes(received)
            return data == payload, "sent={} recv={}".format(payload, data)
        finally:
            deinit = getattr(self.spi, "deinit", None)
            if deinit:
                deinit()


class Buzzer:
    def __init__(self, pin_name, active=True):
        self.pin_name = pin_name
        self.active = active

    def beep(self, duration_ms=300, frequency=2000):
        if self.active:
            import machine
            pin = machine.Pin(self.pin_name, machine.Pin.OUT, value=1)
            sleep_ms(duration_ms)
            pin.value(0)
            return "active_gpio"
        pwm = PwmOutput(self.pin_name, frequency, 50)
        mode = pwm.start()
        sleep_ms(duration_ms)
        pwm.stop()
        return mode

