# easy_api 接口文档

本文档整理当前 `starter/easy_api.py` 中由 `easy_api_main_builder.html` 使用的
全部接口，并补充零基础用户常用的测试和兼容接口。用户只需要在 Thonny REPL
或自己的 `main.py` 中写：

```python
from easy_api import *
```

然后按本文档调用函数即可。

> 注意：实际文件名是 `easy_api.py`。如果写成 `eazy_api` 会导入失败。

## 1. 基本规则

- `xxx(1)`：启用某个功能。
- `xxx(0)`：关闭某个功能，或释放相关对象。
- `readxxx()`：读取数据。
- `setxxx(...)` / `sendxxx(...)` / `writexxx(...)`：输出或控制。
- `testxxx()`：运行一次标准测试，并打印 `PASS / FAIL / SKIP`。

返回值约定：

- 控制成功通常返回 `True`。
- 读取成功返回数字、字节、字符串、元组、列表或字典。
- 未启用、未配置或不适合运行时返回 `None`。
- 测试失败返回 `False`。

## 2. 最小示例

```python
from easy_api import *

init()

guangmin(1)
i = readguangmin()
print(i)

anjian(1)
event = waitanjian()
print(event)
```

## 2A. Scratch 风格运算接口

这些接口由 HTML 的运算积木生成，算法文件按需导入，不需要启用硬件模块。

- `baoliuxiaoshu(value, digits)`：将数字、列表或字典格式化为指定小数位的文字。
- `shuzipaixu(values, reverse=False)`：数字列表排序；`reverse=True` 时从大到小。
- `zuidazhi(values)` / `zuixiao(values)`：返回数字列表最大值 / 最小值；没有有效数字时返回 `None`。
- `pingjunzhi(values)`：返回数字列表平均值；没有有效数字时返回 `None`。
- `pin_jie(*items)`：把任意数量的文字或变量无分隔拼接为一段文字。
- `yunsuan(left, operator, right)`：数字二元运算。运算符支持 `+`、`-`、`*`、`/`、`//`、`%`、`**`；除数为 0 时返回 `None`。
- `suijishu(start, end)`：范围随机数。两个边界都是整数时返回包含边界的整数，否则返回范围内小数。
- `shuxue(operator, value)`：单值数学函数。支持 `round`、`abs`、`floor`、`ceil`、`sqrt`、三角函数、对数和指数。
- `bijiao(left, operator, right)`：比较两个值，支持 `==`、`!=`、`>`、`>=`、`<`、`<=`。
- `luoji(left, operator, right=None)`：逻辑运算，支持 `and`、`or`、`not`。
- `wenbenchangdu(text)`：返回文本长度。
- `wenbenzifu(text, index)`：按 Scratch 习惯从 1 开始读取字符，越界返回空文字。
- `wenbenbaohan(text, part)`：忽略大小写判断文本是否包含指定内容。
- `zhuanshuzi(value)`：将变量或文字转换为数字，无法转换时返回 0。
- `zhuanwenzi(value)`：将变量转换为文字。

HTML 中使用“数字运算”“数学函数”“比较与逻辑”“文本运算”积木，将结果保存到变量后，再连接 LCD、串口、BLE 或条件判断积木。UART2/BLE 是否收到数据不再使用专用判断模块；在原有“变量比较”中选择“空值 None”和“不等于”即可。

## 2B. main.py 生成器接口分类总表

本节与 `easy_api_main_builder.html` 的接口分类同步。生成器使用
`import easy_api as api`，所以下列示例均带 `api.`；使用
`from easy_api import *` 时可去掉此前缀。

放置规则：模块启用、模式和通信参数放“启动区”；按键、UART/BLE 新消息、
`updateaudio()` 和临时 LCD 状态放“快速轮询区”；传感器、状态、定位和普通
LCD 刷新放“慢速刷新区”。LED、GPIO、音频等动作应放在事件或条件内部。

### System / 系统

| 生成器接口 | 功能与返回值 |
|---|---|
| `api.init()` | 初始化已启用的安全模块，返回是否成功。 |
| `api.status()` | 打印并返回功能、错误和传感器状态字典。 |
| `api.delay(ms)` | 阻塞等待指定毫秒，返回 `True`。 |
| `api.millis()` | 返回单调递增的运行毫秒计数，适合非阻塞计时。 |
| `api.preflight()` | 检查固件必需模块，返回测试结果。 |
| `api.ready()` | 预检的就绪入口，等同运行 `testyujian()`。 |
| `api.testall()` | 运行默认安全测试集合。 |

### LED / 指示灯

| 生成器接口 | 功能与返回值 |
|---|---|
| `api.led(enabled=1)` | 启用或关闭 LED 模块；关闭时同时熄灭。 |
| `api.setled(name, value)` | 设置 `red`、`green`、`blue` 等指定灯的电平。 |
| `api.ledoff()` | 熄灭全部已配置 LED。 |
| `api.ledrun(delay_ms=250)` | 按配置顺序执行一次流水灯。 |
| `api.testled()` | 执行 LED 自检。 |

### Key / 按键

| 生成器接口 | 功能与返回值 |
|---|---|
| `api.anjian(enabled=1)` | 启用或关闭 USER 键和五向键。 |
| `api.readanjian()` | 非阻塞取出一个 `(按键名, 事件)`；无事件返回 `None`。 |
| `api.lastanjian()` | 返回最近一次已取出的按键事件，不再读取硬件。 |
| `api.keytext(event)` | 只把 `short` / `long` 格式化为紧凑英文状态。 |
| `api.readanjianadc()` | 读取五向键 ADC 原始值；不可用时返回 `None`。 |
| `api.readanjian_direction()` | 按当前 ADC 值直接返回 `up`、`down`、`left`、`right` 或 `center`；松手/超出阈值返回 `None`。别名：`readkeydirection()`、`buttondirection()`。 |
| `api.waitkey(name, timeout=10000, event="short")` | 阻塞等待指定按键事件，超时返回 `None`。 |
| `api.iskey(name)` | 返回指定键当前是否按住。 |
| `api.testanjian(timeout=15000)` | 在限定时间内交互测试全部按键。 |

按键名为 `user`、`up`、`down`、`left`、`right`、`center`；常用事件为
`press`、`release`、`short`、`long`。普通轮询优先使用 `readanjian()`，避免
`waitkey()` 阻塞其他任务。

五向键使用 UniKnect LCD Shield 的模拟电阻梯形输入。当前套件默认引脚为
`config.NAV_ADC_PIN = "C1"`（Arduino Shield A3），方向对应关系由
`config.NAV_THRESHOLDS` 决定：`left`、`down`、`center`、`right`、`up`。
不同批次电阻有偏差时，先运行 `examples/00_nav_calibration.py`，再修改
`NAV_THRESHOLDS`；网页生成器和运行库都会使用同一份配置。

### Sensor / 传感器

