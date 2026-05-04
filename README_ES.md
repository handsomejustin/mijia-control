# MijiaPilot

**Mijia × MCP × AI Agent × HomeKit — La plataforma puente todo-en-uno para el hogar inteligente.**

[中文](README.md) | [English](README_EN.md) | [日本語](README_JA.md) | [한국어](README_KO.md) | Español

[![MCP Server](https://glama.ai/mcp/servers/handsomejustin/mijia-control/badges/score.svg)](https://glama.ai/mcp/servers/handsomejustin/mijia-control)

> **Agradecimientos**: Este proyecto está construido sobre [Do1e/mijia-api](https://github.com/Do1e/mijia-api) (mijiaAPI v3.0+),
> un SDK de Python para comunicarse con Xiaomi Cloud, controlar dispositivos, leer/escribir propiedades y ejecutar escenas.

## Demo

![Demo de Agent](screenshot/1.png)

![Video de demostración](screenshot/demo.gif)

## Características

- **Panel Web** — Control de dispositivos, gestión de hogares/escenas, monitorización de energía, reglas de automatización, modo oscuro, diseño adaptable a móviles
- **API RESTful** — Autenticación JWT, documentación Swagger completa (`/api/docs/`), integración con terceros
- **Herramienta CLI** — Línea de comandos `mijia-control`: inicio de sesión, listado de dispositivos, lectura/escritura de propiedades, ejecución de escenas
- **Comunicación en tiempo real** — Notificaciones push de cambios de estado de dispositivos vía SocketIO
- **Grupos y favoritos** — Agrupación personalizada, acceso rápido a favoritos
- **Automatización programada** — Disparadores cron, intervalos, amanecer/atardecer
- **Panel de energía** — Seguimiento de energía por dispositivo (granularidad diaria/horaria)
- **Gestión de tokens API** — Creación y gestión de tokens de acceso para aplicaciones de terceros
- **Servidor MCP** — Soporte integrado del protocolo MCP; Claude Code, Hermes Agent y otros Agentes IA pueden controlar dispositivos directamente
- **Puente HomeKit** — Control de dispositivos Mijia desde la app Hogar de Apple y Siri; compatible con luces, enchufes, sensores, termostatos y más
- **Sensores BLE Bluetooth** — Conexión directa via Bluetooth del PC a termómetros Xiaomi BLE, recopilación de datos local en tiempo real, disparadores de automatización
- **Multiusuario y permisos** — Registro de usuarios, panel de administración, limitación de solicitudes

## Stack Tecnológico

| Capa | Tecnología |
|------|-----------|
| Framework Web | Flask 3.0+ |
| ORM y Migraciones | SQLAlchemy + Flask-Migrate (Alembic) |
| Base de Datos | MySQL (pymysql) |
| Autenticación | Flask-Login (Sesión) + Flask-JWT-Extended (API) |
| Protección CSRF | Flask-WTF |
| Limitación | Flask-Limiter |
| Tiempo Real | Flask-SocketIO |
| Documentación API | Flasgger (Swagger UI) |
| Serialización | Marshmallow |
| SDK Mijia | [mijiaAPI](https://github.com/Do1e/mijia-api) >= 3.0 |
| Protocolo MCP | [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk) >= 1.6 |
| HomeKit | [HAP-Python](https://github.com/ikalchev/HAP-python) >= 5.0 |
| Escaneo BLE | [bleak](https://github.com/hbldh/bleak) >= 0.22 |
| Calidad de Código | Ruff (lint + formato) |
| Tests | pytest |

## Estructura del Proyecto

```
├── app/
│   ├── __init__.py          # Fábrica de aplicaciones Flask
│   ├── extensions.py        # Instancias de extensiones (db, jwt, csrf, socketio...)
│   ├── api/                 # Blueprint REST API (auth JWT)
│   ├── web/                 # Blueprint Web UI (Sesión + CSRF)
│   ├── services/            # Capa de lógica de negocio
│   ├── models/              # Modelos SQLAlchemy
│   ├── schemas/             # Serialización/validación Marshmallow
│   ├── utils/               # Adaptador MijiaAPI, helpers de respuesta, decoradores
│   ├── cli/                 # Comandos Click CLI
│   ├── homekit/             # Puente HomeKit
│   └── ble/                 # Demonio de sensores BLE Bluetooth (proceso independiente)
├── mcp_server/              # Servidor MCP (herramientas para Agentes IA)
├── config/                  # Configuración Flask (development/testing/production)
├── migrations/              # Scripts de migración Alembic
├── tests/                   # Tests pytest
├── run.py                   # Punto de entrada del servidor de desarrollo
├── docs/                    # Documentación detallada
└── pyproject.toml           # Configuración del proyecto y dependencias
```

## Inicio Rápido

### 1. Requisitos Previos

- Python 3.10+
- MySQL 5.7+

### 2. Instalación

```bash
git clone https://github.com/handsomejustin/mijia-control.git
cd mijia-control

python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

pip install -e ".[dev]"
```

### 3. Configuración

Copia `.env.example` a `.env` y completa tus ajustes:

```bash
cp .env.example .env
```

```env
FLASK_APP=app:create_app
FLASK_ENV=development
SECRET_KEY=tu-clave-secreta-aqui
DATABASE_URL=mysql+pymysql://usuario:contraseña@127.0.0.1:3306/mijia
JWT_SECRET_KEY=tu-clave-jwt-secreta-aqui
GO2RTC_URL=http://127.0.0.1:1984
```

### 4. Inicializar Base de Datos

```bash
mysql -u root -p -e "CREATE DATABASE mijia CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
flask db upgrade
```

### 5. Ejecutar

```bash
python run.py
```

Visita http://127.0.0.1:5000, registra una cuenta y listo.

## Resumen de API

| Módulo | Prefijo | Descripción |
|--------|---------|-------------|
| Autenticación (Sesión) | `/api/auth/` | Registro, login, logout, cambio de contraseña |
| Autenticación (JWT) | `/api/auth-jwt/` | Login JWT, refresh token |
| Vinculación Xiaomi | `/api/xiaomi/` | Vinculación QR, estado, desvinculación |
| Dispositivos | `/api/devices/` | Lista, leer/escribir propiedades, acciones, stream de cámara |
| Hogares | `/api/homes/` | Lista de hogares, detalles |
| Escenas | `/api/scenes/` | Lista de escenas, ejecución |
| Grupos | `/api/groups/` | CRUD de grupos, favoritos |
| Automatizaciones | `/api/automations/` | CRUD de reglas programadas, activar/desactivar |
| Energía | `/api/energy/` | Registros de energía, diario/horario/último |
| Sensores BLE | `/api/ble/` | Registro de dispositivos BLE, reporte de datos, consulta histórica |
| Tokens API | `/api/tokens/` | Gestión de tokens para integración con terceros |

Documentación completa de la API disponible en `/api/docs/` tras iniciar el servidor.

## Servidor MCP (Integración con Agentes IA)

Servidor MCP integrado — Claude Code, Hermes Agent, OpenClaw y cualquier Agente IA compatible con MCP pueden controlar dispositivos Mijia directamente.

### Instalación

```bash
pip install -e ".[mcp]"
```

### Configuración

Asegúrate de que el servicio Web esté en ejecución (`python run.py`), luego obtén un token:

```bash
# Opción 1: Login CLI (recomendado, guarda el token automáticamente)
mijia-control login

# Opción 2: Login vía API
curl -X POST http://127.0.0.1:5000/api/auth/jwt/login \
  -H "Content-Type: application/json" \
  -d '{"username": "tu_usuario", "password": "tu_contraseña"}'
# El access_token devuelto es tu MIJIA_TOKEN
```

Configura las variables de entorno:

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

### Uso con Claude Code

```bash
# Registrar el servidor MCP
claude mcp add mijia -- python -m mcp_server

# Luego úsalo directamente en la conversación:
# "Apaga la luz del salón"
# "Muestra el estado online de todos los dispositivos"
# "Ejecuta la escena de bienvenida a casa"
```

### Herramientas Disponibles

| Herramienta | Función |
|-------------|---------|
| `list_devices` | Listar todos los dispositivos |
| `get_device` | Ver detalles y especificaciones del dispositivo |
| `get_property` | Leer propiedad del dispositivo |
| `set_property` | Establecer propiedad del dispositivo (controlar) |
| `run_action` | Ejecutar acción del dispositivo |
| `list_scenes` | Listar escenas |
| `run_scene` | Ejecutar una escena |
| `list_homes` | Listar hogares |
| `get_home` | Ver detalles del hogar |
| `list_ble_devices` | Listar dispositivos sensores BLE |
| `get_ble_sensor` | Obtener datos del sensor BLE |
| `get_ble_readings` | Consultar historial del sensor BLE |

## Puente HomeKit (Apple Home y Siri)

Conecta dispositivos Mijia a Apple Home vía HAP-Python — contrólalos desde la app Hogar y Siri en iPhone/Mac.

### Arquitectura

```
Apple Home / Siri  →  Puente HomeKit (HAP-Python)  →  Flask REST API  →  Dispositivos Mijia
                  Proceso independiente, puerto 51826        python run.py
```

### Instalación

```bash
pip install -e ".[homekit]"
```

> **Usuarios de Windows**: Instalar [Bonjour Print Services](https://developer.apple.com/bonjour/) o ejecutar el puente en Docker.

### Configuración

Añade a `.env` (o configúralo como variables de entorno):

```env
HOMEKIT_ENABLED=true
HOMEKIT_PORT=51826
HOMEKIT_PIN=123-45-678
```

Asegúrate de que el servicio Web esté en ejecución y tengas un JWT Token (el mismo `MIJIA_TOKEN` que el servidor MCP).

### Inicio

```bash
# Inicia primero el servicio web
python run.py

# Inicia el puente HomeKit (otro terminal)
python -m app.homekit
```

### Emparejamiento

1. Asegúrate de que el teléfono y el ordenador estén en la **misma red local**
2. iPhone → app Hogar → Añadir dispositivo → escanea el código QR del terminal, o introduce el PIN manualmente
3. Tras el emparejamiento, los dispositivos aparecerán bajo el puente "Mijia Smart Home"

### App Hogar de iPhone

<p align="center">
  <img src="screenshot/2.png" width="200" alt="HomeKit App Hogar - Lista de dispositivos">
  <img src="screenshot/3.png" width="200" alt="HomeKit App Hogar - Control de dispositivos">
</p>

### Tipos de Dispositivos Soportados

| Tipo HomeKit | Dispositivos Mijia | Capacidades |
|---|---|---|
| Lightbulb | Bombillas, tiras LED | Encendido/apagado, brillo, temperatura de color |
| Outlet | Enchufes, interruptores inteligentes | Encendido/apagado |
| Switch | Robots aspiradora, purificadores de aire | Encendido/apagado |
| TemperatureSensor | Sensores de temperatura/humedad | Lectura de temperatura y humedad |
| Thermostat | Compañeros de AC, deshumidificadores | Encendido/apagado, temperatura objetivo |
| HeaterCooler | Calefactores | Encendido/apagado, temperatura objetivo |

### Mapeo Personalizado de Dispositivos

Cuando el modelo de un dispositivo no está en las reglas integradas, el puente infiere automáticamente el tipo desde spec_data. Si la inferencia es incorrecta, crea `homekit_mapping.yaml`:

```bash
cp homekit_mapping.yaml.example homekit_mapping.yaml
```

```yaml
# homekit_mapping.yaml
devices:
  zhimi.airp.mb4a: switch           # Coincidencia exacta de modelo
  lumi.sensor_magnet.aq2: ignored   # Ignorar dispositivos no deseados

fallback: auto    # auto=inferencia inteligente | switch=todo como interruptor | ignore=ignorar desconocidos
```

Categorías disponibles: `light`, `outlet`, `switch`, `temperature_sensor`, `thermostat`, `heater`, `camera`, `ignored`

## Sensores BLE Bluetooth (Recopilación Local de Datos)

Conecta termómetros Xiaomi BLE directamente vía Bluetooth del PC — sin hardware de gateway adicional. Compatible con visualización de datos, consulta histórica y disparadores de automatización.

### Arquitectura

```
Termómetro BLE  ─BLE broadcast→  BLE Scanner (independiente)  ─HTTP POST→  Flask API  →  DB
                                  python -m app.ble                          python run.py
```

### Instalación

```bash
pip install -e ".[ble]"
```

> Requiere PC con capacidad Bluetooth (Windows 10/11 tiene soporte integrado).

### Configuración

Añade a `.env`:

```env
BLE_ENABLED=true
```

Asegúrate de que `MIJIA_TOKEN` esté configurado (igual que MCP Server / puente HomeKit).

### Inicio Rápido

```bash
# 1. Escanear dispositivos BLE cercanos para encontrar la dirección MAC
mijia-control ble scan

# 2. Registrar dispositivo BLE (obtiene la clave de descifrado automáticamente)
mijia-control ble register --did "blt.3.xxxxx" --mac "A4:C1:38:XX:XX:XX"

# 3. Iniciar demonio BLE (requiere servicio Web en ejecución)
python run.py           # Terminal 1
python -m app.ble       # Terminal 2

# 4. Ver datos
mijia-control ble list
mijia-control ble readings "blt.3.xxxxx" --hours 24
```

### Dispositivos Soportados

| Dispositivo | Modelo | Datos |
|-------------|--------|-------|
| Sensor Temp/Humedad Mini | LYWSD03MMC | Temperatura, humedad, batería |
| Sensor Temp/Humedad (redondo) | LYWSDCGQ | Temperatura, humedad, batería |
| Sensor Temp/Humedad (nuevo) | MJWSD05MMC | Temperatura, humedad, batería |

📖 **Documentación completa**: [docs/ble.md](docs/ble.md) — arquitectura, configuración, depuración, resolución de problemas, extensión a nuevos dispositivos.

## Uso de CLI

Tras instalar y activar el venv, el comando `mijia-control` está disponible (sin contexto Flask):

```bash
mijia-control --help                           # Mostrar ayuda
```

> También disponible vía Flask CLI: `flask mijia <command>`

### Gestión de Usuarios

```bash
mijia-control login                            # Login (interactivo)
mijia-control logout                           # Logout
mijia-control whoami                           # Mostrar usuario actual
mijia-control xiaomi status                    # Estado de vinculación Xiaomi
mijia-control xiaomi unlink                    # Desvincular cuenta Xiaomi
```

### Control de Dispositivos

```bash
mijia-control device list                      # Listar dispositivos
mijia-control device list --home-id <id>       # Filtrar por hogar
mijia-control device list --refresh            # Forzar actualización
mijia-control device show <did>                # Detalles del dispositivo
mijia-control device get <did> <prop_name>     # Leer propiedad
mijia-control device set <did> <prop_name> <value>  # Establecer propiedad
mijia-control device action <did> <action_name>     # Ejecutar acción
```

### Escenas y Hogares

```bash
mijia-control scene list                       # Listar escenas
mijia-control scene list --refresh             # Forzar actualización
mijia-control scene run <scene_id>             # Ejecutar escena
mijia-control home list                        # Listar hogares
mijia-control home show <home_id>              # Detalles del hogar
```

### Sensores BLE Bluetooth

```bash
mijia-control ble scan                          # Escanear dispositivos BLE cercanos
mijia-control ble register --did <did> --mac <mac>  # Registrar dispositivo BLE
mijia-control ble list                          # Listar dispositivos BLE con últimas lecturas
mijia-control ble readings <did> --hours 24     # Consultar historial de lecturas
```

## Desarrollo

```bash
ruff check .           # Lint
ruff check --fix .     # Auto-corrección
ruff format .          # Formato
pytest -v              # Ejecutar tests
```

## Licencia

Este proyecto está licenciado bajo [GPL-3.0](https://www.gnu.org/licenses/gpl-3.0.html), heredada del proyecto original [mijiaAPI](https://github.com/Do1e/mijia-api).
