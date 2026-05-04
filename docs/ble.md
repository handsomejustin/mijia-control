# BLE 蓝牙传感器详细文档

## 概述

BLE 蓝牙传感器模块是 mijia-control 的一个独立守护进程，通过 PC 的蓝牙适配器直接接收小米 BLE 设备（如温湿度计）广播的传感器数据。无需额外的蓝牙网关硬件，PC 本身即可作为蓝牙网关使用。

该模块作为独立进程运行（类似 HomeKit Bridge），通过 HTTP API 将采集到的传感器数据上报到 Flask 主服务，实现数据展示、历史查询和自动化联动。

## 架构

```
┌──────────────────┐   BLE 广播包（被动扫描）  ┌──────────────────┐
│  小米 BLE 温度计   │ ─────────────────────→ │  BLE Scanner     │
│  LYWSD03MMC 等    │                        │  (bleak 扫描引擎) │
└──────────────────┘                         └────────┬─────────┘
                                                      │ AES-CCM 解密
                                                      │ 数据解析
                                                      ▼
                                              ┌───────────────┐
                                              │  数据上报      │
                                              │  HTTP POST     │
                                              └───────┬───────┘
                                                      │ Bearer Token
┌─────────────┐  查询/展示   ┌─────────────────────────▼──────────────┐
│  Web UI     │ ←────────── │           Flask API Server              │
│  CLI        │             │  /api/ble/devices/*                     │
│  MCP Agent  │             │                                         │
│  HomeKit    │             │  ┌─────────┐  ┌──────────────────────┐  │
└─────────────┘             │  │ DB 模型  │  │   自动化引擎          │  │
                            │  │ BLEDevice│  │ ble_sensor 触发类型  │  │
                            │  │ Reading  │  │ 温度阈值 → 控制设备   │  │
                            │  └─────────┘  └──────────────────────┘  │
                            └─────────────────────────────────────────┘
```

**关键设计决策**：

- **独立进程**：BLE Scanner 与 Flask 主服务隔离，互不影响，可独立重启
- **被动扫描**：只监听设备主动广播的数据包，不主动连接设备，功耗最低
- **AES 加密**：小米 BLE 设备广播数据经过 AES-CCM 加密，需要 bindkey 才能解密
- **可扩展解析器**：采用注册表模式，新增设备类型只需添加一个解析器类

## 支持的设备

### 首期支持

| 设备 | 型号 | 数据字段 |
|------|------|---------|
| 米家温湿度传感器迷你 | LYWSD03MMC (`xiaomi.sensor_ht.mini`) | 温度、湿度、电量 |

### 架构已支持（待实际测试）

| 设备 | 型号 | 数据字段 |
|------|------|---------|
| 米家温湿度传感器（圆形） | LYWSDCGQ | 温度、湿度、电量 |
| 米家温湿度传感器（新品） | MJWSD05MMC | 温度、湿度、电量 |

### 未来可扩展

解析器采用注册表模式，社区可以通过 PR 添加新设备支持：

- MCCGQ02HL — 门窗传感器（开/关状态、电量）
- RTCGQ02LM — 人体传感器（移动检测、光照、电量）
- SJWS01LM — 水浸传感器（水浸状态、电量）
- XMWXKG01YL — 无线开关（按键事件）

## 安装与配置

### 硬件要求

- PC 具备蓝牙功能（内置或 USB 蓝牙适配器）
- Windows 10/11（内置蓝牙协议栈，无需额外驱动）
- Linux 需要安装 BlueZ（`apt install bluez`）
- macOS 需要系统支持 BLE

### 安装

```bash
pip install -e ".[ble]"
```

会安装以下依赖：
- `bleak` >= 0.22 — 跨平台 BLE 扫描库
- `pycryptodome` >= 3.20 — AES 解密库
- `httpx` >= 0.27 — HTTP 客户端（与 Flask API 通信）

### 环境变量