| 生成器接口 | 功能与返回值 |
|---|---|
| `api.guangmin(enabled=1)` | 启用或关闭光敏 ADC。 |
| `api.readguangmin()` | 返回光敏 ADC 原始值。 |
| `api.readguangmin_percent()` | 返回换算后的光敏百分比。 |
| `api.readguangmin_all()` | 返回含原始值和百分比的光敏字典。 |
| `api.wenhumi(enabled=1)` | 启用或关闭温湿度传感器。 |
| `api.readwendu()` / `api.readshidu()` | 分别返回温度 / 湿度。 |
| `api.jiasudu(enabled=1)` | 启用或关闭三轴加速度计。 |
| `api.readx()` / `api.readyaxis()` / `api.readz()` | 分别返回 X / Y / Z 轴加速度。 |

### IO-Bus / GPIO与总线

| 生成器接口 | 功能与返回值 |
|---|---|
| `api.i2c(enabled=1)` | 启用或关闭 I2C 总线。 |
| `api.scani2c()` | 扫描并返回 I2C 地址列表。 |
| `api.gpio(enabled=1)` | 设置 GPIO 功能开关。 |
| `api.setgpio(pin, value)` | 把指定引脚设为输出并写入 `0` 或 `1`。 |
| `api.readgpio(pin)` | 把指定引脚设为下拉输入并读取电平。 |
| `api.highpins(pins)` | 不改变引脚模式，返回当前高电平引脚名组成的文字。 |
| `api.timer(enabled=1)` | 设置定时器功能开关。 |
| `api.after(ms, func)` | 等待后执行一次函数；当前实现会阻塞。 |
| `api.every(ms, func, count=5)` | 按间隔重复执行函数；当前实现会阻塞。 |
| `api.pwm(enabled=1)` | 启用或关闭 PWM；关闭时停止当前输出。 |
| `api.startpwm(pin=None, freq=1000, duty=50)` | 启动 PWM，参数为引脚、频率和占空比。 |
| `api.setpwmduty(duty)` / `api.readpwmduty()` | 动态设置 / 读取当前 PWM 占空比。 |
| `api.stoppwm()` | 停止当前 PWM 输出。 |
| `api.spi(enabled=1)` | 启用或关闭 SPI 回环功能。 |
| `api.sendspi(data=b"test")` | SPI 发送并返回同时读到的数据。 |
| `api.beep(ms=300, freq=2000)` | 蜂鸣器动作积木使用的接口；响指定时长和频率。 |

高级引脚配置积木：

| 接口 | 用途 |
|---|---|
| `api.configuregpio(pin, mode="in", pull="none", initial=0)` | 为指定 GPIO 选择输入/输出、上拉/下拉，并设置输出初值。 |
| `api.readadc(pin)` | 读取指定 ADC 引脚的 16 位原始值；板载光敏默认仍使用 `C5`，五向键使用 `C1`。 |
| `api.configurei2c(bus_id=1, sda=None, scl=None, freq=400000)` | 配置 I2C 编号、频率和可选 SDA/SCL；留空时使用固件默认引脚。 |
| `api.configurespi(bus_id=1, baudrate=1000000, polarity=0, phase=0, sck=None, mosi=None, miso=None)` | 配置 SPI 速率、模式和可选信号引脚。 |

### LCD-Text / 屏幕与文本

| 生成器接口 | 功能与返回值 |
|---|---|
| `api.lcd(enabled=1)` | 启用或关闭 LCD。 |
| `api.clearlcd()` | 立即清屏。 |
| `api.clearlcdline(row)` | 只清除一行。 |
| `api.showlcd(text, row=0, col=0)` | 从指定行列显示文字或变量。 |
| `api.showlcdcolor(text, row=0, col=0, color="white")` | 从指定行列彩色显示。 |
| `api.showlcdtemp(text, ms=10000, row=0, col=0)` | 非阻塞临时显示，并在到期后由状态轮询清屏。 |
| `api.showlcdrowtemp(text, ms=5000, row=0, col=0, color="white")` | 单行临时显示，不清其它行。 |
| `api.updatelcdtemp()` | 在快速轮询中清除已到期的单行临时消息。 |
| `api.lcdtempactive()` | 临时消息有效时返回 `True`；到期时清屏并返回 `False`。 |
| `api.lcdrowtempactive(row=0)` | 指定行的临时消息仍有效时返回 `True`，用于避免普通刷新覆盖它。 |
| `api.lcdline(row, text, col=0)` | 按“行、文字、列”的参数顺序显示。 |
| `api.lcdvalue(name, value, row=0, col=0)` | 显示 `名称: 值`。 |
| `api.showstatus(row=0, col=0)` | 显示就绪状态并返回 `status()` 字典。 |

临时显示必须在快速轮询中持续调用 `api.lcdtempactive()`；慢速 LCD 刷新应先
判断其返回值，只在临时消息不活动时刷新普通页面。

### Algorithm / 算法与运算

| 生成器接口 | 功能与返回值 |
|---|---|
| `api.baoliuxiaoshu(value, digits)` | 按位数格式化数据，返回文字。 |
| `api.shuzipaixu(values, reverse=False)` | 数字排序，返回新列表。 |
| `api.zuidazhi(values)` / `api.zuixiao(values)` | 返回最大值 / 最小值。 |
| `api.pingjunzhi(values)` | 返回平均值。 |
| `api.pin_jie(*items)` | 把任意数量内容拼接为文字。 |
| `api.yunsuan(left, operator, right)` | 加、减、乘、除、整除、取余或乘方。 |
| `api.suijishu(start, end)` | 生成包含边界的整数或范围内小数。 |
| `api.shuxue(operator, value)` | 执行取整、绝对值、平方根、三角或对数等运算。 |
| `api.bijiao(left, operator, right)` | 比较两个值，返回布尔值。 |
| `api.luoji(left, operator, right=None)` | 执行 and、or、not 逻辑，返回布尔值。 |
| `api.wenbenchangdu(text)` | 返回文本长度。 |
| `api.wenbenzifu(text, index)` | 从 1 开始取字符，越界返回空文字。 |
| `api.wenbenbaohan(text, part)` | 忽略大小写判断包含关系。 |
| `api.zhuanshuzi(value)` | 转为数字，失败返回 `0`。 |
| `api.zhuanwenzi(value)` | 转为文字。 |

算法接口会按需加载 `starter/lib/alg/` 中的独立模块。生成器下载前会根据实际
使用的算法积木生成所需文件清单；未使用的算法模块无需上传到板上。

### UART / 串口

| 生成器接口 | 功能与返回值 |
|---|---|
| `api.uart(enabled=1, uart_id=None, baudrate=None, timeout=None)` | 启用 UART，并可同时修改编号、波特率和超时。 |
| `api.setuart(uart_id, baudrate=115200, timeout=1000)` | 配置并打开指定 UART。比赛固定使用 `api.setuart(2, ...)`。 |
| `api.senduart(data)` | 通过 UART2 发送；默认同时镜像到电脑 REPL 串口。 |
| `api.readuart()` | 非阻塞读取当前原始数据，无数据返回 `None`。 |
| `api.readuarttext()` | 非阻塞读取并转为可显示文字，无数据返回 `None`。 |
| `api.waituart(timeout=10000)` | 阻塞等待数据，超时返回 `None`。 |
| `api.rs232(enabled=1)` / `api.sendrs232(data=b"RS232")` | 启用 RS232 / 发送数据，必须使用电平转换器。 |
| `api.rs485(enabled=1)` / `api.sendrs485(data=b"RS485")` | 启用 RS485 / 自动切换方向后发送。 |

