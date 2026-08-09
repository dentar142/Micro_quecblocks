# -*- coding: utf-8 -*-
"""UniKnect EC200U LED1 呼吸灯最小示例。

LED1: PB0, green, active high, hardware PWM.
Upload this file to the board as main.py with Thonny.
"""

import easy_api as api

print("[BOOT] LED1 breathe demo")

required = ("init", "led", "ledbreathe", "updateled", "ledoff")
missing = [name for name in required if not hasattr(api, name)]
if missing:
    raise RuntimeError(
        "easy_api runtime is outdated; missing: " + ", ".join(missing)
    )


def main():
    api.init()
    if not api.led(1):
        raise RuntimeError("LED module initialization failed")

    # Start once. updateled() advances the non-blocking animation.
    if not api.ledbreathe("green", 2000, 0, 100, 32):
        raise RuntimeError("LED1 PWM breathe setup failed")

    try:
        while True:
            api.updateled()
            api.delay(20)
    except KeyboardInterrupt:
        api.ledoff()
        print("[BOOT] LED1 breathe stopped")


if __name__ == "__main__":
    main()