BLE 守护进程复用 MCP Server / HomeKit Bridge 的认证配置：

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `MIJIA_TOKEN` | 无（必填） | JWT Token，通过 `mijia-control login` 获取 |
| `MIJIA_API_URL` | `http://127.0.0.1:5000/api` | Flask API 地址 |
| `BLE_ENABLED` | `false` | 是否启用（预留，当前不影响独立启动） |
| `BLE_ADAPTER` | 留空（自动选择） | 指定蓝牙适配器（Windows 通常不需要指定） |

在 `.env` 中添加：

```env
# BLE 蓝牙传感器（可选，需要 pip install -e ".[ble]"）
BLE_ENABLED=true
BLE_ADAPTER=
```

## 使用指南

### 第一步：确认 PC 蓝牙可用

确保 PC 的蓝牙功能已开启：

- **Windows**：设置 → 蓝牙和其他设备 → 确认蓝牙开关已打开
- **Linux**：`hciconfig hci0 up` 或确认系统设置中蓝牙已开启
- **macOS**：系统设置 → 蓝牙 → 确认已开启

### 第二步：发现 BLE 设备 MAC 地址

使用 CLI 扫描附近的 BLE 设备：

```bash
mijia-control ble scan
```

输出示例：

```json
[
  {"name": "LYWSD03MMC", "address": "A4:C1:38:XX:XX:XX"},
  {"name": "未知", "address": "AA:BB:CC:DD:EE:FF"}
]
```

记下你的温度计的 MAC 地址（如 `A4:C1:38:XX:XX:XX`）。

> **提示**：温度计需要在米家 APP 中已绑定。DID 可以在 Web UI 的设备列表中找到，格式为 `blt.3.xxxxx`。

### 第三步：注册 BLE 设备

```bash
mijia-control ble register \
  --did "blt.3.1otolfegp0k01" \
  --mac "A4:C1:38:XX:XX:XX"
```

系统会自动尝试从小米云端获取 bindkey（解密密钥）。如果自动获取失败，可以手动指定：

```bash
mijia-control ble register \
  --did "blt.3.1otolfegp0k01" \
  --mac "A4:C1:38:XX:XX:XX" \
  --bindkey "your-32-char-hex-bindkey"
```

> **如何手动获取 bindkey**：从 Android 手机的 `/sdcard/SmartHome/logs/plug_DeviceManager` 日志文件中搜索 BLE Token。

### 第四步：启动 BLE 守护进程

```bash
# 先启动 Web 服务（终端 1）
python run.py

# 启动 BLE 守护进程（终端 2）
python -m app.ble
```

成功启动后会看到类似日志：

```
2026-05-04 12:00:00 [app.ble.scanner] INFO: 正在加载目标设备列表...
2026-05-04 12:00:00 [app.ble.scanner] INFO: 已加载 1 台目标设备: ['A4:C1:38:XX:XX:XX']
2026-05-04 12:00:00 [app.ble.scanner] INFO: 开始 BLE 扫描 (adapter=default)...
2026-05-04 12:05:00 [app.ble.scanner] INFO: 设备 blt.3.1otolfegp0k01 (A4:C1:38:XX:XX:XX): temperature=25.3, humidity=62.1, battery=87
```

### 第五步：查看数据

**CLI 查询**：

```bash
# 列出所有 BLE 设备及最新读数
mijia-control ble list

# 查询历史读数
mijia-control ble readings "blt.3.1otolfegp0k01" --hours 24 --limit 50
```

**API 查询**：

```bash
# 获取所有 BLE 设备及最新读数
curl -H "Authorization: Bearer $MIJIA_TOKEN" \
  http://127.0.0.1:5000/api/ble/devices

# 查询历史读数
curl -H "Authorization: Bearer $MIJIA_TOKEN" \
  "http://127.0.0.1:5000/api/ble/devices/blt.3.1otolfegp0k01/readings?hours=24&limit=100"
```

**MCP Agent 查询**（通过 Claude Code / Hermes Agent 等）：

```
"查看蓝牙温度计的最新读数"
"列出所有蓝牙传感器设备"
"查询温度计最近24小时的历史数据"
```

## 自动化联动

BLE 传感器数据可以作为自动化规则的触发条件。例如：当房间温度高于 30°C 时自动开启空调。

