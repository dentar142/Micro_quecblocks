# 离线资产清单

赛前将以下资产放入 `offline-assets/`，并补充实际文件名、版本和 SHA-256。

| 类别 | 必需性 | 示例文件 | 状态 | 说明 |
|---|---:|---|---|---|
| Thonny | 必需 | `Thonny-4.1.7.zip` | 已在 `../tools/` 中存在 | MicroPython IDE 与文件上传 |
| MCU 固件 | 必需 | `UniKnect_MicroPython_F413ZH_v*.hex` | 待补齐 | NUCLEO-F413ZH MicroPython 固件 |
| ST-LINK 驱动 | 必需 | `stsw-link009.zip` | 待补齐 | 固件烧录与虚拟串口 |
| STM32CubeProgrammer | 必需 | `STM32CubeProgrammer-*.zip` | 待补齐 | 离线烧录工具 |
| CP210x 驱动 | 必需 | `CP210x_Universal_Windows_Driver.zip` | 待补齐 | UniKnect USB-TTL 调试口 |
| Quectel USB 驱动 | 可选 | `Quectel_Windows_USB_Driver*.zip` | 待补齐 | 4G 模组 AT/Log 端口 |
| USB-TTL 工具 | 可选 | `serial-terminal-*` | 待确认 | 裁判 PC 串口辅助测试 |

## 固件内置模块要求

当前基础库假设所选 UniKnect MicroPython 固件已经内置以下模块：

- `machine`
- `st7735`
- `ahtx0`
- `lis2dh12`
- `quectel`

赛前必须在开发板上运行 `examples/09_preflight.py`。任一模块缺失时，应更换固件，或将合法可分发的纯 Python 驱动加入离线包。

如果许可证不允许重分发某个安装包，请在赛前电脑镜像中预装，并在本表标记为“预装”。
