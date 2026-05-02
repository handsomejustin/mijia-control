# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Added

- **HomeKit Bridge** — 通过 HAP-Python 实现 Apple HomeKit 桥接，支持 iPhone/Mac 家庭 App 和 Siri 控制
  - Bridge 模式：所有米家设备作为单个桥接器暴露给 Apple 家庭
  - 支持 6 种设备类型：灯光、插座、开关、温湿度传感器、温控器、取暖器
  - 基于 spec_data 的智能属性发现（自动识别 brightness/color_temperature 等属性名）
  - 定时状态轮询（10 秒间隔），双向同步设备状态
- **HomeKit 设备映射扩展性** — 开源社区友好的设备映射系统
  - 基于 spec_data 的智能回退：当 model 未匹配内置规则时，自动从设备属性推断类型
  - 用户可覆盖的 YAML 配置文件（`homekit_mapping.yaml`），支持自定义映射和兜底策略
  - 内置 30+ 种米家设备型号的映射规则
  - 完整的单元测试覆盖（32 个测试用例）
- `homekit_mapping.yaml.example` — 带完整注释的配置模板
- `app/homekit/` 包：mapper.py、accessories.py、bridge.py、__init__.py、__main__.py
- `pyproject.toml` 新增 `[homekit]` 可选依赖组（HAP-python、httpx、pyyaml）
- `.env.example` 新增 HOMEKIT_ENABLED、HOMEKIT_PORT、HOMEKIT_PIN 配置项
- `config/__init__.py` 新增 HomeKit 相关配置项

## [0.1.0] - 2026-05-01

### Added

- **Web 管理界面** — 设备控制、家庭/场景管理、能耗统计、自动化规则、深色模式、移动端适配
- **RESTful API** — JWT 认证，完整的 Swagger 文档（`/api/docs/`），支持第三方集成
- **CLI 工具** — `mijia-control` 命令行，支持登录、设备列表、属性读写、场景执行
- **SocketIO 实时通信** — 推送设备状态变更
- **MCP Server** — 内置 MCP 协议支持，Claude Code / Hermes Agent 等 AI Agent 可直接调用
- **设备分组/收藏** — 自定义分组管理设备，快速收藏常用设备
- **定时自动化规则** — 支持 cron、interval、日出/日落等触发方式
- **能耗统计仪表板** — 按设备记录和展示能耗数据（日/小时粒度）
- **API Token 管理** — 为第三方应用创建和管理访问令牌
- **多用户 & 权限** — 用户注册登录、管理员后台、限流保护
- GitHub Actions CI 工作流（lint + smoke test）
- MCP Dockerfile（`Dockerfile.mcp`）
- Glama.ai MCP 目录集成和评分徽章
- MIT + GPL-3.0 双许可证

### Security

- 所有敏感配置移至 `.env` 环境变量
- CSRF 保护、限流保护、安全响应头