比赛数据串口只使用 UART2（`usart_b`，连接电脑 `COM43`）；`COM17` 仅用于
REPL 烧录和调试，不能把 `usart_a` 当作题目数据串口。

高级 UART 配置：

```python
api.configureuart(2, 115200, 8, None, 1, 1000, None, None)
```

参数依次为 UART 编号、波特率、数据位、校验（`None`/`"even"`/`"odd"`）、停止位、超时、TX 引脚和 RX 引脚。留空引脚使用固件默认映射。

### Storage-Audio / 存储与音频

| 生成器接口 | 功能与返回值 |
|---|---|
| `api.cunchu(enabled=1)` | 启用或关闭存储功能。 |
| `api.sdcard(enabled=1)` | `cunchu()` 的 SDCard 语义别名；启用后才能调用下列存储接口。 |
| `api.writefile(path, data)` | 覆盖写入文字、字节或变量，成功返回 `True`。 |
| `api.readfile(path, size=1024, default="")` | 读取指定字节数；失败返回 `default`。 |
| `api.removefile(path)` | 删除文件，返回是否成功。 |
| `api.listfiles(path="*")` | 列出文件/目录，返回 `[{"name": ..., "size": ..., "directory": ...}]`。 |
| `api.storageinfo(volume="UFS")` | 返回卷空间字典 `volume/total/free/used`；UniKnect 官方示例使用 `UFS`。 |
| `api.makedir(path)` | 创建目录，成功返回 `True`。 |
| `api.removedir(path, force=False)` | 删除目录；`force=True` 时按固件能力尝试递归/强制删除。 |
| `api.yinpin(enabled=1)` | 初始化或释放录音、播放和 TTS。 |
| `api.recordstart(path=None)` | 开始录音；默认使用配置文件路径。 |
| `api.recordstop()` | 停止当前录音。 |
| `api.record(path=None, ms=1500)` | 阻塞录音指定毫秒后停止。 |
| `api.recordtimed(path=None, ms=1500)` | 非阻塞开始定时录音。 |
| `api.updateaudio()` | 更新定时录音；到期自动停止，必须放快速轮询。 |
| `api.playfile(path=None, wait=True)` | 播放本地音频；`wait=False` 时立即返回。 |
| `api.play(path=None, wait=True)` | `playfile()` 的别名。 |
| `api.stopplay()` / `api.playstop()` | 停止本地音频播放。 |
| `api.tts(text=None, wait=True)` | 播放 TTS；`wait=False` 时不阻塞主循环。 |
| `api.say(text=None)` | 阻塞式 `tts(text)` 的别名。 |
| `api.settts(speed=None, pitch=None, volume=None)` | 设置 TTS 语速、音调和音量；`None` 表示不改。 |
| `api.setttsparams(speed=None, pitch=None, volume=None)` | `settts()` 的别名。 |
| `api.setvolume(value=None)` | 保存并应用扬声器音量。 |
| `api.volume(value=None)` | `setvolume()` 的别名，不是读取接口。 |
| `api.readvolume()` | 返回 Easy API 当前保存的音量。 |

生成器“写文件”积木写固定文字，“写变量到文件”积木直接写变量；两者不要
混用。要保持按键和通信响应，优先使用 `recordtimed()`、`playfile(..., False)`
和 `tts(..., False)`，并在快速轮询调用 `updateaudio()`。

存储路径由 QuecPython 官方 `quectel.File` 接口解释。音频和文件示例中的
`SD:` 是设备文件路径前缀；它不是标准 MicroPython 的通用挂载点。空间统计
使用 `File.statvfs("UFS")`，这是当前 UniKnect/EC200U 参考示例中的卷名。
网页积木和运行库已经生成这些调用，但是否插入实体 SD 卡、卡是否被固件挂载，
必须在目标板上运行 `api.teststorage()` 或 `api.storageinfo()` 实测确认，不能
仅凭代码生成结果宣称硬件已验证。

### Wireless-Location / 无线与定位

| 生成器接口 | 功能与返回值 |
|---|---|
| `api.lte(enabled=1)` | 启用或关闭 LTE。 |
| `api.readlte()` | 返回 LTE 状态快照，不可用时返回 `None`。 |
| `api.ble(enabled=1, mode=None, target_name=None)` | 启用/关闭 BLE，可指定 `server` 或 `client`。 |
| `api.setblemode(mode="server", target_name=None)` | 保存 BLE 模式和客户端目标名。 |
| `api.bleserver(enabled=1)` | 服务端模式快捷入口。 |
| `api.bleclient(enabled=1, target_name=None)` | 客户端模式快捷入口。 |
| `api.scanble(timeout=5000, target_name=None)` | 客户端扫描，返回设备列表。 |
| `api.connectble(target_name=None, timeout=10000)` | 连接目标设备，返回是否成功。 |
| `api.discoverble(timeout=5000)` | 发现服务和特征，返回是否成功。 |
| `api.readble()` / `api.readbleclient()` | 返回 BLE 状态字典；后者是完全相同的别名。 |
| `api.readbledata()` | 消费一条新接收消息并返回文字；无消息返回 `None`。 |
| `api.sendble(data, handle=None)` | 服务端通知或客户端写入；客户端可指定值句柄。 |
| `api.readblehandle(handle=None)` | 客户端读取值句柄，省略时使用配置值。 |
| `api.writeblehandle(handle, data)` | 客户端写入指定值句柄。 |
| `api.gnss(enabled=1)` | 启用或关闭 GNSS。 |
| `api.readgnss()` | 返回 GNSS 定位字典；室内无定位时通常为 `None`。 |
| `api.readgnsslat()` / `api.readgnsslon()` | 分别读取 GNSS 纬度 / 经度。 |
| `api.lbs(enabled=1)` | 启用或关闭 LBS；定位通常需要可用 SIM 和蜂窝网络。 |
| `api.readlbs()` | 返回 LBS 定位字典；重试间隔内复用缓存。 |
| `api.readlocation()` | 优先 GNSS，失败时用 LBS，返回含 `source` 的定位字典。 |

定位积木必须先执行 `location_data = api.readlocation()`，再从同一字典读取
`source`、`latitude` 和 `longitude`。这样一次刷新只发起一次定位，不会因分别
读取纬度和经度而重复阻塞。纬度和经度应保留原值，其他数字可再连接
`api.baoliuxiaoshu(value, digits)`。

### HMI / 人机交互

| 生成器接口 | 功能与返回值 |
|---|---|
| `api.hmi(enabled=1)` | 同时启用或关闭 LCD 与按键。 |
| `api.menu()` | 运行一次默认 HMI 菜单。 |
| `api.runhmi(timeout=30000)` | 在指定时间内运行交互菜单。 |
| `api.testhmi()` | 执行 HMI 测试。 |

