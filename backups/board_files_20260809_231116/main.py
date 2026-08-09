# -*- coding: utf-8 -*-
import easy_api as api
print("[BOOT] main.py loaded")

_REQUIRED_EASY_API = ["anjian","cunchu","fengmingqi","gpio","guangmin","i2c","init","jiasudu","lcd","lcdrect","led","lte","pwm","readuarttext","senduart","setuart","showlcdcolor","timer","tts","uart","wenhumi","yinpin"]
_MISSING_EASY_API = [name for name in _REQUIRED_EASY_API if not hasattr(api, name)]
if _MISSING_EASY_API:
    raise RuntimeError("easy_api runtime is outdated; upload the complete runtime/starter before main.py. Missing: " + ", ".join(_MISSING_EASY_API))

def _lte_status_snapshot():
    try:
        raw = api.readlte() or {}
        if not isinstance(raw, dict):
            return {"status": raw}
        result = dict(raw)
        if result.get("sim") is None: result["sim"] = raw.get("query_usim")
        if result.get("status") is None: result["status"] = raw.get("get_status")
        if result.get("status") is None: result["status"] = raw.get("status")
        if result.get("signal") is None: result["signal"] = raw.get("query_signal")
        if result.get("signal") is None: result["signal"] = raw.get("get_signal")
        if result.get("registered") is None: result["registered"] = result.get("status")
        if result.get("attached") is None: result["attached"] = raw.get("is_attached")
        return result
    except Exception as _lte_error:
        print("[LTE] read skipped:", _lte_error)
        return {}

def _draw_lcd_canvas(clear=True):
    if clear:
        try:
            api.lcdfill("black")
        except Exception as _lcd_canvas_error:
            print("[LCD] canvas fill skipped:", _lcd_canvas_error)
    try:
        api.showlcdcolor("UniKnect EC200U", 0, 1, "cyan")
    except Exception as _lcd_canvas_error:
        print("[LCD] canvas element skipped:", _lcd_canvas_error)
    try:
        api.lcdrect(3, 25, 152, 28, "blue", False, 1)
    except Exception as _lcd_canvas_error:
        print("[LCD] canvas element skipped:", _lcd_canvas_error)
    try:
        api.showlcdcolor("LTE:OK", 2, 1, "white")
    except Exception as _lcd_canvas_error:
        print("[LCD] canvas element skipped:", _lcd_canvas_error)
    return True

# 参数设置
DISPLAY_CYCLES = None
BUTTON_POLL_MS = 20
SENSOR_REFRESH_MS = 1000
UART_ID = 2                 # fixed UART2 / USART_B, PC COM43
UART_BAUDRATE = 115200
UART_TIMEOUT_MS = 1000

# 启用或关闭模块
api.init()                 # initialize easy_api
api.cunchu(1)
api.yinpin(1)
api.lcd(1)
api.led(1)
api.pwm(1)
api.anjian(1)
api.gpio(1)
api.timer(1)
api.fengmingqi(1)
api.guangmin(1)
api.i2c(1)
api.wenhumi(1)
api.jiasudu(1)
api.uart(1)
api.lte(1)
api.setuart(UART_ID, UART_BAUDRATE, UART_TIMEOUT_MS)


def main():
    loop = 0
    sensor_timer = 0
    key_adc_at_press = {}

    # LCD 设计画布：变量初始化后绘制，避免变量文字在启动阶段未定义
    _draw_lcd_canvas()
    print("[BOOT] LCD scene rendered")

    while DISPLAY_CYCLES is None or loop < DISPLAY_CYCLES:
        uart_received_text = api.readuarttext()
        if uart_received_text == "LED_ON":
            api.senduart("ON")
            api.tts("开了")
        if uart_received_text == "LED_OFF":
            api.senduart("OFF")
            api.tts("关了")
        api.senduart(uart_received_text)
        sensor_timer += BUTTON_POLL_MS

        if sensor_timer >= SENSOR_REFRESH_MS:
            sensor_timer = 0
            loop += 1
            pass

        api.delay(BUTTON_POLL_MS)


if __name__ == "__main__":
    main()
