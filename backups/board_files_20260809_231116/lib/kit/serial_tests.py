"""UART、TTL、RS232 和 RS485 测试封装。"""

from .compat import sleep_ms


class UartPort:
    def __init__(self, uart_id=2, baudrate=115200, timeout=1000, machine_module=None):
        if machine_module is None:
            import machine as machine_module
        self.uart = machine_module.UART(uart_id, baudrate, timeout=timeout)

    def write(self, payload):
        return self.uart.write(payload)

    def read_available(self):
        count = self.uart.any()
        if count:
            return self.uart.read(count)
        return b""

    def loopback(self, payload=b"QUECTEL-UART", wait_ms=200):
        self.write(payload)
        sleep_ms(wait_ms)
        data = self.read_available()
        return data == payload, "sent={} recv={}".format(payload, data)


class Rs485Port(UartPort):
    def __init__(self, uart_id=2, baudrate=115200, timeout=1000,
                 direction_pin=None, machine_module=None):
        super().__init__(uart_id, baudrate, timeout, machine_module)
        self.direction = None
        if direction_pin:
            if machine_module is None:
                import machine as machine_module
            self.direction = machine_module.Pin(direction_pin, machine_module.Pin.OUT, value=0)

    def set_tx(self, enabled):
        if self.direction:
            self.direction.value(1 if enabled else 0)

    def loopback(self, payload=b"QUECTEL-RS485", wait_ms=250):
        self.set_tx(True)
        self.write(payload)
        sleep_ms(20)
        self.set_tx(False)
        sleep_ms(wait_ms)
        data = self.read_available()
        return data == payload, "sent={} recv={}".format(payload, data)

