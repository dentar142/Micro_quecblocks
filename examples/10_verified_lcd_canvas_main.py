# -*- coding: utf-8 -*-
import easy_api as api
print("[BOOT] main.py loaded")

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
        api.showlcdcolor("ABCDE", 0, 1, "cyan")
    except Exception as _lcd_canvas_error:
        print("[LCD] canvas element skipped:", _lcd_canvas_error)
    try:
        api.lcdrect(4, 30, 152, 28, "blue", False, 1)
    except Exception as _lcd_canvas_error:
        print("[LCD] canvas element skipped:", _lcd_canvas_error)
    try:
        api.showlcdcolor("LTE:OK", 2, 1, "white")
    except Exception as _lcd_canvas_error:
        print("[LCD] canvas element skipped:", _lcd_canvas_error)
    try:
        api.lcdrect(20, 80, 80, 24, "green", False, 1)
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
api.led(1)
api.anjian(1)
api.timer(1)
api.guangmin(1)
api.i2c(1)
api.wenhumi(1)
api.jiasudu(1)
api.lcd(1)


def main():
    loop = 0
    sensor_timer = 0
    key_adc_at_press = {}

    # LCD 设计画布：变量初始化后绘制，避免变量文字在启动阶段未定义
    _draw_lcd_canvas()
    print("[BOOT] LCD scene rendered")

    while DISPLAY_CYCLES is None or loop < DISPLAY_CYCLES:
        key_event = api.readanjian()
        if key_event and key_event[0] == "center" and key_event[1] == "press":
            api.setled("red", 1)
        sensor_timer += BUTTON_POLL_MS

        if sensor_timer >= SENSOR_REFRESH_MS:
            sensor_timer = 0
            loop += 1
            light_value = api.readguangmin()
            light_value_text = api.baoliuxiaoshu(light_value, 2)
            wendu = api.readwendu()
            wendu_text = api.baoliuxiaoshu(wendu, 2)
            shidu = api.readshidu()
            shidu_text = api.baoliuxiaoshu(shidu, 2)
            x = api.readx()
            x_text = api.baoliuxiaoshu(x, 2)
            y = api.readyaxis()
            y_text = api.baoliuxiaoshu(y, 2)
            z = api.readz()
            z_text = api.baoliuxiaoshu(z, 2)
            api.clearlcdline(0)
            api.showlcdcolor("T:", 0, 0, "red")
            api.showlcdcolor(wendu_text, 0, 3, "red")
            api.clearlcdline(1)
            api.showlcdcolor("H:", 1, 0, "blue")
            api.showlcdcolor(shidu_text, 1, 3, "blue")
            api.clearlcdline(2)
            api.showlcdcolor("L:", 2, 0, "white")
            api.showlcdcolor(light_value_text, 2, 3, "white")
            # LCD 画布元素叠加在主程序 LCD 内容之后
            _draw_lcd_canvas(False)

        api.delay(BUTTON_POLL_MS)


if __name__ == "__main__":
    main()
