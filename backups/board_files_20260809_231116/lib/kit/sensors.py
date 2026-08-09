"""板载 ADC、AHT20 和 LIS2DH12 传感器封装。"""


class LightSensor:
    def __init__(self, pin_name="C5", machine_module=None, reference_voltage=3.3):
        if machine_module is None:
            import machine as machine_module
        self.adc = machine_module.ADC(machine_module.Pin(pin_name))
        self.reference_voltage = reference_voltage

    def read(self):
        raw = self.adc.read_u16()
        return {
            "raw_u16": raw,
            "voltage": raw * self.reference_voltage / 65535.0,
            "percent": raw * 100.0 / 65535.0,
        }


class I2CBus:
    def __init__(self, bus_id=1, freq=400000, machine_module=None):
        if machine_module is None:
            import machine as machine_module
        self.bus = machine_module.I2C(bus_id, freq=freq)

    def scan(self):
        return self.bus.scan()


class ClimateSensor:
    def __init__(self, i2c):
        from ahtx0 import AHT20
        self.sensor = AHT20(i2c)

    def read(self):
        return {
            "temperature_c": self.sensor.temperature,
            "humidity_percent": self.sensor.relative_humidity,
        }


class MotionSensor:
    def __init__(self, i2c):
        from lis2dh12 import LIS2DH12
        self.sensor = LIS2DH12(i2c)

    def read(self):
        x, y, z = self.sensor.acceleration
        return {"x": x, "y": y, "z": z}


class SensorSuite:
    def __init__(self, config, machine_module=None):
        self.devices = {}
        self.errors = {}
        features = config.FEATURES
        if features.get("adc"):
            self._add("light", lambda: LightSensor(config.LIGHT_ADC_PIN, machine_module))
        if features.get("i2c"):
            try:
                bus = I2CBus(config.I2C_ID, config.I2C_FREQ, machine_module)
                self.devices["i2c"] = bus
                self._add("climate", lambda: ClimateSensor(bus.bus))
                self._add("motion", lambda: MotionSensor(bus.bus))
            except Exception as exc:
                self.errors["i2c"] = str(exc)

    def _add(self, name, factory):
        try:
            self.devices[name] = factory()
        except Exception as exc:
            self.errors[name] = str(exc)

    def snapshot(self):
        data = {}
        for name, device in self.devices.items():
            if name == "i2c":
                try:
                    data[name] = {"addresses": device.scan()}
                except Exception as exc:
                    self.errors[name] = str(exc)
                continue
            try:
                data[name] = device.read()
            except Exception as exc:
                self.errors[name] = str(exc)
        return {"sensors": data, "errors": dict(self.errors)}

