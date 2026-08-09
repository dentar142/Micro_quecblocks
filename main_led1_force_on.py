# -*- coding: utf-8 -*-
"""LED1 hardware path diagnostic for UniKnect EC200U / NUCLEO-F413ZH."""

import easy_api as api

print("[LED1] force-on diagnostic")
api.init()
api.led(1)

# Bypass the animation and PWM layers: LED1 is PB0 and high-active.
try:
    import machine
    pin = machine.Pin("B0", machine.Pin.OUT, value=1)
    print("[LED1] B0 high:", pin.value())
except Exception as exc:
    print("[LED1] machine B0 failed:", repr(exc))
    try:
        import pyb
        pin = pyb.Pin("B0", pyb.Pin.OUT_PP)
        pin.high()
        print("[LED1] pyb B0 high:", pin.value())
    except Exception as pyb_exc:
        print("[LED1] pyb B0 failed:", repr(pyb_exc))

while True:
    api.delay(1000)
