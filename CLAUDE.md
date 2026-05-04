# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

米家智能设备控制系统 — Flask + MySQL 应用，提供 Web UI、REST API（Flasgger 文档在 `/api/docs/`）、CLI、SocketIO 实时通信、MCP Server（AI Agent 工具）和 HomeKit 桥接。

底层依赖 `mijiaAPI` 包（v3.0+）与小米云端通信，通过 `app/utils/mijia_pool.py` 的 `MijiaAPIAdapter` 适配（从 DB 中的 auth_data 直接初始化，无文件 I/O）。

## Build, Test & Lint

```bash
python run.py                    # 启动开发服务器（SocketIO，端口 5000）
python -m mcp_server             # 启动 MCP Server（需 pip install -e ".[mcp]"）
python -m app.homekit            # 启动 HomeKit Bridge（需 pip install -e ".[homekit]"）
pytest -v                        # 运行测试
pytest tests/test_services/ -v   # 仅运行 service 层测试
ruff check .                     # Lint
ruff check --fix .               # Lint 自动修复
ruff format .                    # 格式化
```

## Database

- ORM: SQLAlchemy + Flask-Migrate（Alembic）
- MySQL（pymysql），测试库为 `mijia_test`
- 迁移：`flask db migrate -m "描述"` / `flask db upgrade`
- 连接池配置：`pool_recycle=3600`, `pool_pre_ping=True`

## Architecture

```
app/
├── __init__.py          # create_app() 工厂，注册扩展/蓝图/CLI/错误处理/安全头
├── extensions.py        # 单例扩展（db, migrate, jwt, csrf, limiter, socketio）
├── api/                 # REST API 蓝图（url_prefix=/api），JWT 认证
├── web/                 # Web UI 蓝图，Session+CSRF 认证
│   ├── routes.py        # 前端路由
│   ├── admin.py         # 管理后台
│   └── socketio.py      # SocketIO 事件
├── services/            # 业务逻辑层（不直接操作 HTTP request/response）
├── models/              # SQLAlchemy 模型
├── schemas/             # Marshmallow 序列化/校验
├── utils/               # MijiaAPIAdapter、统一响应格式、装饰器
├── cli/                 # Click CLI 命令
└── homekit/             # HomeKit Bridge（pyhap，设备映射 + 桥接启动）
mcp_server/              # MCP Server（FastMCP，通过 httpx 调用 Flask API）
config/                  # Flask 配置类（development/testing/production）
migrations/              # Alembic 迁移脚本
tests/                   # pytest 测试
```

## Key Conventions

- API 层只做参数校验和响应构造，业务逻辑放 `services/`
- 统一响应使用 `app/utils/response.py` 的 `success()` / `error()` 辅助函数
- API 认证：JWT（`@jwt_required()`）；Web 认证：Session + CSRF（Flask-Login + Flask-WTF）
- 限流：Flask-Limiter，默认 200/day、50/hour
- Ruff 配置：`line-length=120`，规则 `E, F, W, I`，目标 Python 3.9+

## Required Environment Variables

参见 `.env.example`：`FLASK_APP`, `FLASK_ENV`, `SECRET_KEY`, `DATABASE_URL`, `JWT_SECRET_KEY`, `GO2RTC_URL`

MCP Server / HomeKit Bridge 共用：
- `MIJIA_API_URL` — Flask API 地址（默认 `http://127.0.0.1:5000/api`）
- `MIJIA_TOKEN` — JWT Token，用于 MCP/HomeKit 调用 API

HomeKit Bridge 可选：
- `HOMEKIT_ENABLED` — 是否启用（默认 `false`）
- `HOMEKIT_PORT` — HAP 端口（默认 `51826`）
- `HOMEKIT_PIN` — 配对 PIN（默认 `123-45-678`）

## Gotchas

- `MijiaAPIAdapter` 从数据库中的 `auth_data` dict 初始化，不走文件 I/O — 不要改为文件路径方式
- SocketIO 使用 `async_mode="threading"`（非 eventlet 异步模式）
- 安全头在 `create_app()` 的 `_add_security_headers()` 中全局设置
- `mijiaAPI` 的 `execute_text_directive` 的 `quiet` 参数需要转为 `int`
- MCP Server 通过 `httpx.AsyncClient` 调用 Flask API，不走内部函数调用 — 两者是独立进程
- HomeKit 设备映射规则在 `app/homekit/mapper.py` 中硬编码（按 model 关键词匹配），非数据库配置
- `homekit_mapping.yaml` 路径是相对于 `app/homekit/` 目录解析的（`../../homekit_mapping.yaml`）