`menu()` 和 `runhmi()` 会接管按键与屏幕，属于阻塞式完整交互流程；不要把它们
放进需要同时处理 UART、BLE 或传感器的快速轮询。

### 生成器参数积木的实际调用

生成器会根据输入框类型正确区分固定文字与变量，典型输出如下：

```python
api.writefile("SD:test.txt", "hello")       # 固定文字
api.writefile("SD:test.txt", show_text)      # 变量，不加引号
file_text = api.readfile("SD:test.txt", 1024)
api.recordtimed("SD:test.wav", 10000)
api.playfile("SD:test.wav", False)
api.tts("光线暗", False)
api.showlcdtemp(show_text, 10000, 0, 0)
api.sendble(show_text)
```

## 3. 系统与通用接口

| 函数 | 作用 | 示例 |
|---|---|---|
| `init()` | 初始化所有已启用功能 | `init()` |
| `status()` | 打印并返回当前快照 | `data = status()` |
| `delay(ms)` | 延时，单位毫秒 | `delay(500)` |
| `millis()` | 读取单调递增的运行毫秒数 | `now = millis()` |
| `preflight()` | 检查固件模块是否齐全 | `preflight()` |
| `yujian()` | `preflight()` 的中文拼音别名 | `yujian()` |
| `ready()` | 运行预检，确认是否准备好 | `ready()` |
| `testyujian()` | 预检测试 | `testyujian()` |
| `testall()` | 运行默认安全测试集合 | `testall()` |

## 4. LED 接口

| 函数 | 作用 | 示例 |
|---|---|---|
| `led(1)` | 启用 LED 功能 | `led(1)` |
| `led(0)` | 关闭 LED 功能并熄灯 | `led(0)` |
| `setled(name, value)` | 设置指定 LED | `setled("red", 1)` |
| `ledoff()` | 关闭所有 LED | `ledoff()` |
| `ledrun(delay_ms=250)` | LED 流水灯 | `ledrun()` |
| `testled()` | LED 测试 | `testled()` |

可用 LED 名称以 `config.py` 的 `LED_PINS` 为准，当前常用：`red`、`green`、`blue`。

## 5. 按键接口

| 函数 | 作用 | 示例 |
|---|---|---|
| `anjian(1)` | 启用按键功能 | `anjian(1)` |
| `anjian(0)` | 关闭按键功能 | `anjian(0)` |
| `button(1)` | `anjian(1)` 的英文别名 | `button(1)` |
| `readanjian()` | 读取一次按键事件，不阻塞 | `e = readanjian()` |
| `readbutton()` | `readanjian()` 的英文别名 | `readbutton()` |
| `keytext(event)` | 只把短按/长按事件格式化为英文状态；其它事件返回 `None` | `s = keytext(e)` |
| `waitanjian(timeout=10000)` | 等待任意按键事件 | `waitanjian()` |
| `waitbutton(timeout=10000)` | `waitanjian()` 的英文别名 | `waitbutton()` |
| `waitkey(name, timeout=10000, event="short")` | 等待指定按键指定事件 | `waitkey("center")` |
| `waitshort(timeout=10000)` | 等待任意短按 | `waitshort()` |
| `waitlong(timeout=10000)` | 等待任意长按 | `waitlong()` |
| `iskey(name)` | 判断某个按键当前是否按下 | `iskey("user")` |
| `testanjian(timeout=15000)` | 按键测试 | `testanjian()` |
| `testbutton(timeout=15000)` | `testanjian()` 的英文别名 | `testbutton()` |
| `testanjianled(timeout=15000)` | 按键触发 LED 测试 | `testanjianled()` |
| `testbuttonled(timeout=15000)` | `testanjianled()` 的英文别名 | `testbuttonled()` |

按键名称：

```text
user, up, down, left, right, center
```

事件名称：

```text
press, release, short, long, repeat
```

示例：

```python
anjian(1)
event = waitanjian()
if event:
    name, action = event
    print(name, action)
```

## 6. 光敏 ADC 接口

| 函数 | 作用 | 示例 |
|---|---|---|
| `guangmin(1)` | 启用光敏 ADC | `guangmin(1)` |
| `guangming(1)` | `guangmin(1)` 的兼容别名 | `guangming(1)` |
| `light(1)` | `guangmin(1)` 的英文别名 | `light(1)` |
| `readguangmin()` | 读取光敏原始值 | `i = readguangmin()` |
| `readguangmin_percent()` | 读取光敏百分比 | `p = readguangmin_percent()` |
| `readguangmin_all()` | 读取完整光敏数据 | `d = readguangmin_all()` |
| `testguangmin()` | 光敏测试 | `testguangmin()` |

完整数据格式：

```python
{"raw": 15171, "voltage": 0.76, "percent": 23.1}
```

## 7. I2C 与传感器接口

### I2C

| 函数 | 作用 | 示例 |
|---|---|---|
| `i2c(1)` | 启用 I2C | `i2c(1)` |
| `scani2c()` | 扫描 I2C 地址 | `addr = scani2c()` |
| `testi2c()` | I2C 测试 | `testi2c()` |

### 温湿度 AHT20

| 函数 | 作用 | 示例 |
|---|---|---|
| `wenhumi(1)` | 启用温湿度读取 | `wenhumi(1)` |
| `aht20(1)` | `wenhumi(1)` 的别名 | `aht20(1)` |
| `readwenhumi()` | 读取温度和湿度 | `t, h = readwenhumi()` |
| `readwendu()` | 读取温度 | `t = readwendu()` |
| `readshidu()` | 读取湿度 | `h = readshidu()` |
| `testwenhumi()` | 温湿度测试 | `testwenhumi()` |

### 加速度 LIS2DH12

| 函数 | 作用 | 示例 |
|---|---|---|
| `jiasudu(1)` | 启用加速度读取 | `jiasudu(1)` |
| `motion(1)` | `jiasudu(1)` 的英文别名 | `motion(1)` |
| `readjiasudu()` | 读取三轴加速度 | `x, y, z = readjiasudu()` |
| `readx()` | 读取 X 轴 | `x = readx()` |
| `readyaxis()` | 读取 Y 轴 | `y = readyaxis()` |
| `readz()` | 读取 Z 轴 | `z = readz()` |
| `testjiasudu()` | 加速度测试 | `testjiasudu()` |

注意：Y 轴函数叫 `readyaxis()`，不是 `ready()`，因为 `ready()` 已用于系统预检。

## 8. GPIO 接口

| 函数 | 作用 | 示例 |
|---|---|---|
| `gpio(1)` | 启用 GPIO | `gpio(1)` |
| `setgpio(pin, value)` | 设置 GPIO 输出 | `setgpio("D2", 1)` |
| `readgpio(pin)` | 读取 GPIO 输入 | `v = readgpio("D3")` |
| `highpins(pins)` | 不改变已有引脚模式，汇总当前为高电平的引脚名 | `s = highpins(("PA3", "PC0"))` |
| `testgpio(out_pin=None, in_pin=None)` | GPIO 回环测试 | `testgpio("D2", "D3")` |

