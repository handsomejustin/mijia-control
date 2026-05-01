# 米家 Web + CLI + API

基于 Flask 的米家智能家居设备管理平台，提供 Web UI、REST API、CLI 和 SocketIO 实时通信等多种控制接口。

> **致谢**：本项目底层使用了 [Do1e/mijia-api](https://github.com/Do1e/mijia-api)（mijiaAPI v3.0+）提供的 Python SDK，
> 用于与小米云端进行设备通信、属性读写和场景执行。感谢原作者的开源贡献。

## 演示

![Agent 演示界面](screenshot/1.png)

[▶ 观看演示视频](screenshot/2.mp4)

## 功能特性

- **Web 管理界面** — 设备控制、家庭/场景管理、能耗统计、自动化规则、深色模式、移动端适配
- **RESTful API** — JWT 认证，完整的 Swagger 文档（`/api/docs/`），支持第三方集成
- **CLI 工具** — `mijia-control` 命令行，支持登录、设备列表、属性读写、场景执行
- **实时通信** — SocketIO 推送设备状态变更
- **设备分组/收藏** — 自定义分组管理设备，快速收藏常用设备
- **定时自动化规则** — 支持 cron、interval、日出/日落等触发方式
- **能耗统计仪表板** — 按设备记录和展示能耗数据（日/小时粒度）
- **API Token 管理** — 为第三方应用创建和管理访问令牌
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
│   └── cli/                 # Click CLI 命令
├── config/                  # Flask 配置（development/testing/production）
├── migrations/              # Alembic 数据库迁移脚本
├── tests/                   # pytest 测试
├── run.py                   # 开发服务器入口
└── pyproject.toml           # 项目配置 & 依赖
```

## 快速开始

### 1. 环境准备

- Python 3.9+
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
| API Token | `/api/tokens/` | 令牌管理（第三方集成） |

完整 API 文档：启动后访问 `/api/docs/`。

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
