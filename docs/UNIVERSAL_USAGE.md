# 通用代码使用说明（高级诊断）

> 这不是当前积木工作台的主操作界面。日常使用请打开 `builder/easy_api_main_builder_microblocks.html`，上传目录为 `runtime/starter/`。下面的 `UniversalKit` 命令仅用于板端自检、回环测试和没有积木覆盖的现场诊断。

这套代码按组委会常见离线考核方式设计：先用杜邦线完成必要回环或外设连接，再在 Thonny 的 REPL 中运行一个统一接口。不要为每道题重写底层驱动，只改 `runtime/starter/config.py`，再调用对应命令。

## 预计题型与对应命令

| 可能题型 | 先做什么 | 运行命令 |
|---|---|---|
| 检查固件/库是否完整 | 上传 `runtime/starter/` 后先测 | `app.run("preflight")` |
| LED、按键、人机交互 | 使用板载 LED、用户键、LCD Shield 五向键 | `app.run("led")`、`app.run("button_led")`、`app.run("hmi")` |
| GPIO 高低电平/杜邦线回环 | 在 `config.py` 填 `GPIO_LOOP_OUT_PIN`、`GPIO_LOOP_IN_PIN`，用杜邦线短接 | `app.run("gpio")` |
| 定时器、PWM、蜂鸣器 | PWM 需把输出脚接到测量脚；蜂鸣器需确认引脚 | `app.run("timer")`、`app.run("pwm")`、`app.run("buzzer")` |
| ADC 光敏电阻 | 确认 `LIGHT_ADC_PIN` | `app.run("adc")` |
| I2C 温湿度/加速度 | 确认 AHT20、LIS2DH12 在 I2C 总线上 | `app.run("i2c")`、`app.run("sensors")` |
| SPI/LCD/SPI 回环 | LCD 用默认 SPI；SPI 回环需 MOSI 接 MISO 并打开 `spi_loopback` | `app.run("spi_lcd")`、`app.run("spi_loopback")` |
| UART/RS232/RS485 | UART TX 接 RX；RS232 必须接真实电平转换器；RS485 填方向控制脚 | `app.run("uart")`、`app.run("rs232")`、`app.run("rs485")` |
| 存储卡、麦克风、扬声器 | 存储卡默认开启；音频需确认模块和权限后打开 `audio` | `app.run("storage")`、`app.run("audio")` |

## 使用步骤

1. 在电脑上打开 `runtime/starter/config.py`。
2. 按实际题目修改功能开关和引脚。例如 GPIO 回环题只需要：

   ```python
   GPIO_LOOP_OUT_PIN = "D2"
   GPIO_LOOP_IN_PIN = "D3"
   ```

3. 用 Thonny 把整个 `runtime/starter/` 目录上传到开发板根目录。
4. 运行 `main.py`。看到 `kit>` 后输入命令，例如：

   ```python
   adc
   i2c
   pwm
   all
   ```

5. 如果不想进交互模式，也可以在 Thonny REPL 手动执行：

   ```python
   from universal_main import UniversalKit
   app = UniversalKit()
   app.help()
   app.run("adc")
   app.run_all()
   ```

## 现场策略

- 不确定题目时先运行 `preflight`，再运行 `all`，看哪些项 PASS、SKIP、FAIL。
- SKIP 通常表示未启用或未配置引脚；先改 `config.py`，不要改驱动库。
- FAIL 表示已经运行但硬件、接线或固件不满足要求；优先检查杜邦线、供电、串口号和外设地址。
- EC200U 的 PWRKEY、RESET、BOOT 等物理控制脚不要默认当成软件可控按钮；只有官方明确给出可控引脚时再配置。
- RS232 不能直接用 STM32 GPIO 对接，必须经过 RS232 电平转换模块。

## 最常用命令速查

```python
from universal_main import UniversalKit
app = UniversalKit()
app.run("preflight")    # 赛前第一步
app.run("button_led")   # 按键 + LED 交互
app.run("adc")          # 光敏 ADC
app.run("i2c")          # I2C 扫描
app.run("sensors")      # 温湿度/加速度
app.run("uart")         # 串口回环
app.run("storage")      # 存储卡读写
app.run_all()           # 一次运行全部已启用项目
```
