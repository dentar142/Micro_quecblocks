# 引脚与杜邦线矩阵

## 已知板载资源

| 功能 | 默认资源 | 说明 |
|---|---|---|
| 光敏电阻 | `C5` / Arduino A5 | ADC 读取环境亮度 |
| AHT20 / LIS2DH12 | `I2C(1)` | S502 必须拨到 MCU 侧 |
| LCD | `SPI(1)`, DC=`F12`, CS=`D14` | ST7735 屏幕 |
| LCD 五向键 | Arduino A3 / 当前固件映射 `C1` | TFT Shield `NAV` 模拟电阻梯形输入；必须在实际板上校准。旧版 `C0/A1` 记录不作为当前映射依据 |
| NUCLEO 用户键 | `SW` | 数字输入，默认下拉 |
| NUCLEO LED | `B0`, `LED_BLUE`, `B14` | 绿/蓝/红；不同固件可能只有 `LED_BLUE` 别名 |
| UART | `UART(2)` | 用于 TTL、RS232、RS485 示例 |

## 现场需配置资源

| 功能 | `config.py` 字段 | 何时填写 |
|---|---|---|
| GPIO 回环 | `GPIO_LOOP_OUT_PIN`, `GPIO_LOOP_IN_PIN` | 裁判给定杜邦线接线后 |
| PWM 输出 | `PWM_OUTPUT_PIN` | 需要测试 PWM 或无源蜂鸣器时 |
| PWM 测量 | `PWM_MEASURE_PIN` | 输出脚通过杜邦线接输入脚时 |
| 蜂鸣器 | `BUZZER_PIN`, `BUZZER_ACTIVE` | 按赛方蜂鸣器示例确认后 |
| RS485 方向控制 | `RS485_DIRECTION_PIN` | 使用半双工 RS485 模块时 |
| RS232 转换器确认 | `FEATURES["rs232"]`, `RS232_TRANSCEIVER_CONFIRMED` | 裁判确认使用 RS232 电平转换后 |
| SPI 回环 | `FEATURES["spi_loopback"]` | MOSI/MISO 杜邦线回环且不冲突时 |

## 禁止或不建议的软件控制

- EC200U `PWRKEY`、`RESET`、`BOOT`。
- NUCLEO `RESET`。
- 电源、SIM、I2C 设备选择等物理拨码开关。
- 任何未经过电平转换的 RS232 线路。
