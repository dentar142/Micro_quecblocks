"""Fast beginner-friendly API for the offline competition kit.

The implementation is split into small source parts so memory-constrained
MicroPython boards never parse the former 64 KB module in one pass. All parts
execute in this module namespace, preserving the public api.xxx surface and
shared lazy hardware state.
"""

import gc


try:
    _api_file = __file__.replace("\\", "/")
    if "/" in _api_file:
        _api_base = _api_file.rsplit("/", 1)[0]
    else:
        _api_base = ""
except Exception:
    _api_base = ""
if _api_base:
    _api_base += "/"


def _load_api_part(name):
    gc.collect()
    path = _api_base + "easy_api_parts/" + name
    try:
        source_file = open(path, "r", encoding="utf-8")
    except TypeError:
        source_file = open(path, "r")
    try:
        source = source_file.read()
    finally:
        source_file.close()
    exec(source, globals())
    del source
    gc.collect()


for _part_name in (
    "00_core.py",
    "10_led_buttons.py",
    "20_sensors.py",
    "30_io_display.py",
    "40_serial.py",
    "50_storage_audio.py",
    "60_radio.py",
    "70_hmi.py",
):
    _load_api_part(_part_name)

del _part_name
del _load_api_part
del _api_base
try:
    del _api_file
except Exception:
    pass
gc.collect()
