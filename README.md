# MijiaPilot

[中文](README.md) | [English](README_EN.md) | [日本語](README_JA.md) | [한국어](README_KO.md) | [Español](README_ES.md)

[![MCP Server](https://glama.ai/mcp/servers/handsomejustin/mijia-control/badges/score.svg)](https://glama.ai/mcp/servers/handsomejustin/mijia-control)
[![GitHub license](https://img.shields.io/github/license/handsomejustin/mijia-control)](https://github.com/handsomejustin/mijia-control/blob/main/LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue)](https://www.python.org/)
[![Version](https://img.shields.io/badge/version-1.0.2-green)](https://github.com/handsomejustin/mijia-control)
[![Flask](https://img.shields.io/badge/Flask-3.0%2B-black)](https://flask.palletsprojects.com/)
[![GitHub stars](https://img.shields.io/github/stars/handsomejustin/mijia-control?style=social)](https://github.com/handsomejustin/mijia-control)
[![GitHub issues](https://img.shields.io/github/issues/handsomejustin/mijia-control)](https://github.com/handsomejustin/mijia-control/issues)
[![GitHub last commit](https://img.shields.io/github/last-commit/handsomejustin/mijia-control)](https://github.com/handsomejustin/mijia-control)

米家 × MCP × AI Agent × HomeKit 全桥接智能家居平台。

> **致谢**：本项目底层使用了 [Do1e/mijia-api](https://github.com/Do1e/mijia-api)（mijiaAPI v3.0+）提供的 Python SDK，
> 用于与小米云端进行设备通信、属性读写和场景执行。感谢原作者的开源贡献。

## 演示

![Agent 演示界面](screenshot/1.png)

![Agent 演示视频](screenshot/demo.gif)

## 功能特性

- **Web 管理界面** — 设备控制、家庭/场景管理、能耗统计、自动化规则、深色模式、移动端适配
- **RESTful API** — JWT 认证，完整的 Swagger 文档（`/api/docs/`），支持第三方集成
- **CLI 工具** — `mijia-control` 命令行，支持登录、设备列表、属性读写、场景执行
- **实时通信** — SocketIO 推送设备状态变更
- **设备分组/收藏** — 自定义分组管理设备，快速收藏常用设备
- **定时自动化规则** — 支持 cron、interval、日出/日落等触发方式
- **能耗统计仪表板** — 按设备记录和展示能耗数据（日/小时粒度）
- **API Token 管理** — 为第三方应用创建和管理访问令牌
- **MCP Server** — 内置 MCP 协议支持，Claude Code / Hermes Agent 等 AI Agent 可直接调用
- **HomeKit 桥接** — 通过 Apple 家庭 App 和 Siri 控制米家设备，支持灯光、插座、传感器、温控器等
- **BLE 蓝牙传感器** — PC 蓝牙直连小米 BLE 温湿度计，本地实时数据采集，支持自动化联动
- **多用户 & 权限** — 用户注册登录、管理员后台、限流保护

## 技术栈

| 层级 | 技术 |
|------|------|
| Web 框架 | Flask 3.0+ |
| ORM & 迁移 | SQLAlchemy + Flask-Migrate (Alembic) |
| 数据库 | MySQL (pymysql) |
| 认证 | Flask-Login (Session) + Flask-JWT-Extended (API) |
| CSRF 保护 | Flask-WTF |
| 限流 | Flask-Limiter |
| 实时通信 | Flask-SocketIO |
| API 文档 | Flasgger (Swagger UI) |
| 序列化/校验 | Marshmallow |
| 米家 SDK | [mijiaAPI](https://github.com/Do1e/mijia-api) >= 3.0 |
| MCP 协议 | [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk) >= 1.6 |
| HomeKit | [HAP-Python](https://github.com/ikalchev/HAP-python) >= 5.0 |
| BLE 扫描 | [bleak](https://github.com/hbldh/bleak) >= 0.22 |
| 代码质量 | Ruff (lint + format) |
| 测试 | pytest |

## 项目结构

```
├── app/
│   ├── __init__.py          # Flask 应用工厂
│   ├── extensions.py        # 扩展实例（db, jwt, csrf, socketio...）
│   ├── api/                 # REST API 蓝图 (JWT 认证)
│   ├── web/                 # Web UI 蓝图 (Session + CSRF 认证)
│   ├── services/            # 业务逻辑层
│   ├── models/              # SQLAlchemy 数据模型
│   ├── schemas/             # Marshmallow 序列化/校验
│   ├── utils/               # MijiaAPI 适配器、统一响应、装饰器
│   ├── cli/                 # Click CLI 命令
│   ├── homekit/             # HomeKit Bridge（Apple 家庭桥接）
│   └── ble/                 # BLE 蓝牙传感器守护进程（独立进程）
├── mcp_server/              # MCP Server（AI Agent 工具）
├── config/                  # Flask 配置（development/testing/production）
├── migrations/              # Alembic 数据库迁移脚本
├── tests/                   # pytest 测试
├── run.py                   # 开发服务器入口
├── docs/                    # 详细文档（HomeKit、API 等）
└── pyproject.toml           # 项目配置 & 依赖
```

## 快速开始

### 1. 环境准备

- Python 3.10+
- MySQL 5.7+

### 2. 安装

```bash
# 克隆本项目
git clone https://github.com/handsomejustin/mijia-control.git
cd mijia-control

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# 安装依赖（mijiaAPI 会作为依赖自动安装）
pip install -e ".[dev]"
```

### 3. 配置

复制 `.env.example` 为 `.env` 并填写实际配置：

```bash
cp .env.example .env
```

```env
FLASK_APP=app:create_app
FLASK_ENV=development
SECRET_KEY=your-secret-key-here
DATABASE_URL=mysql+pymysql://user:password@127.0.0.1:3306/mijia
JWT_SECRET_KEY=your-jwt-secret-key-here
GO2RTC_URL=http://127.0.0.1:1984
```

### 4. 初始化数据库

```bash
# 创建 MySQL 数据库
mysql -u root -p -e "CREATE DATABASE mijia CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"

# 执行迁移
flask db upgrade
```

### 5. 启动

```bash
python run.py
```

访问 http://127.0.0.1:5000 ，注册账号后即可使用。

## API 概览

| 模块 | 路径前缀 | 说明 |
|------|----------|------|
| 认证 (Session) | `/api/auth/` | 注册、登录、登出、修改密码 |
| 认证 (JWT) | `/api/auth-jwt/` | JWT 登录、刷新令牌 |
| 小米账号绑定 | `/api/xiaomi/` | 二维码绑定、状态查询、解绑 |
| 设备管理 | `/api/devices/` | 设备列表、属性读写、动作执行、摄像头流 |
| 家庭管理 | `/api/homes/` | 家庭列表、详情 |
| 场景执行 | `/api/scenes/` | 场景列表、执行 |
| 设备分组 | `/api/groups/` | 分组 CRUD、收藏管理 |
| 自动化规则 | `/api/automations/` | 定时规则 CRUD、启用/禁用 |
| 能耗统计 | `/api/energy/` | 能耗记录、日/小时/最新查询 |
| BLE 传感器 | `/api/ble/` | BLE 设备注册、数据上报、历史查询 |
| API Token | `/api/tokens/` | 令牌管理（第三方集成） |

完整 API 文档：启动后访问 `/api/docs/`。

## MCP Server（AI Agent 集成）

内置 MCP Server，支持 Claude Code、Hermes Agent、OpenClaw 等任何兼容 MCP 协议的 AI Agent 直接控制米家设备。

### 安装

```bash
pip install -e ".[mcp]"
```

### 配置

首先确保 Web 服务已启动（`python run.py`），然后获取 Token：

```bash
# 方式一：CLI 登录（推荐，自动保存 Token）
mijia-control login

# 方式二：API 登录获取
curl -X POST http://127.0.0.1:5000/api/auth/jwt/login \
  -H "Content-Type: application/json" \
  -d '{"username": "你的用户名", "password": "你的密码"}'
# 返回的 access_token 即为 MIJIA_TOKEN
```

设置环境变量：

```bash
# Linux / macOS
export MIJIA_API_URL=http://127.0.0.1:5000/api
export MIJIA_TOKEN=eyJhbGci...   # 上一步获取的 access_token

# Windows (PowerShell)
$env:MIJIA_API_URL = "http://127.0.0.1:5000/api"
$env:MIJIA_TOKEN = "eyJhbGci..."

# Windows (CMD)
set MIJIA_API_URL=http://127.0.0.1:5000/api
set MIJIA_TOKEN=eyJhbGci...
```

### Claude Code 中使用

```bash
# 注册 MCP 服务器
claude mcp add mijia -- python -m mcp_server

# 之后在对话中直接使用
# "帮我把客厅的灯关掉"
# "查看所有设备的在线状态"
# "执行回家场景"
```

### 可用工具

| 工具 | 功能 |
|------|------|
| `list_devices` | 列出所有设备 |
| `get_device` | 查看设备详情与规格 |
| `get_property` | 读取设备属性 |
| `set_property` | 设置设备属性（控制设备） |
| `run_action` | 执行设备动作 |
| `list_scenes` | 列出场景 |
| `run_scene` | 执行场景 |
| `list_homes` | 列出家庭 |
| `get_home` | 查看家庭详情 |
| `list_ble_devices` | 列出 BLE 传感器设备 |
| `get_ble_sensor` | 获取 BLE 传感器最新数据 |
| `get_ble_readings` | 查询 BLE 传感器历史读数 |

## HomeKit Bridge（Apple 家庭 & Siri 控制）

通过 HAP-Python 实现 HomeKit 桥接，让 iPhone、Mac 用户在 Apple 家庭 App 和 Siri 中直接控制米家设备。

### 架构

```
Apple 家庭 / Siri  →  HomeKit Bridge (HAP-Python)  →  Flask REST API  →  米家设备
                    独立进程，端口 51826                  python run.py
```

### 安装

```bash
pip install -e ".[homekit]"
```

> **Windows 用户**：需要安装 [Bonjour Print Services](https://developer.apple.com/bonjour/) 或使用 Docker 运行 Bridge。

### 配置

在 `.env` 中添加（或直接设置环境变量）：

```env
HOMEKIT_ENABLED=true
HOMEKIT_PORT=51826
HOMEKIT_PIN=123-45-678
```

确保 Web 服务已启动并获取 JWT Token（与 MCP Server 相同的 `MIJIA_TOKEN`）。

### 启动

```bash
# 先启动 Web 服务
python run.py

# 再启动 HomeKit Bridge（另一个终端）
python -m app.homekit
```

### 配对

1. 确保手机和电脑在同一局域网
2. iPhone → 家庭 App → 添加设备 → 扫描终端显示的 QR 码，或手动输入 PIN
3. 配对成功后，设备会以「米家智能家居」桥接器的形式出现

### iPhone 家庭 App 效果

<p align="center">
  <img src="screenshot/2.png" width="200" alt="HomeKit 家庭 App - 设备列表">
  <img src="screenshot/3.png" width="200" alt="HomeKit 家庭 App - 设备控制">
</p>

### 支持的设备类型

| HomeKit 类型 | 米家设备 | 控制能力 |
|---|---|---|
| Lightbulb | 灯泡、灯带 | 开关、亮度、色温 |
| Outlet | 插座、智能开关 | 开关 |
| Switch | 扫地机、净化器等 | 开关 |
| TemperatureSensor | 温湿度传感器 | 温度、湿度读取 |
| Thermostat | 空调伴侣、除湿机 | 开关、目标温度 |
| HeaterCooler | 取暖器 | 开关、目标温度 |

### 设备映射自定义

当你的设备型号不在内置规则中时，Bridge 会自动从设备的 spec_data 推断类型。如果推断不准确，可以创建 `homekit_mapping.yaml` 自定义映射：

```bash
cp homekit_mapping.yaml.example homekit_mapping.yaml
```

```yaml
# homekit_mapping.yaml
devices:
  zhimi.airp.mb4a: switch           # 精确 model 匹配
  lumi.sensor_magnet.aq2: ignored   # 忽略不需要的设备

fallback: auto    # auto=智能推断 | switch=全部当开关 | ignore=忽略未知
```

可用类别：`light`、`outlet`、`switch`、`temperature_sensor`、`thermostat`、`heater`、`camera`、`ignored`

## BLE 蓝牙传感器（本地蓝牙数据采集）

通过 PC 蓝牙直连小米 BLE 温湿度计等传感器，无需额外蓝牙网关硬件。支持数据展示、历史查询和自动化联动。

### 架构

```
BLE 温度计  ─BLE 广播→  BLE Scanner (独立进程)  ─HTTP POST→  Flask API  →  DB
                         python -m app.ble                        python run.py
```

### 安装

```bash
pip install -e ".[ble]"
```

> 需要 PC 具备蓝牙功能（Windows 10/11 内置支持，无需额外驱动）。

### 配置

在 `.env` 中添加：

```env
BLE_ENABLED=true
```

确保已设置 `MIJIA_TOKEN`（与 MCP Server / HomeKit Bridge 相同）。

### 使用步骤

```bash
# 1. 扫描附近 BLE 设备，发现 MAC 地址
mijia-control ble scan

# 2. 注册 BLE 设备（自动从云端获取解密密钥）
mijia-control ble register --did "blt.3.xxxxx" --mac "A4:C1:38:XX:XX:XX"

# 3. 启动 BLE 守护进程（需要先启动 Web 服务）
python run.py           # 终端 1
python -m app.ble       # 终端 2

# 4. 查看数据
mijia-control ble list
mijia-control ble readings "blt.3.xxxxx" --hours 24
```

### 支持的设备

| 设备 | 型号 | 数据 |
|------|------|------|
| 米家温湿度传感器迷你 | LYWSD03MMC | 温度、湿度、电量 |
| 米家温湿度传感器（圆形） | LYWSDCGQ | 温度、湿度、电量 |
| 米家温湿度传感器（新品） | MJWSD05MMC | 温度、湿度、电量 |

### 自动化联动

BLE 传感器数据可触发自动化规则，例如温度 > 30°C 自动开空调：

```bash
curl -X POST http://127.0.0.1:5000/api/automations \
  -H "Authorization: Bearer $MIJIA_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "温度过高开空调",
    "trigger_type": "ble_sensor",
    "trigger_config": {
      "did": "blt.3.xxxxx",
      "metric": "temperature",
      "operator": ">",
      "threshold": 30.0,
      "cooldown_seconds": 300
    },
    "action_type": "set_property",
    "action_config": {"did": "空调did", "prop_name": "power", "value": "on"}
  }'
```

📖 **详细文档**：[docs/ble.md](docs/ble.md) — 包含架构说明、安装配置、调试指南、故障排除、扩展新设备等完整内容。

## CLI 使用

安装并激活虚拟环境后，可直接使用 `mijia-control` 命令（无需 Flask 上下文）：

```bash
mijia-control --help                           # 查看帮助
```

> 也可通过 Flask CLI 调用：`flask mijia <command>`

**跨平台说明：** `pip install -e ".[dev]"` 会自动创建平台对应的可执行入口：

| 平台 | 入口路径 | 说明 |
|------|----------|------|
| Windows | `venv\Scripts\mijia-control.exe` | 激活 venv 后直接可用 |
| Linux / macOS | `venv/bin/mijia-control` | 激活 venv 后直接可用 |

**可选：全局使用（不激活 venv）**

```bash
# Linux / macOS — 创建软链接
sudo ln -s /path/to/mijia-control/venv/bin/mijia-control /usr/local/bin/mijia-control

# Windows — 将以下路径添加到系统 PATH 环境变量
# D:\path\to\mijia-control\venv\Scripts
```

### 用户管理

```bash
mijia-control login                            # 登录（交互式输入用户名密码）
mijia-control logout                           # 退出登录
mijia-control whoami                           # 查看当前用户
mijia-control xiaomi status                    # 查看小米账号绑定状态
mijia-control xiaomi unlink                    # 解绑小米账号
```

### 设备控制

```bash
mijia-control device list                      # 列出设备
mijia-control device list --home-id <id>       # 按家庭筛选
mijia-control device list --refresh            # 强制刷新设备列表
mijia-control device show <did>                # 查看设备详情
mijia-control device get <did> <prop_name>     # 读取设备属性
mijia-control device set <did> <prop_name> <value>  # 设置设备属性
mijia-control device action <did> <action_name>     # 执行设备动作
```

### 场景 & 家庭

```bash
mijia-control scene list                       # 列出场景
mijia-control scene list --refresh             # 强制刷新
mijia-control scene run <scene_id>             # 执行场景
mijia-control home list                        # 列出家庭
mijia-control home show <home_id>              # 查看家庭详情
```

### BLE 蓝牙传感器

```bash
mijia-control ble scan                          # 扫描附近 BLE 设备
mijia-control ble register --did <did> --mac <mac>  # 注册 BLE 设备
mijia-control ble list                          # 列出 BLE 设备及最新读数
mijia-control ble readings <did> --hours 24     # 查询历史读数
```

## 开发

```bash
# Lint
ruff check .

# 自动修复
ruff check --fix .

# 格式化
ruff format .

# 运行测试
pytest -v
```

## 许可证

本项目基于 [GPL-3.0](https://www.gnu.org/licenses/gpl-3.0.html) 许可证开源，继承自上游 [mijiaAPI](https://github.com/Do1e/mijia-api) 的许可协议。