回环测试需要用杜邦线把输出脚接到输入脚。

## 9. 定时器接口

| 函数 | 作用 | 示例 |
|---|---|---|
| `timer(1)` | 启用定时器功能 | `timer(1)` |
| `dingshiqi(1)` | `timer(1)` 的中文拼音别名 | `dingshiqi(1)` |
| `after(ms, func)` | 延时后执行函数 | `after(1000, hello)` |
| `every(ms, func, count=5)` | 周期执行函数 | `every(1000, hello, 5)` |
| `testtimer()` | 定时器测试 | `testtimer()` |

示例：

```python
def hello():
    print("tick")

every(1000, hello, 5)
```

## 10. PWM 接口

| 函数 | 作用 | 示例 |
|---|---|---|
| `pwm(1)` | 启用 PWM | `pwm(1)` |
| `pwm(0)` | 关闭 PWM 并停止输出 | `pwm(0)` |
| `startpwm(pin=None, freq=1000, duty=50)` | 开始 PWM 输出 | `startpwm("D5", 1000, 50)` |
| `setpwmduty(duty)` | 不重建 PWM，动态设置当前占空比并限制在 0–100% | `setpwmduty(75)` |
| `readpwmduty()` | 读取当前输出占空比；未启动时返回 `None` | `duty = readpwmduty()` |
| `stoppwm()` | 停止 PWM 输出 | `stoppwm()` |
| `readpwm(pin=None, ms=500)` | 测量 PWM | `readpwm("D6")` |
| `testpwm(out_pin=None, measure_pin=None)` | PWM 输出 + 测量测试 | `testpwm("D5", "D6")` |

测试时需要用杜邦线把 PWM 输出脚接到测量脚。

## 11. 蜂鸣器接口

| 函数 | 作用 | 示例 |
|---|---|---|
| `fengmingqi(1)` | 启用蜂鸣器功能 | `fengmingqi(1)` |
| `buzzer(1)` | `fengmingqi(1)` 的英文别名 | `buzzer(1)` |
| `beep(ms=300, freq=2000)` | 蜂鸣器响一声 | `beep(300)` |
| `testbuzzer()` | 蜂鸣器测试 | `testbuzzer()` |

需要先在 `config.py` 设置 `BUZZER_PIN`。

## 12. LCD 接口

| 函数 | 作用 | 示例 |
|---|---|---|
| `lcd(1)` | 启用 LCD 功能 | `lcd(1)` |
| `clearlcd()` | 清屏 | `clearlcd()` |
| `showlcd(text, row=0, col=0)` | 从指定行列开始显示文字 | `showlcd("Hello", 0, 0)` |
| `showlcdcolor(text, row=0, col=0, color="white")` | 用指定颜色显示文字 | `showlcdcolor("T:23.4", 0, 0, "red")` |
| `clearlcdline(row)` | 只清除指定文字行，不影响其它行 | `clearlcdline(3)` |
| `showlcdrowtemp(text, ms=5000, row=0, col=0, color="white")` | 在单行临时显示，超时后只清该行 | `showlcdrowtemp(text, 5000, 3, 0, "cyan")` |
| `updatelcdtemp()` | 更新单行临时显示计时，必须放快速轮询区 | `updatelcdtemp()` |
| `lcdrowtempactive(row=0)` | 查询指定行是否正由临时消息占用 | `busy = lcdrowtempactive(5)` |
| `showtest(name, status, detail="")` | 显示测试结果 | `showtest("ADC", "PASS", "ok")` |
| `testlcd()` | LCD 测试 | `testlcd()` |

颜色可选 `white`、`red`、`blue`、`green`、`cyan`、`magenta`、`yellow`。
同一行多种颜色时，先调用一次 `clearlcdline(row)`，再用不同列数连续调用
`showlcdcolor()`。`showlcdrowtemp()` 与旧的全屏 `showlcdtemp()` 相互独立。

当前板卡 LCD 使用 `PF12`（DC）和 `PD14`（CS）。`highpins()` 读取这两个名称时
不会把它们改成输入模式，但读到的是 LCD 当前驱动电平，而不是空闲外接 GPIO。

## 13. SPI 接口

| 函数 | 作用 | 示例 |
|---|---|---|
| `spi(1)` | 启用 SPI 回环功能 | `spi(1)` |
| `sendspi(data=b"test")` | SPI 发送并读取 | `r = sendspi(b"abc")` |
| `testspi(data=b"QUECTEL-SPI")` | SPI 回环测试 | `testspi()` |

SPI 回环需要 MOSI 接 MISO。

## 14. UART / RS232 / RS485 接口

### UART TTL

| 函数 | 作用 | 示例 |
|---|---|---|
| `uart(1)` | 启用 UART 功能 | `uart(1)` |
| `senduart(data)` | 发送 UART 数据，并默认同步输出到电脑 USB/REPL 串口 | `senduart(b"hi")` |
| `readuart()` | 读取 UART 数据 | `data = readuart()` |
| `readuarttext()` | 非阻塞读取 UART2 新文字；没有数据返回 `None` | `text = readuarttext()` |
| `testuart(data=b"hello")` | UART 回环测试 | `testuart()` |

UART 回环需要 TX 接 RX。`api.senduart(...)` 默认会同时发送到外接 UART 和电脑 USB/REPL 串口，方便在电脑串口工具里看到同一份输出；如需关闭，在 `starter/config.py` 中把 `UART_MIRROR_TO_PC` 改成 `False`。

### RS232

| 函数 | 作用 | 示例 |
|---|---|---|
| `rs232(1)` | 启用 RS232 功能 | `rs232(1)` |
| `sendrs232(data)` | 发送 RS232 数据 | `sendrs232(b"hi")` |
| `readrs232()` | 读取 RS232 数据 | `readrs232()` |
| `testrs232(data=b"RS232")` | RS232 测试 | `testrs232()` |

RS232 必须使用真实 RS232 电平转换器，并设置：

```python
FEATURES["rs232"] = True
RS232_TRANSCEIVER_CONFIRMED = True
```

### RS485

| 函数 | 作用 | 示例 |
|---|---|---|
| `rs485(1)` | 启用 RS485 | `rs485(1)` |
| `setrs485tx(enabled)` | 设置 RS485 收发方向 | `setrs485tx(1)` |
| `sendrs485(data)` | 发送 RS485 数据 | `sendrs485(b"hi")` |
| `readrs485()` | 读取 RS485 数据 | `readrs485()` |
| `testrs485(data=b"RS485")` | RS485 测试 | `testrs485()` |

需要先在 `config.py` 设置 `RS485_DIRECTION_PIN`。

## 15. 存储文件接口

