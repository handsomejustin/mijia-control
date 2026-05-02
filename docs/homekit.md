# HomeKit Bridge 详细文档

## 概述

HomeKit Bridge 是 mijia-control 的一个独立桥接服务，将米家智能设备暴露给 Apple HomeKit 生态。用户可以在 iPhone/Mac 的「家庭」App 中直接看到和控制米家设备，也可以通过 Siri 进行语音控制。

## 架构

```
┌──────────────────────┐
│  Apple Home / Siri   │
└──────────┬───────────┘
           │ HAP Protocol (mDNS + HTTP, 端口 51826)
┌──────────▼───────────┐
│  HomeKit Bridge      │  ← 独立进程 (python -m app.homekit)
│  (HAP-Python Bridge) │
│                      │
│  内含多个 Accessory:  │
│  - Lightbulb         │
│  - Outlet            │
│  - Switch            │
│  - TemperatureSensor │
│  - Thermostat        │
│  - HeaterCooler      │
└──────────┬───────────┘
           │ HTTP REST API (httpx 同步调用)
┌──────────▼───────────┐
│  Flask API Server    │  ← python run.py (端口 5000)
│  /api/devices/...    │
└──────────────────────┘
```

Bridge 作为独立进程运行，不和 Flask 共用进程，避免 HAP 的 asyncio 事件循环和 Flask 的线程模型冲突。

## 设备映射系统

Bridge 使用三级映射策略来确定每个米家设备对应的 HomeKit 类型：

### 1. 用户自定义规则（最高优先级）

通过 `homekit_mapping.yaml` 文件定义，精确匹配设备 model：

```yaml
devices:
  zhimi.airp.mb4a: switch
  lumi.sensor_magnet.aq2: ignored
```

### 2. 内置 Model 规则

基于设备 model 字符串的子串匹配，内置 30+ 种常见型号：

| 关键词 | 类型 |
|--------|------|
| yeelink.light, philips.light, mijia.light | Light |
| chuangmi.plug, zimi.plug, lumi.switch | Outlet |
| zhimi.airpurifier, roborock.vacuum | Switch |
| acpartner, aircondition, derh | Thermostat |
| heater | Heater |
| ht.sen, weather.v1, sensor_ht | Temperature Sensor |
| chuangmi.camera, isa.camera | Camera |
| router, cardvr, kettle | Ignored |

### 3. Spec Data 智能推断

当 model 未匹配任何规则时，分析设备的 spec_data 属性列表自动推断：

| 属性组合 | 推断类型 |
|----------|----------|
| 有 `brightness` | Light |
| 有 `temperature` + `target-temperature` + `power` | Thermostat |
| 有 `temperature` + `target-temperature` | Heater |
| 有 `temperature`/`humidity`，无 `power` | Temperature Sensor |
| 有 `power`/`on`/`switch` | Switch |
| 无法推断 | 按兜底策略处理（默认 Switch） |

### 兜底策略

在 `homekit_mapping.yaml` 中配置：

```yaml
fallback: auto    # auto=从 spec_data 推断（默认）
                  # switch=未知设备全部映射为开关
                  # ignore=忽略未知设备
```

## 安装与配置

### 安装

```bash
pip install -e ".[homekit]"
```

会安装以下依赖：
- `HAP-python[QRCode]` >= 5.0 — HomeKit 协议实现
- `httpx` >= 0.27 — HTTP 客户端
- `pyyaml` >= 6.0 — YAML 配置解析

### 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `MIJIA_TOKEN` | 无（必填） | JWT Token，通过 `mijia-control login` 获取 |
| `MIJIA_API_URL` | `http://127.0.0.1:5000/api` | Flask API 地址 |
| `HOMEKIT_PORT` | `51826` | HAP 服务端口 |
| `HOMEKIT_PIN` | `123-45-678` | 配对 PIN 码 |

### 启动

```bash
# 终端 1：启动 Web 服务
python run.py

# 终端 2：启动 HomeKit Bridge
python -m app.homekit
```

启动后会显示 QR 码和 PIN，用 iPhone 家庭 App 扫描即可配对。

### 平台注意事项

- **macOS / Linux**：需要安装 Avahi（`apt install avahi-daemon` 或 `brew install avahi`）
- **Windows**：需要安装 Bonjour Print Services，或使用 Docker 运行
- 配对信息保存在 `homekit.state` 文件中，删除此文件需要重新配对

## 支持的设备类型

### Lightbulb（灯光）

支持的属性：
- `On` — 开关（从 `on`/`power`/`switch` 属性自动发现）
- `Brightness` — 亮度（从 `brightness` 属性）
- `ColorTemperature` — 色温（从 `color_temperature`/`color-temp`/`color_temp` 属性，可选）

### Outlet（插座）

支持的属性：
- `On` — 开关
- `OutletInUse` — 在使用中（跟随开关状态）

### Switch（通用开关）

支持的属性：
- `On` — 开关

适用于扫地机、空气净化器等只需开关控制的设备。

### TemperatureSensor（温湿度传感器）

支持的属性：
- `CurrentTemperature` — 当前温度
- `CurrentRelativeHumidity` — 当前湿度（可选）

### Thermostat（温控器）

支持的属性：
- `CurrentTemperature` — 当前温度
- `TargetTemperature` — 目标温度
- `CurrentHeatingCoolingState` — 当前状态
- `TargetHeatingCoolingState` — 目标状态

### HeaterCooler（取暖器）

支持的属性：
- `Active` — 激活状态
- `CurrentTemperature` — 当前温度
- `HeatingThresholdTemperature` — 加热阈值温度

## 状态同步

- **HomeKit → 米家**：实时（通过 setter_callback 直接调用 API）
- **米家 → HomeKit**：轮询模式，每 10 秒读取一次设备属性
- 状态同步延迟约 3-10 秒

## 故障排除

### Bridge 启动失败

- 检查 `MIJIA_TOKEN` 是否已设置且有效
- 检查 Flask API 是否已启动（`python run.py`）
- 检查端口 51826 是否被占用

### iPhone 找不到设备

- 确保手机和电脑在同一局域网
- Windows 用户确认已安装 Bonjour
- 尝试手动输入 PIN 码

### 设备映射错误

1. 查看 Bridge 启动日志中的映射结果
2. 如需调整，创建 `homekit_mapping.yaml` 并指定正确的类别
3. 修改后重启 Bridge 即可生效

### 500 错误

- 检查设备是否在线
- 检查属性名是否正确（查看日志中实际请求的属性名）
- 某些设备属性名与通用名称不同，需要通过 spec_data 自动发现
