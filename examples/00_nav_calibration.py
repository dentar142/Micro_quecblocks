"""LCD TFT Shield 五向键 ADC 校准。

在 Thonny 运行后依次松开、按下 LEFT/DOWN/CENTER/RIGHT/UP，
记录串口中的 ADC 原始值，再据此调整 runtime/starter/config.py。
"""

import machine
import utime


ADC_PIN = "C1"
adc = machine.ADC(machine.Pin(ADC_PIN))

print("[NAV] ADC pin = " + ADC_PIN)
print("[NAV] release: do not press any key")
for index in range(20):
    print("[NAV][release] " + str(adc.read_u16()))
    utime.sleep_ms(100)

print("[NAV] press each key for several samples")
while True:
    print("[NAV] raw=" + str(adc.read_u16()))
    utime.sleep_ms(100)