| 函数 | 作用 | 示例 |
|---|---|---|
| `cunchu(1)` | 启用存储 | `cunchu(1)` |
| `storage(1)` | `cunchu(1)` 的英文别名 | `storage(1)` |
| `writefile(path, data)` | 写文件 | `writefile("test.txt", b"hi")` |
| `readfile(path, size=1024, default="")` | 读文件；失败返回默认值 | `data = readfile("SD:test.txt")` |
| `removefile(path)` | 删除文件 | `removefile("test.txt")` |
| `teststorage()` | 存储读写测试 | `teststorage()` |

## 16. 音频接口

| 函数 | 作用 | 示例 |
|---|---|---|
| `yinpin(1)` | 启用音频 | `yinpin(1)` |
| `audio(1)` | `yinpin(1)` 的英文别名 | `audio(1)` |
| `recordstart(path=None)` | 开始录音 | `recordstart("SD:test.wav")` |
| `recordstop()` | 停止录音 | `recordstop()` |
| `record(path=None, ms=1500)` | 阻塞录音指定时间 | `record("SD:test.wav", 1500)` |
| `recordtimed(path=None, ms=1500)` | 非阻塞定时录音 | `recordtimed("SD:test.wav", 10000)` |
| `updateaudio()` | 更新非阻塞录音并在到期时停止 | `updateaudio()` |
| `playfile(path=None, wait=True)` | 播放本地文件，可选择不等待 | `playfile("SD:test.wav", False)` |
| `play(path=None, wait=True)` | `playfile()` 的别名 | `play("SD:test.wav")` |
| `stopplay()` / `playstop()` | 停止播放 | `stopplay()` |
| `tts(text=None, wait=True)` | TTS 朗读，可选择不等待 | `tts("Quectel test", False)` |
| `say(text=None)` | 阻塞式 `tts()` 的别名 | `say("Quectel test")` |
| `settts(speed=None, pitch=None, volume=None)` | 设置 TTS 参数 | `settts(5, 5, 8)` |
| `setttsparams(speed=None, pitch=None, volume=None)` | `settts()` 的别名 | `setttsparams(5, 5, 8)` |
| `setvolume(value=None)` / `volume(value=None)` | 设置扬声器音量 | `setvolume(8)` |
| `readvolume()` | 读取当前保存的音量 | `value = readvolume()` |
| `testaudio()` | 音频测试 | `testaudio()` |

音频功能默认关闭，需要确认硬件后再启用。`recordtimed()` 后必须在快速轮询
持续调用 `updateaudio()`，否则不会在设定时间自动停止。

## 17. HMI 接口

| 函数 | 作用 | 示例 |
|---|---|---|
| `hmi(1)` | 启用 LCD + 按键 | `hmi(1)` |
| `menu()` | 运行菜单 | `menu()` |
| `runhmi(timeout=30000)` | 运行 HMI 菜单 | `runhmi()` |
| `testhmi()` | HMI 测试 | `testhmi()` |

## 17A. 4G / BLE / GNSS / LBS 接口

这些接口会 lazy import `quectel`，在 PC 端或固件缺少模块时不会影响导入 `easy_api.py`，但启用或测试会返回 `FAIL` / `None`。

### 4G / LTE

| 函数 | 作用 | 示例 |
|---|---|---|
| `lte(1)` | 启用 4G/LTE 网络 | `lte(1)` |
| `g4(1)` | `lte(1)` 的短别名 | `g4(1)` |
| `network4g(1)` | `lte(1)` 的英文别名 | `network4g(1)` |
| `readlte()` | 读取 LTE 状态快照 | `data = readlte()` |
| `readg4()` | `readlte()` 的别名 | `data = readg4()` |
| `testlte()` | LTE 启动测试 | `testlte()` |

注意：Python 函数名不能以数字开头，`api.4G(1)` / `4G(1)` 都是非法写法。要使用：

```python
api.lte(1)
api.g4(1)
```

### BLE

| 函数 | 作用 | 示例 |
|---|---|---|
| `ble(enabled=1, mode=None, target_name=None)` | 启用或关闭 BLE，并可指定服务端或客户端 | `ble(1, "server")` |
| `setblemode(mode="server", target_name=None)` | 设置 `server` / `client` 模式及客户端目标名 | `setblemode("client", "Uniknect_BLE_DEMO")` |
| `bleserver(enabled=1)` | 服务端模式快捷入口 | `bleserver(1)` |
| `bleclient(enabled=1, target_name=None)` | 客户端模式快捷入口 | `bleclient(1, "Uniknect_BLE_DEMO")` |
| `scanble(timeout=5000, target_name=None)` | 客户端扫描附近设备，可按名称过滤 | `devices = scanble(5000, "Uniknect_BLE_DEMO")` |
| `connectble(target_name=None, timeout=10000)` | 连接目标设备，返回是否成功 | `ok = connectble("Uniknect_BLE_DEMO", 10000)` |
| `discoverble(timeout=5000)` | 发现已连接设备的服务和特征 | `ok = discoverble(5000)` |
| `readble()` | 返回含 `mode`、`ready`、地址和错误等信息的状态字典 | `data = readble()` |
| `readbleclient()` | `readble()` 的兼容别名 | `data = readbleclient()` |
| `readbledata()` | 消费一条 BLE 新消息；没有消息返回 `None` | `text = readbledata()` |
| `sendble(data, handle=None)` | 服务端连接后发送通知；客户端向值句柄写入数据。未连接时立即返回 `False`。 | `sendble("hello")` |
| `readblehandle(handle=None)` | 客户端读取值句柄；省略时使用配置值 | `readblehandle(21)` |
| `writeblehandle(handle, data)` | 客户端写入指定值句柄 | `writeblehandle(21, "hello")` |
| `testble()` | 检查当前 BLE 模式是否就绪 | `testble()` |

BLE 参数集中在 `starter/config.py`：`BLE_NAME`、`BLE_MODE`、
`BLE_CLIENT_TARGET_NAME`、`BLE_CLIENT_VALUE_HANDLE` 以及服务和特征 UUID。
服务端供电脑或手机连接；客户端负责扫描、连接、发现服务后读写句柄。两种模式
不能同时启用，切换模式后应重新调用 `ble(1, ...)`。

### GNSS

| 函数 | 作用 | 示例 |
|---|---|---|
| `gnss(1)` | 启用 GNSS | `gnss(1)` |
| `GNSS(1)` | `gnss(1)` 的大写别名 | `GNSS(1)` |
| `readgnss()` | 读取完整定位字典 | `data = readgnss()` |
| `readgnsslat()` | 读取纬度 | `lat = readgnsslat()` |
| `readgnsslon()` | 读取经度 | `lon = readgnsslon()` |
| `readgnss_lat()` | `readgnsslat()` 的别名 | `readgnss_lat()` |
| `readgnss_lon()` | `readgnsslon()` 的别名 | `readgnss_lon()` |
| `GNSSread()` | `readgnss()` 的别名 | `GNSSread()` |
| `GNSSreadLat()` | `readgnsslat()` 的别名 | `GNSSreadLat()` |
| `GNSSreadLon()` | `readgnsslon()` 的别名 | `GNSSreadLon()` |
| `testgnss()` | GNSS 启动/定位测试 | `testgnss()` |

