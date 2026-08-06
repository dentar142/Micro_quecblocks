# -*- coding: utf-8 -*-
import easy_api as api

# 参数设置
DISPLAY_CYCLES = None
BUTTON_POLL_MS = 20
SENSOR_REFRESH_MS = 500
UART_ID = 2                 # fixed UART2 / USART_B, PC COM43
UART_BAUDRATE = 115200
UART_TIMEOUT_MS = 1000

# 启用或关闭模块
api.init()                 # initialize easy_api
api.anjian(1)
api.guangmin(1)
api.wenhumi(1)
api.lcd(1)
api.uart(1)
api.ble(1, "server", "Uniknect_BLE_DEMO")
api.cunchu(1)
api.yinpin(1)
api.setuart(UART_ID, UART_BAUDRATE, UART_TIMEOUT_MS)


def main():
    loop = 0
    sensor_timer = 0
    key_adc_at_press = {}
    light_percent = 0
    light_text = ""
    wendu = 0
    wendu_text = ""
    shidu = 0
    shidu_text = ""
    key_event = None
    light_records = []
    record_count = 0
    dark_announced = False
    sorted_values = []
    sorted_text = ""
    saved_text = ""
    saved_message = ""
    sensor_message = ""
    light_line = ""
    temp_line = ""
    humi_line = ""

    while DISPLAY_CYCLES is None or loop < DISPLAY_CYCLES:
        light_percent = api.readguangmin_percent()
        key_event = api.readanjian()
        api.updateaudio()
        uart_received_text = api.readuarttext()
        if uart_received_text is not None:
            uart_lcd_message = api.pin_jie("UART:", uart_received_text, "", "", "", "")
            api.showlcdtemp(uart_lcd_message, 10000, 0, 0)
        ble_received_text = api.readbledata()
        if ble_received_text is not None:
            ble_lcd_message = api.pin_jie("BLE:", ble_received_text, "", "", "", "")
            api.showlcdtemp(ble_lcd_message, 10000, 0, 0)
        if key_event and key_event[0] == "user" and key_event[1] == "press":
            light_records.append(light_percent)
            record_count += 1
            if record_count >= 10:
                sorted_values = api.shuzipaixu(light_records, False)
                sorted_text = api.pin_jie("", sorted_values, "", "", "", "")
                api.writefile("SD:light_sorted.txt", sorted_text)
                record_count = 0
                light_records = []
        if key_event and key_event[0] == "center" and key_event[1] == "press":
            saved_text = api.readfile("SD:light_sorted.txt", 1024)
            saved_message = api.pin_jie("SORTED:", saved_text, "", "", "", "")
            api.senduart(saved_message)
            api.senduart("\r\n")
            api.sendble(saved_message)
            api.showlcdtemp(saved_message, 10000, 0, 0)
        if key_event and key_event[0] in ("left", "right") and key_event[1] == "press":
            api.recordtimed("SD:light_record.wav", 10000)
        if key_event and key_event[0] in ("up", "down") and key_event[1] == "press":
            api.playfile("SD:light_record.wav", False)
        sensor_timer += BUTTON_POLL_MS

        if sensor_timer >= SENSOR_REFRESH_MS:
            sensor_timer = 0
            loop += 1
            wendu = api.readwendu()
            shidu = api.readshidu()
            light_text = api.baoliuxiaoshu(light_percent, 2)
            wendu_text = api.baoliuxiaoshu(wendu, 2)
            shidu_text = api.baoliuxiaoshu(shidu, 2)
            sensor_message = api.pin_jie("Light:", light_text, "% T:", wendu_text, " H:", shidu_text)
            api.senduart(sensor_message)
            api.senduart("\r\n")
            api.sendble(sensor_message)
            if light_percent > 50:
                if dark_announced == False:
                    api.tts("光线暗", False)
                    dark_announced = True
            if light_percent <= 50:
                dark_announced = False
            light_line = api.pin_jie("Light:", light_text, "%", "", "", "")
            temp_line = api.pin_jie("Temp:", wendu_text, " C", "", "", "")
            humi_line = api.pin_jie("Humi:", shidu_text, "%", "", "", "")
            if not api.lcdtempactive():
                api.clearlcd()
                api.showlcd(light_line, 0, 0)
                api.showlcd(temp_line, 1, 0)
                api.showlcd(humi_line, 2, 0)

        api.delay(BUTTON_POLL_MS)


if __name__ == "__main__":
    main()