### 创建 BLE 触发的自动化规则

通过 API 创建：

```bash
curl -X POST http://127.0.0.1:5000/api/automations \
  -H "Authorization: Bearer $MIJIA_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "温度过高开空调",
    "trigger_type": "ble_sensor",
    "trigger_config": {
      "did": "blt.3.1otolfegp0k01",
      "metric": "temperature",
      "operator": ">",
      "threshold": 30.0,
      "cooldown_seconds": 300
    },
    "action_type": "set_property",
    "action_config": {
      "did": "你的空调设备did",
      "prop_name": "power",
      "value": "on"
    }
  }'
```

### 触发条件说明

| 字段 | 说明 | 可选值 |
|------|------|--------|
| `metric` | 监测的指标 | `temperature`（温度）、`humidity`（湿度）、`battery`（电量） |
| `operator` | 比较运算符 | `>`、`>=`、`<`、`<=`、`==` |
| `threshold` | 阈值 | 数字（温度单位 °C，湿度单位 %，电量单位 %） |
| `cooldown_seconds` | 冷却时间 | 触发后多久内不再重复触发（秒），默认 300 |

### 自动化触发流程

```
温度计广播新数据 → BLE Scanner 解密上报 → BLEService.ingest_reading()
                                                  │
                                                  ▼
                                    检查所有 ble_sensor 类型的自动化规则
                                                  │
                                          匹配触发条件？
                                          ┌─────┴─────┐
                                          │ 是        │ 否
                                          ▼           ▼
                                    冷却期内？    跳过
                                    ┌─────┴─────┐
                                    │ 否        │ 是
                                    ▼           ▼
                              执行动作       跳过
                           （如：开空调）
```

## API 端点

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/ble/devices` | 列出所有已注册 BLE 设备（含最新读数） |
| POST | `/api/ble/devices` | 注册新 BLE 设备（`{"did": "...", "mac_address": "..."}`） |
| GET | `/api/ble/devices/<did>` | 查看指定 BLE 设备详情 |
| DELETE | `/api/ble/devices/<did>` | 删除 BLE 设备 |
| POST | `/api/ble/devices/<did>/readings` | 上报传感器数据（内部接口） |
| GET | `/api/ble/devices/<did>/readings` | 查询历史读数（`?hours=24&limit=200`） |
| POST | `/api/ble/devices/<did>/bindkey` | 重新获取/更新 bindkey |

## MCP 工具

| 工具 | 功能 | 示例 |
|------|------|------|
| `list_ble_devices` | 列出所有 BLE 设备及最新读数 | "列出蓝牙传感器" |
| `get_ble_sensor` | 获取指定 BLE 设备最新数据 | "查看温度计读数" |
| `get_ble_readings` | 查询历史读数 | "查看最近6小时的温湿度趋势" |

## CLI 命令

| 命令 | 说明 |
|------|------|
| `mijia-control ble scan` | 扫描附近 BLE 设备，发现 MAC 地址 |
| `mijia-control ble register --did <did> --mac <mac>` | 注册 BLE 设备 |
| `mijia-control ble list` | 列出 BLE 设备及最新读数 |
| `mijia-control ble readings <did> --hours 24` | 查询历史读数 |

## 数据存储

### 数据模型

**BLEDevice**（BLE 设备注册表）：

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键 |
| user_id | Integer | 所属用户 |
| did | String | 设备 ID（与 DeviceCache 关联） |
| mac_address | String | 蓝牙 MAC 地址 |
| bindkey | String | AES 解密密钥 |
| model | String | 设备型号 |
| capabilities | JSON | 能力标签 `["temperature", "humidity", "battery"]` |
| is_enabled | Boolean | 是否启用 |
| last_seen_at | DateTime | 最后收到数据时间 |

**BLESensorReading**（传感器读数）：

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键 |
| ble_device_id | Integer | 关联 BLEDevice |
| values | JSON | 读数值 `{"temperature": 25.3, "humidity": 62.1, "battery": 87}` |
| recorded_at | DateTime | 记录时间 |

## 调试指南

### 查看 BLE 扫描日志

BLE 守护进程启动时会输出详细日志：

```bash
python -m app.ble
```

日志级别说明：
- `INFO` — 正常数据接收、设备发现
- `WARNING` — bindkey 获取失败、解密失败、API 不可达
- `DEBUG` — 原始广播包内容、解密过程
- `ERROR` — 蓝牙适配器不可用

开启 DEBUG 日志：

```bash
# 修改 app/ble/__main__.py 中的 logging level
logging.basicConfig(level=logging.DEBUG, ...)
```

### 常见问题排查

#### 问题：启动时报 "BLE 适配器不可用"

**原因**：PC 蓝牙未开启或蓝牙适配器驱动异常。

**解决**：
1. Windows：设置 → 蓝牙和其他设备 → 打开蓝牙
2. 确认设备管理器中蓝牙适配器正常工作
3. 如使用 USB 蓝牙适配器，尝试重新插拔

#### 问题：注册设备时 bindkey 获取失败

**原因**：小米云端 API 可能不支持通过 mijiaAPI 直接获取 bindkey。

**解决**：
1. 从 Android 手机获取 bindkey：
   - 打开文件管理器，进入 `/sdcard/SmartHome/logs/plug_DeviceManager`
   - 搜索最新的日志文件，查找你的设备 MAC 地址对应的 BLE Token
2. 使用 `--bindkey` 参数手动指定：
   ```bash
   mijia-control ble register --did <did> --mac <mac> --bindkey <bindkey>
   ```

#### 问题：启动后一直收不到数据

**原因**：可能是 MAC 地址错误、bindkey 错误、或设备不在蓝牙范围内。

**排查步骤**：
1. 确认温度计在蓝牙范围内（10 米以内）
2. 确认 MAC 地址正确：`mijia-control ble scan` 检查
3. 查看日志中是否有 "解密失败" 的 WARNING
4. 如果连续解密失败，尝试重新获取 bindkey
5. 确认 Flask API 正在运行：`curl http://127.0.0.1:5000/api/ble/devices`