GNSS 第一次定位可能需要时间；`readgnss()` 没有定位时返回 `None`，可在 `config.py` 中调整 `GNSS_TIMEOUT_MS`。

### LBS 与自动定位回退

| 函数 | 作用 | 示例 |
|---|---|---|
| `lbs(1)` | 启用 LBS 基站定位 | `lbs(1)` |
| `LBS(1)` | `lbs(1)` 的大写别名 | `LBS(1)` |
| `readlbs()` | 读取 LBS 完整定位字典 | `data = readlbs()` |
| `readlbslat()` | 读取 LBS 纬度 | `lat = readlbslat()` |
| `readlbslon()` | 读取 LBS 经度 | `lon = readlbslon()` |
| `readlocation()` | 优先读 GNSS；GNSS 无坐标时自动读 LBS | `data = readlocation()` |
| `readlocationlat()` | 自动定位纬度 | `lat = readlocationlat()` |
| `readlocationlon()` | 自动定位经度 | `lon = readlocationlon()` |
| `testlbs()` | LBS 定位测试 | `testlbs()` |

`readlocation()` 返回字典时会带 `source` 字段，值为 `"GNSS"` 或 `"LBS"`。比赛主程序建议用 `readlocation()`，这样 GNSS 没有定位时仍能显示 LBS 坐标。

## 18. 常用别名汇总

下表列出比赛代码中最常见的兼容写法；生成器的完整接口以第 2B 节 11 类总表
为准。

| 别名 | 等同于 |
|---|---|
| `button` | `anjian` |
| `readbutton` | `readanjian` |
| `readbuttonadc` | `readanjianadc` |
| `readkeyadc` | `readanjianadc` |
| `waitbutton` | `waitanjian` |
| `testbutton` | `testanjian` |
| `testbuttonled` | `testanjianled` |
| `guangming` | `guangmin` |
| `light` | `guangmin` |
| `aht20` | `wenhumi` |
| `motion` | `jiasudu` |
| `dingshiqi` | `timer` |
| `buzzer` | `fengmingqi` |
| `storage` | `cunchu` |
| `audio` | `yinpin` |
| `g4` | `lte` |
| `network4g` | `lte` |
| `readg4` | `readlte` |
| `GNSS` | `gnss` |
| `readgnss_lat` | `readgnsslat` |
| `readgnss_lon` | `readgnsslon` |
| `GNSSread` | `readgnss` |
| `GNSSreadLat` | `readgnsslat` |
| `GNSSreadLon` | `readgnsslon` |
| `LBS` | `lbs` |

## 19. 推荐现场调用顺序

```python
from easy_api import *

init()
preflight()

testled()
testguangmin()
testi2c()
testwenhumi()
testjiasudu()
testtimer()
teststorage()
```

如果题目要求杜邦线回环，再按题目接线后调用：

```python
testgpio("D2", "D3")
testpwm("D5", "D6")
testuart()
testspi()
```

## 20. 常见错误

- 写成 `from eazy_api import *`：错误，实际文件名是 `easy_api.py`。
- 忘记上传 `easy_api.py`：需要上传整个 `starter/` 目录。
- `SKIP`：通常是功能未开启或引脚未配置。
- `FAIL`：通常是接线、硬件、固件或参数有问题。
- RS232 不能 TTL 直连，必须接 RS232 电平转换器。

## 最新补充：LCD 行列、串口选择、持续刷新

### LCD 行列显示

LCD 显示函数已扩展为：

```python
showlcd(text, row=0, col=0)
```

含义：

- `text`：要显示的文字，也可以传变量、数字、列表、字典。
- `row`：行数，从 `0` 开始。
- `col`：列数，从 `0` 开始，按字符列理解。
- 文字会从被选中的行数和列数开始打印。

示例：

```python
from easy_api import *

lcd(1)
guangmin(1)
clearlcd()

i = readguangmin()
showlcd("Light:", 0, 0)
showlcd(i, 0, 8)      # 从第 0 行第 8 列开始显示变量 i
showlcd("OK", 2, 5)
```

LCD 新增函数：

| 函数 | 作用 | 示例 |
|---|---|---|
| `lcdclear()` | `clearlcd()` 的别名 | `lcdclear()` |
| `lcdtext(text, row=0, col=0)` | `showlcd()` 的别名 | `lcdtext("Hi", 0, 0)` |
| `lcdline(row, text, col=0)` | 按“行、文字、列”顺序显示 | `lcdline(1, "OK", 0)` |
| `lcdvalue(name, value, row=0, col=0)` | 显示名称和值 | `lcdvalue("light", 123, 0, 0)` |
| `lcdpass(name, detail="")` | 显示 PASS | `lcdpass("ADC")` |
| `lcdfail(name, detail="")` | 显示 FAIL | `lcdfail("UART")` |
| `lcdskip(name, detail="")` | 显示 SKIP | `lcdskip("PWM")` |
| `showguangmin(row=0, col=0)` | 显示光敏百分比 | `showguangmin()` |
| `showwenhumi(row=0, col=0)` | 显示温湿度，占两行 | `showwenhumi()` |
| `showjiasudu(row=0, col=0)` | 显示三轴加速度，占三行 | `showjiasudu()` |
| `showi2c(row=0, col=0)` | 显示 I2C 地址 | `showi2c()` |
| `showstatus(row=0, col=0)` | 显示状态并返回快照 | `showstatus()` |

### 串口选择、读取和写入

串口现在支持先决定使用哪个 UART，再读写：

| 函数 | 作用 | 示例 |
|---|---|---|
| `uart(1, uart_id=None, baudrate=None, timeout=None)` | 启用 UART，可同时指定编号和波特率 | `uart(1, 2, 115200)` |
| `setuart(uart_id, baudrate=115200, timeout=1000)` | 决定使用哪个串口并打开 | `setuart(2, 115200)` |
| `senduart(data)` | 写串口 | `senduart(b"hello")` |
| `readuart()` | 读当前已有串口数据，不等待 | `data = readuart()` |
| `waituart(timeout=10000)` | 等待串口数据 | `data = waituart(5000)` |

示例：

```python
from easy_api import *

setuart(2, 115200)
senduart(b"hello")
data = readuart()
data = waituart(5000)
```

## main.py 中编写持续轮询

`easy_api.py` 只提供“启用、读取、控制、测试”这类单次函数，不提供 `refresh()` 或 `loop()` 轮询函数。

`starter/main.py` 中只有 `main()` 是程序入口；如果看到 `api.xxx(...)`，
它就是在调用 `easy_api.py` 的公开接口。旧示例里的 `serial_title`、
`safe_call`、`show_page` 等名字不是 easy_api 接口，已经从正式入口移除。

如果题目要求“持续显示传感器数据”“持续检测按键”或“持续读取串口”，请在 `starter/main.py` 的 `main()` 函数中写 `while True:`。

示例：LCD 持续显示光敏值

