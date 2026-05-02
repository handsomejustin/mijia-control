# MijiaPilot

**Mijia × MCP × AI Agent × HomeKit — The All-in-One Smart Home Bridge Platform.**

[中文](README.md) | English | [日本語](README_JA.md) | [한국어](README_KO.md) | [Español](README_ES.md)

[![MCP Server](https://glama.ai/mcp/servers/handsomejustin/mijia-control/badges/score.svg)](https://glama.ai/mcp/servers/handsomejustin/mijia-control)

> **Acknowledgements**: This project is built on top of [Do1e/mijia-api](https://github.com/Do1e/mijia-api) (mijiaAPI v3.0+),
> a Python SDK for communicating with Xiaomi Cloud for device control, property read/write, and scene execution.

## Demo

![Agent Demo](screenshot/1.png)

![Agent Demo Video](screenshot/demo.gif)

## Features

- **Web Dashboard** — Device control, home/scene management, energy monitoring, automation rules, dark mode, mobile responsive
- **RESTful API** — JWT authentication, full Swagger docs (`/api/docs/`), third-party integration ready
- **CLI Tool** — `mijia-control` command line: login, device listing, property read/write, scene execution
- **Real-time Communication** — SocketIO push for device status changes
- **Device Groups & Favorites** — Custom grouping, quick-access favorites
- **Scheduled Automation** — cron, interval, sunrise/sunset triggers
- **Energy Dashboard** — Per-device energy tracking (daily/hourly granularity)
- **API Token Management** — Create and manage access tokens for third-party apps
- **MCP Server** — Built-in MCP protocol support; Claude Code, Hermes Agent, and other AI Agents can control devices directly
- **HomeKit Bridge** — Control Mijia devices via Apple Home App and Siri; supports lights, outlets, sensors, thermostats, and more
- **Multi-user & Permissions** — User registration, admin panel, rate limiting

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Web Framework | Flask 3.0+ |
| ORM & Migrations | SQLAlchemy + Flask-Migrate (Alembic) |
| Database | MySQL (pymysql) |
| Auth | Flask-Login (Session) + Flask-JWT-Extended (API) |
| CSRF Protection | Flask-WTF |
| Rate Limiting | Flask-Limiter |
| Real-time | Flask-SocketIO |
| API Docs | Flasgger (Swagger UI) |
| Serialization | Marshmallow |
| Mijia SDK | [mijiaAPI](https://github.com/Do1e/mijia-api) >= 3.0 |
| MCP Protocol | [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk) >= 1.6 |
| HomeKit | [HAP-Python](https://github.com/ikalchev/HAP-python) >= 5.0 |
| Code Quality | Ruff (lint + format) |
| Testing | pytest |

## Project Structure

```
├── app/
│   ├── __init__.py          # Flask application factory
│   ├── extensions.py        # Extension instances (db, jwt, csrf, socketio...)
│   ├── api/                 # REST API blueprint (JWT auth)
│   ├── web/                 # Web UI blueprint (Session + CSRF auth)
│   ├── services/            # Business logic layer
│   ├── models/              # SQLAlchemy models
│   ├── schemas/             # Marshmallow serialization/validation
│   ├── utils/               # MijiaAPI adapter, response helpers, decorators
│   ├── cli/                 # Click CLI commands
│   └── homekit/             # HomeKit Bridge
├── mcp_server/              # MCP Server (AI Agent tools)
├── config/                  # Flask config (development/testing/production)
├── migrations/              # Alembic migration scripts
├── tests/                   # pytest tests
├── run.py                   # Dev server entry point
├── docs/                    # Detailed docs (HomeKit, API, etc.)
└── pyproject.toml           # Project config & dependencies
```

## Quick Start

### 1. Prerequisites

- Python 3.9+
- MySQL 5.7+

### 2. Install

```bash
git clone https://github.com/handsomejustin/mijia-control.git
cd mijia-control

python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

pip install -e ".[dev]"
```

### 3. Configure

Copy `.env.example` to `.env` and fill in your settings:

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

### 4. Initialize Database

```bash
mysql -u root -p -e "CREATE DATABASE mijia CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
flask db upgrade
```

### 5. Run

```bash
python run.py
```

Visit http://127.0.0.1:5000, register an account, and you're good to go.

## API Overview

| Module | Prefix | Description |
|--------|--------|-------------|
| Auth (Session) | `/api/auth/` | Register, login, logout, change password |
| Auth (JWT) | `/api/auth-jwt/` | JWT login, refresh token |
| Xiaomi Binding | `/api/xiaomi/` | QR code binding, status check, unbind |
| Devices | `/api/devices/` | List, read/write properties, actions, camera streams |
| Homes | `/api/homes/` | List homes, details |
| Scenes | `/api/scenes/` | List scenes, execute |
| Groups | `/api/groups/` | Group CRUD, favorites |
| Automations | `/api/automations/` | Scheduled rules CRUD, enable/disable |
| Energy | `/api/energy/` | Energy records, daily/hourly/latest |
| API Tokens | `/api/tokens/` | Token management for third-party integration |

Full API docs available at `/api/docs/` after starting the server.

## MCP Server (AI Agent Integration)

Built-in MCP Server — Claude Code, Hermes Agent, OpenClaw, and any MCP-compatible AI Agent can control Mijia devices directly.

### Install

```bash
pip install -e ".[mcp]"
```

### Configure

Ensure the Web service is running (`python run.py`), then obtain a token:

```bash
# Option 1: CLI login (recommended, auto-saves token)
mijia-control login

# Option 2: API login
curl -X POST http://127.0.0.1:5000/api/auth/jwt/login \
  -H "Content-Type: application/json" \
  -d '{"username": "your_username", "password": "your_password"}'
# The returned access_token is your MIJIA_TOKEN
```

Set environment variables:

```bash
# Linux / macOS
export MIJIA_API_URL=http://127.0.0.1:5000/api
export MIJIA_TOKEN=eyJhbGci...

# Windows (PowerShell)
$env:MIJIA_API_URL = "http://127.0.0.1:5000/api"
$env:MIJIA_TOKEN = "eyJhbGci..."

# Windows (CMD)
set MIJIA_API_URL=http://127.0.0.1:5000/api
set MIJIA_TOKEN=eyJhbGci...
```

### Use with Claude Code

```bash
# Register the MCP server
claude mcp add mijia -- python -m mcp_server

# Then use it in conversation:
# "Turn off the living room light"
# "Show all device online status"
# "Execute the 'Welcome Home' scene"
```

### Available Tools

| Tool | Function |
|------|----------|
| `list_devices` | List all devices |
| `get_device` | View device details & specs |
| `get_property` | Read device property |
| `set_property` | Set device property (control device) |
| `run_action` | Execute device action |
| `list_scenes` | List scenes |
| `run_scene` | Execute a scene |
| `list_homes` | List homes |
| `get_home` | View home details |

## HomeKit Bridge (Apple Home & Siri)

Bridge Mijia devices into Apple Home via HAP-Python — control them from the Home App and Siri on iPhone/Mac.

### Architecture

```
Apple Home / Siri  →  HomeKit Bridge (HAP-Python)  →  Flask REST API  →  Mijia Devices
                   Independent process, port 51826          python run.py
```

### Install

```bash
pip install -e ".[homekit]"
```

> **Windows users**: Install [Bonjour Print Services](https://developer.apple.com/bonjour/) or run the Bridge in Docker.

### Configure

Add to `.env` (or set as environment variables):

```env
HOMEKIT_ENABLED=true
HOMEKIT_PORT=51826
HOMEKIT_PIN=123-45-678
```

Ensure the Web service is running and you have a JWT Token (same `MIJIA_TOKEN` as MCP Server).

### Start

```bash
# Start the web service first
python run.py

# Start the HomeKit Bridge (another terminal)
python -m app.homekit
```

### Pairing

1. Ensure your phone and computer are on the **same local network**
2. iPhone → Home App → Add Device → scan the QR code shown in terminal, or enter the PIN manually
3. After pairing, devices appear under the "Mijia Smart Home" bridge

### iPhone Home App

<p align="center">
  <img src="screenshot/2.png" width="200" alt="HomeKit Home App - Device List">
  <img src="screenshot/3.png" width="200" alt="HomeKit Home App - Device Control">
</p>

### Supported Device Types

| HomeKit Type | Mijia Devices | Capabilities |
|---|---|---|
| Lightbulb | Bulbs, light strips | On/off, brightness, color temperature |
| Outlet | Plugs, smart switches | On/off |
| Switch | Robot vacuums, air purifiers | On/off |
| TemperatureSensor | Temp/humidity sensors | Temperature, humidity reading |
| Thermostat | AC partners, dehumidifiers | On/off, target temperature |
| HeaterCooler | Heaters | On/off, target temperature |

### Custom Device Mapping

When a device model isn't in the built-in rules, the Bridge auto-infers the type from spec_data. If the inference is wrong, create `homekit_mapping.yaml`:

```bash
cp homekit_mapping.yaml.example homekit_mapping.yaml
```

```yaml
# homekit_mapping.yaml
devices:
  zhimi.airp.mb4a: switch           # Exact model match
  lumi.sensor_magnet.aq2: ignored   # Ignore unwanted devices

fallback: auto    # auto=smart inference | switch=all as switch | ignore=ignore unknown
```

Available categories: `light`, `outlet`, `switch`, `temperature_sensor`, `thermostat`, `heater`, `camera`, `ignored`

## CLI Usage

After installing and activating the venv, the `mijia-control` command is available (no Flask context needed):

```bash
mijia-control --help                           # Show help
```

> Also available via Flask CLI: `flask mijia <command>`

**Cross-platform**: `pip install -e ".[dev]"` creates the appropriate executable:

| Platform | Path | Note |
|----------|------|------|
| Windows | `venv\Scripts\mijia-control.exe` | Available after activating venv |
| Linux / macOS | `venv/bin/mijia-control` | Available after activating venv |

**Optional: Global access (without activating venv)**

```bash
# Linux / macOS — create a symlink
sudo ln -s /path/to/mijia-control/venv/bin/mijia-control /usr/local/bin/mijia-control

# Windows — add to system PATH
# D:\path\to\mijia-control\venv\Scripts
```

### User Management

```bash
mijia-control login                            # Login (interactive)
mijia-control logout                           # Logout
mijia-control whoami                           # Show current user
mijia-control xiaomi status                    # Xiaomi account binding status
mijia-control xiaomi unlink                    # Unlink Xiaomi account
```

### Device Control

```bash
mijia-control device list                      # List devices
mijia-control device list --home-id <id>       # Filter by home
mijia-control device list --refresh            # Force refresh
mijia-control device show <did>                # Device details
mijia-control device get <did> <prop_name>     # Read property
mijia-control device set <did> <prop_name> <value>  # Set property
mijia-control device action <did> <action_name>     # Execute action
```

### Scenes & Homes

```bash
mijia-control scene list                       # List scenes
mijia-control scene list --refresh             # Force refresh
mijia-control scene run <scene_id>             # Execute scene
mijia-control home list                        # List homes
mijia-control home show <home_id>              # Home details
```

## Development

```bash
ruff check .           # Lint
ruff check --fix .     # Auto-fix
ruff format .          # Format
pytest -v              # Run tests
```

## License

This project is licensed under [GPL-3.0](https://www.gnu.org/licenses/gpl-3.0.html), inherited from the upstream [mijiaAPI](https://github.com/Do1e/mijia-api).
