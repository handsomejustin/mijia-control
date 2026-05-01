# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

米家智能设备控制系统 — Flask + MySQL 应用，提供 Web UI、REST API（Flasgger 文档在 `/api/docs/`）、CLI 和 SocketIO 实时通信。

底层依赖 `mijiaAPI` 包（v3.0+）与小米云端通信，通过 `app/utils/mijia_pool.py` 的 `MijiaAPIAdapter` 适配（从 DB 中的 auth_data 直接初始化，无文件 I/O）。

## Build, Test & Lint

```bash
python run.py                    # 启动开发服务器（SocketIO，端口 5000）
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
└── cli/                 # Click CLI 命令
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

## Gotchas

- `MijiaAPIAdapter` 从数据库中的 `auth_data` dict 初始化，不走文件 I/O — 不要改为文件路径方式
- SocketIO 使用 `async_mode="threading"`（非 eventlet 异步模式）
- 安全头在 `create_app()` 的 `_add_security_headers()` 中全局设置
- `mijiaAPI` 的 `execute_text_directive` 的 `quiet` 参数需要转为 `int`
