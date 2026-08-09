"""比赛项目的烧录前配置。

选手应在 Thonny 上传文件前修改本文件。联网、音频录制和外接蜂鸣器等
有额外硬件或副作用的功能默认关闭。
"""

FEATURES = {
    "gpio": True,
    "timer": True,
    "pwm": True,
    "i2c": True,
    "spi": True,
    "adc": True,
    "uart": True,
    "rs232": False,
    "rs485": False,
    "buttons": True,
    "leds": True,
    "buzzer": False,
    "audio": False,
    "storage": True,
    "lcd": True,
    "network": False,
    "lte": False,
    "lbs": False,
    "ble": False,
    "gnss": False,
    "spi_loopback": False,
}

# UniKnect Gen1-PRO + NUCLEO-F413ZH 固定资源。
LIGHT_ADC_PIN = "C5"
USER_BUTTON_PIN = "SW"
LED_PINS = {
    "green": "B0",
    "blue": "LED_BLUE",
    "red": "B14",
}

I2C_ID = 1
I2C_FREQ = 400000
SPI_ID = 1
SPI_BAUDRATE = 10000000
LCD_DC_PIN = "F12"
LCD_CS_PIN = "D14"

# LCD Shield 五向键为模拟电阻梯形输入。
# 实测本套比赛接线使用 Arduino Shield A3；在当前固件命名中对应 C1。
# 不同批次阻值可能存在偏差，先运行 examples/00_nav_calibration.py 校准。
NAV_ADC_PIN = "C1"
NAV_RELEASE_MIN = 60000
NAV_THRESHOLDS = {
    # Arduino 1.8'' TFT Shield schematic:
    # LEFT=R4 22R, DOWN=R2 220R, CENTER=R3 470R,
    # RIGHT=R6 1K, UP=R5 4.7K, release=R7 1K pull-up to 3V3.
    "left": (0, 5000),
    "down": (7000, 16000),
    "center": (17000, 26000),
    "right": (28000, 40000),
    "up": (47000, 59000),
}

# 五向模拟键使用电阻分压，实板松手/按下瞬间会有少量抖动；比赛主程序按稳定事件输出。
BUTTON_DEBOUNCE_MS = 80
BUTTON_LONG_MS = 1800
BUTTON_REPEAT_DELAY_MS = 2200
BUTTON_REPEAT_MS = 300

SENSOR_INTERVAL_MS = 1000
DISPLAY_INTERVAL_MS = 250

# 杜邦线回环引脚必须在实板冲突检查后填写；None 表示裁判程序跳过。
GPIO_LOOP_OUT_PIN = None
GPIO_LOOP_IN_PIN = None
PWM_OUTPUT_PIN = None
PWM_MEASURE_PIN = None
PWM_TIMER_ID = 3
PWM_TIMER_CHANNEL = 1
BUZZER_PIN = None
BUZZER_ACTIVE = False

UART_ID = 2
UART_BAUDRATE = 115200
UART_TIMEOUT_MS = 1000
# True 时，api.senduart(...) 会同时输出到电脑 USB/REPL 串口。
UART_MIRROR_TO_PC = True
RS485_DIRECTION_PIN = None
RS232_TRANSCEIVER_CONFIRMED = False

SPI_LOOPBACK_BAUDRATE = 1000000

# 固件预期已冻结或内置的模块。赛前通过 examples/09_preflight.py 检查。
REQUIRED_FROZEN_MODULES = (
    "machine",
    "st7735",
    "ahtx0",
    "lis2dh12",
    "quectel",
)

AUDIO_RECORD_FILE = "SD:competition_test.wav"
AUDIO_PLAY_FILE = AUDIO_RECORD_FILE
AUDIO_TTS_TEXT = "Quectel test"
AUDIO_VOLUME = 8
AUDIO_TTS_SPEED = None
AUDIO_TTS_PITCH = None
AUDIO_WAIT_TIMEOUT_MS = 8000
STORAGE_TEST_DIR = "competition_test"

# 4G/LTE、BLE、GNSS 默认配置。
BLE_NAME = "Uniknect_BLE_DEMO"
BLE_SERVICE_UUID = 0xFFF0
BLE_CHAR_UUID = 0xFFF1
BLE_CCCD_UUID = 0x2902
BLE_CHAR_MAX_LEN = 32
BLE_RX_QUEUE_MAX = 8
# BLE_MODE 可选：
#   "server"：开发板作为 BLE 外围设备，广播 BLE_NAME，手机/电脑连接它。
#   "client"：开发板作为 BLE 中心设备，扫描并连接目标 BLE_NAME。
BLE_MODE = "server"
BLE_CLIENT_TARGET_NAME = BLE_NAME
# 如果已知目标设备的特征值 value_handle，可填数字；未知时保持 None，
# 先用 scanble/connectble/discoverble 获取 chars 后再写入。
BLE_CLIENT_VALUE_HANDLE = None
# BLE client ?????ACTIVE + ?????????????????
BLE_SCAN_TYPE = "SCAN_ACTIVE"
BLE_SCAN_INTERVAL = 0x60
BLE_SCAN_WINDOW = 0x60
GNSS_TIMEOUT_MS = 15000
LBS_TIMEOUT_MS = 10000
# 通信模块失败后不要每秒重复重试，避免主循环变慢和串口刷屏。
LBS_RETRY_INTERVAL_MS = 30000
BLE_RETRY_INTERVAL_MS = 30000