#### 问题：数据能收到但 API 上报失败

**原因**：Flask 服务未启动或 MIJIA_TOKEN 无效。

**解决**：
1. 确认 `python run.py` 正在运行
2. 确认 `MIJIA_TOKEN` 环境变量已设置且有效
3. 重新登录获取 token：`mijia-control login`

#### 问题：温度计在米家 APP 中显示但 DID 以 blt.3 开头

这是正常的。BLE 设备的 DID 格式为 `blt.3.xxxxx`（`blt` 代表 Bluetooth），系统已经兼容此格式。

### 验证数据完整性

```bash
# 检查数据库中的最新读数
mysql -u root -p mijia -e "
  SELECT d.did, d.mac_address, d.last_seen_at, r.values, r.recorded_at
  FROM ble_devices d
  LEFT JOIN ble_sensor_readings r ON r.ble_device_id = d.id
  ORDER BY r.recorded_at DESC
  LIMIT 10;
"
```

## 扩展新设备

要支持新的小米 BLE 设备类型，只需在 `app/ble/parser.py` 中添加一个新的解析器：

```python
@register_parser
class MCCGQ02HLParser(PayloadParser):
    """门窗传感器"""
    model = "mccgq02hl"
    capabilities = ["contact", "battery"]

    def parse(self, payload: bytes) -> dict:
        result = {}
        if len(payload) >= 1:
            result["contact_open"] = bool(payload[0])
        if len(payload) >= 4:
            result["battery"] = payload[3]
        return result
```

添加后重启 BLE 守护进程即可。注册设备的 `model` 字段需与解析器的 `model` 字段匹配。

## 平台兼容性

| 平台 | 蓝牙协议栈 | bleak 支持 | 状态 |
|------|-----------|-----------|------|
| Windows 10/11 | 内置 | 原生支持 | 已测试 |
| Linux (Ubuntu/Debian) | BlueZ | 原生支持 | 理论兼容 |
| macOS | CoreBluetooth | 原生支持 | 理论兼容 |
