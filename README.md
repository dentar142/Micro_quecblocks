# Micro_quecblocks

面向 **UniKnect EC200U 套件 / NUCLEO-F413ZH / QuecPython** 的离线 MicroBlocks 风格编程工作台。浏览器中的积木编辑器负责生成 `main.py`，板端 `runtime/starter/` 提供与硬件对应的 `easy_api` 运行库，导出的程序仍可在 Thonny 中上传和运行。

本仓库保存的是当前已验证的有效资源，不包含板端备份、Python 缓存、裁判生成样本或固件二进制。固件和 USB 驱动请使用与你的板卡和 EC200U 版本匹配的官方文件，并自行记录版本与 SHA-256。

## 新板第一次使用

### 1. 准备硬件和电脑

需要：

- UniKnect EC200U 套件和 USB 数据线；
- NUCLEO-F413ZH 上已烧录可启动的 QuecPython MicroPython 固件；
- ST-LINK 驱动和 Thonny；
- 如要使用 4G/GNSS，插入有效 SIM，并连接 EC200U 天线；GNSS 首次定位应在室外开阔环境完成。

运行仓库中的串口工具还需要电脑端 Python 和 `pyserial`：

```powershell
python -m pip install pyserial
```

先不要把 5V 信号接到 STM32 GPIO/ADC。RS232、RS485 必须使用对应电平转换器。

### 2. 确认串口

关闭其他串口软件，打开 Thonny，选择 MicroPython 解释器和实际出现的 ST-LINK 虚拟串口。端口号不是固定值；Windows 设备管理器中重新枚举后，以当前 COM 号为准。

在 Thonny REPL 确认：

```python
import sys
print(sys.implementation)
```

目标应显示 `micropython`，并包含 `NUCLEO-F413ZH` 或你的实际板型号。

### 3. 先上传运行库

不要只上传 `easy_api.py`。必须把 `runtime/starter/` 中的整个 Python 目录上传到开发板根目录，保持 `easy_api_parts/`、`lib/alg/` 和 `lib/kit/` 的目录结构。

最稳妥的方式是使用本仓库工具（先关闭 Thonny 的串口连接）：

```powershell
python tools\repl_backup_board.py --port COM19 --dest-root C:\2026soc\board_backups
python tools\repl_flash_verify.py --port COM19 --skip-verify
```

把 `COM19` 替换为设备管理器中实际的端口。第一条命令会把板端文件复制到本地备份目录；第二条命令通过 raw REPL 上传整个运行库。若只使用 Thonny，也要逐个上传 `runtime/starter/` 中的全部 `.py` 文件，不能漏掉 `easy_api_parts/30_io_display.py` 和 `easy_api_parts/60_radio.py`。

### 4. 验证运行库

在板端 REPL 执行：

```python
import easy_api as api
print(hasattr(api, "lcdfill"))
print(hasattr(api, "lcdrect"))
print(hasattr(api, "lcdcircle"))
print(hasattr(api, "readlte"))
print(hasattr(api, "networkstatus"))
print(api.api_version())  # 当前仓库应为 2026.08.10.1 或更高
print("readadc" in api.api_capabilities())
```

以上能力检查都应为 `True`，并且 `api.api_version()` 应为当前仓库版本。如果 `readadc` 为 `False`，说明板上仍是旧运行库；必须重新上传整个 `runtime/starter/`，不能只上传生成的 `main.py`。新生成的 `main.py` 也会在启动前自动检查所需 API，避免运行到中途才出现 `AttributeError`。

### 5. 打开积木工作台

项目只有一个编辑入口：`builder/easy_api_main_builder_microblocks.html`。所有积木、LCD 设计器、SDCard、4G/GNSS、代码生成、复制和下载功能都集成在这个单文件 HTML 中；旧的 `easy_api_main_builder_configured.html` 已移除，避免打开错误版本。

直接双击 `builder/easy_api_main_builder_microblocks.html` 即可离线打开，也可以在仓库目录启动静态服务器：

```powershell
python -m http.server 8878
```

浏览器访问 `http://127.0.0.1:8878/builder/easy_api_main_builder_microblocks.html`。

工作台提供：

- MicroBlocks 风格的积木选择器、脚本舞台、运行/停止和明暗主题；
- EC200U 启动模块独立开关；
- LCD 160×128 可视化画布，可编辑文字、矩形、线条、圆形的坐标、尺寸、粗细、颜色和填充；
- LCD 可从 SD/UFS 读取 RGB565 原始图片显示，主机端转换工具位于 `tools/rgb565_image.py`；
- 4G/LTE、GNSS、串口、传感器和 LCD 相关积木；
- 生成代码预览与 `main.py` 下载。

### 6. 导出并用 Thonny 烧录

在工作台点击“下载 `main.py`”，将文件保存到电脑。然后在 Thonny 中：

1. 选择板端解释器和实际 COM 口；
2. 打开导出的 `main.py`；
3. 点击运行或使用“上传到设备”；
4. 观察 REPL 中的 `[BOOT]`、`[LCD]`、`[LTE]` 和异常信息。

也可以使用工具完成字节校验和启动采样。工具要求源文件名为 `main.py`，因此将浏览器下载的文件改名或复制为 `main.py`：

```powershell
python tools\repl_upload_generated_main.py `
  --port COM19 `
  --source C:\path\to\main.py `
  --log C:\path\to\latest_main.log `
  --seconds 8
```

工具会比较本地与板端文件大小和 SHA-256，并捕获软复位后的启动输出。测试结束时出现由工具主动产生的 `KeyboardInterrupt` 属于预期现象；其他 traceback 需要处理。

## 4G、GNSS 数据的典型用法

生成的 QuecPython 代码使用 `easy_api`，例如：

```python
import easy_api as api

api.init()
api.lte(1)
status = api.networkstatus()
print("LTE", status)

api.gnss(1)
location = api.readlocation()
print("LOCATION", location)
```

`networkstatus()` 返回的是受固件能力约束的诊断快照；字段可能为空。GNSS 室内没有坐标是正常的，必须在室外等待卫星定位。不要把空坐标写成 `0,0`，应保留为空并通过串口记录失败原因。

## 目录

- `builder/`：离线 MicroBlocks 风格 HTML 编辑器。
- `runtime/starter/`：板端完整 QuecPython 运行库和示例入口。
- `tools/`：备份、raw REPL 上传、验证、主机测试和串口辅助工具。
- `examples/`：按 GPIO、传感器、LCD、UART、4G/GNSS 等功能拆分的示例。
- `host_tests/`：主机侧语法、接口和工作流契约测试。
- `docs/`：接口、接线、安全和零基础文档。
- `diagnostics/`：最小 LCD 诊断脚本模板；设备日志应保存在仓库外。

## 主机验证

在仓库根目录执行：

```powershell
python -B tools\run_host_tests.py
```

测试会编译运行库和示例，并检查编辑器中关键生成契约。当前基线应为 71 项通过。

## 许可证与第三方文件

本仓库的许可证见 `LICENSE`。固件、ST-LINK/Quectel/CP210x 驱动和 Thonny 安装包不随本仓库重新分发；请从官方来源获取，并遵守各自许可证。
