# -*- coding: utf-8 -*-
print("[BOOT] minimal diagnostic loaded")

try:
    import easy_api as api
    print("[BOOT] easy_api imported")
except Exception as exc:
    print("[BOOT][FAIL] easy_api import: {}".format(repr(exc)))
    raise

try:
    init_ok = api.init()
    print("[BOOT] api.init={}".format(init_ok))
    lcd_ok = api.lcd(1)
    print("[BOOT] api.lcd={}".format(lcd_ok))
    api.lcdfill("black")
    api.showlcdcolor("UniKnect OK", 1, 2, "cyan")
    api.showlcdcolor("main.py running", 3, 1, "white")
    api.lcdrect(4, 82, 152, 34, "green", False)
    print("[BOOT][PASS] LCD diagnostic rendered")
except Exception as exc:
    print("[BOOT][FAIL] LCD: {}".format(repr(exc)))
    raise

while True:
    api.delay(1000)