```python
from easy_api import *

def main():
    init()
    lcd(1)
    guangmin(1)
    while True:
        i = readguangmin()
        clearlcd()
        showlcd("Light:", 0, 0)
        showlcd(i, 0, 8)
        delay(1000)

main()
```

示例：LCD 显示按键事件

```python
from easy_api import *

def main():
    init()
    lcd(1)
    anjian(1)

    while True:
        event = readanjian()
        if event:
            name, action = event
            clearlcd()
            showlcd(name, 0, 0)
            showlcd(action, 1, 0)
        delay(50)

main()
```

示例：UART 持续读取并回发

```python
from easy_api import *

def main():
    init()
    setuart(2, 115200)

    while True:
        data = readuart()
        if data:
            senduart(data)
        delay(20)

main()
```

注意：不要把持续轮询封装进 `easy_api.py`。比赛时只需要修改 `main.py` 里的组合逻辑。

理想的 `main.py` 内容：

```python
# -*- coding: utf-8 -*-
import easy_api as api


# 下面为参数区：比赛现场通常只需要改这里的数字。
DISPLAY_CYCLES = None      # 轮询次数；None 表示一直轮询。
REFRESH_MS = 1000          # 每轮间隔，单位 ms。
UART_ID = 2                # UART2；请按板卡丝印/原理图连接 TX 和 RX。
UART_BAUDRATE = 115200     # 串口波特率，需要和串口助手一致。
UART_TIMEOUT_MS = 1000     # 串口读取超时，单位 ms。


# 下面为模块启停区：1=开启，0=关闭；直接调用 easy_api，不再套 USE_xxx 开关。
api.init()                 # 初始化系统；会准备 easy_api 内部状态。
api.led(1)                 # LED；开启后可用 api.setled("red", 1) 控制红灯。
api.anjian(1)              # 按键；开启后可用 api.readanjian() / api.waitanjian()。
api.guangmin(1)            # 光敏 ADC；开启后可用 api.readguangmin()。
api.i2c(1)                 # I2C 总线；温湿度、加速度等 I2C 传感器会用到。
api.wenhumi(1)             # 温湿度 AHT20；开启后可用 api.readwendu() / api.readshidu()。
api.jiasudu(1)             # 三轴加速度 LIS2DH12；开启后可用 api.readx() / api.readyaxis() / api.readz()。
api.gpio(1)                # GPIO；需要按题目接线，可用 api.readgpio("D3") / api.setgpio(...)。
api.timer(1)               # 定时器；开启后可用 api.after(...) / api.every(...)。
api.pwm(1)                 # PWM；需要配置输出脚，可用 api.startpwm(...)。
api.fengmingqi(1)          # 蜂鸣器；需要在 config.py 配置蜂鸣器引脚。
api.lcd(1)                 # LCD；开启后可用 api.clearlcd() / api.showlcd(...)。
api.spi(1)                 # SPI；做回环测试时需要 MOSI 接 MISO。
api.uart(1)                # TTL UART；需要 TX/RX 交叉连接或接串口工具。
api.rs232(1)               # RS232；必须外接 RS232 电平转换模块。
api.rs485(1)               # RS485；必须外接 RS485 模块并配置方向控制脚。
api.cunchu(1)              # 存储；开启后可用 api.writefile(...) / api.readfile(...)。
api.yinpin(1)              # 音频；需要确认音频硬件后再使用录音/播放接口。
api.hmi(1)                 # HMI；LCD + 按键组合菜单能力。
api.lte(1)                 # 4G/LTE；开启后可用 api.readlte() 读取状态。
api.ble(1)                 # BLE；开启后可用 api.readble() / api.sendble(...)。
api.gnss(1)                # GNSS；开启后可用 api.readgnsslat() / api.readgnsslon()。
api.lbs(1)                 # LBS 基站定位；GNSS 没有坐标时可用作备用定位。

api.setuart(UART_ID, UART_BAUDRATE, UART_TIMEOUT_MS)


def main():
    loop = 0

    while DISPLAY_CYCLES is None or loop < DISPLAY_CYCLES:
        loop += 1

        # 以下为可能的轮询读取部分
        wendu = api.readwendu()
        shidu = api.readshidu()
        guangmin_value = api.readguangmin()
        x = api.readx()
        y = api.readyaxis()
        z = api.readz()
        uart_read_text = api.readuart()

        lte_read_text = api.readlte()
        ble_read_text = api.readble()
        location_data = api.readlocation()
        location_source = location_data.get("source") if location_data else "NONE"
        lat_text = location_data.get("latitude") if location_data else None
        lon_text = location_data.get("longitude") if location_data else None

        # 以下为可能的轮询 LCD 显示部分：保持直观写法，值跟在词组后面。
        api.showlcd("Light:", 0, 0)
        api.showlcd(guangmin_value, 0, 7)
        api.showlcd("T:", 1, 0)
        api.showlcd(wendu, 1, 3)
        api.showlcd("H:", 2, 0)
        api.showlcd(shidu, 2, 3)
        api.showlcd("x:", 3, 0)
        api.showlcd(x, 3, 3)
        api.showlcd("y:", 4, 0)
        api.showlcd(y, 4, 3)
        api.showlcd("z:", 5, 0)
        api.showlcd(z, 5, 3)
        api.showlcd("Lat:", 6, 0)
        api.showlcd(lat_text, 6, 5)
        api.showlcd("Lon:", 7, 0)
        api.showlcd(lon_text, 7, 5)

        # 以下为可能的轮询串口发送部分：标题和值分开发，更适合零基础用户照着改。
        api.senduart("Light:")
        api.senduart(guangmin_value)
        api.senduart(" T:")
        api.senduart(wendu)
        api.senduart(" H:")
        api.senduart(shidu)
        api.senduart(" x:")
        api.senduart(x)
        api.senduart(" y:")
        api.senduart(y)
        api.senduart(" z:")
        api.senduart(z)
        api.senduart(" LOC:")
        api.senduart(location_source)
        api.senduart(" Lat:")
        api.senduart(lat_text)
        api.senduart(" Lon:")
        api.senduart(lon_text)
        api.senduart(" UART:")
        api.senduart(uart_read_text)
        api.senduart(" LTE:")
        api.senduart(lte_read_text)
        api.senduart(" BLE:")
        api.senduart(ble_read_text)
        api.senduart("\r\n")

        # 以下为可能的用户写功能区
        if api.readgpio("D3") == 1:  # 可能的 GPIO 读取
            api.setled("red", 1)
            api.senduart("red on\r\n")
            # 当前 easy_api.after(...) 是延时后执行；如需真正非阻塞，应后续封装进 easy_api。
            api.after(1000, lambda: api.setled("red", 0))
            api.senduart("red off\r\n")

        event = api.readanjian()  # 可能的按键读取；不阻塞，适合放在轮询里。
        if event:
            name, action = event
            api.senduart(name)
            api.senduart(action)
            api.senduart("\r\n")

            if name == "up" and action == "press":
                api.senduart("up press\r\n")

        api.delay(REFRESH_MS)


if __name__ == "__main__":
    main()
```
