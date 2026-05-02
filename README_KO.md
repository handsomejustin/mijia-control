# MijiaPilot

**Mijia × MCP × AI Agent × HomeKit — 올인원 스마트홈 브릿지 플랫폼.**

[中文](README.md) | [English](README_EN.md) | [日本語](README_JA.md) | 한국어 | [Español](README_ES.md)

[![MCP Server](https://glama.ai/mcp/servers/handsomejustin/mijia-control/badges/score.svg)](https://glama.ai/mcp/servers/handsomejustin/mijia-control)

> **감사 인사**: 이 프로젝트는 [Do1e/mijia-api](https://github.com/Do1e/mijia-api)(mijiaAPI v3.0+)를 기반으로 구축되었습니다.
> Xiaomi Cloud와의 기기 통신, 속성 읽기/쓰기, 씬 실행을 제공하는 Python SDK입니다.

## 데모

![Agent 데모](screenshot/1.png)

![Agent 데모 영상](screenshot/demo.gif)

## 주요 기능

- **웹 대시보드** — 기기 제어, 홈/씬 관리, 에너지 모니터링, 자동화 규칙, 다크 모드, 모바일 대응
- **RESTful API** — JWT 인증, 완전한 Swagger 문서(`/api/docs/`), 서드파티 연동 가능
- **CLI 도구** — `mijia-control` 명령줄: 로그인, 기기 목록, 속성 읽기/쓰기, 씬 실행
- **실시간 통신** — SocketIO 기기 상태 변경 푸시
- **기기 그룹 & 즐겨찾기** — 커스텀 그룹화, 빠른 즐겨찾기 접근
- **예약 자동화** — cron, interval, 일출/일몰 트리거
- **에너지 대시보드** — 기기별 에너지 추적 (일/시간 단위)
- **API 토큰 관리** — 서드파티 앱용 액세스 토큰 생성 및 관리
- **MCP 서버** — 내장 MCP 프로토콜 지원. Claude Code, Hermes Agent 등 AI 에이전트가 직접 기기 제어 가능
- **HomeKit 브릿지** — Apple 홈 앱과 Siri로 Mijia 기기 제어. 조명, 콘센트, 센서, 온도조절기 등 지원
- **다중 사용자 & 권한** — 사용자 등록, 관리자 패널, 요청 제한

## 기술 스택

| 계층 | 기술 |
|------|------|
| 웹 프레임워크 | Flask 3.0+ |
| ORM & 마이그레이션 | SQLAlchemy + Flask-Migrate (Alembic) |
| 데이터베이스 | MySQL (pymysql) |
| 인증 | Flask-Login (Session) + Flask-JWT-Extended (API) |
| CSRF 보호 | Flask-WTF |
| 요청 제한 | Flask-Limiter |
| 실시간 | Flask-SocketIO |
| API 문서 | Flasgger (Swagger UI) |
| 직렬화 | Marshmallow |
| Mijia SDK | [mijiaAPI](https://github.com/Do1e/mijia-api) >= 3.0 |
| MCP 프로토콜 | [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk) >= 1.6 |
| HomeKit | [HAP-Python](https://github.com/ikalchev/HAP-python) >= 5.0 |
| 코드 품질 | Ruff (lint + format) |
| 테스트 | pytest |

## 프로젝트 구조

```
├── app/
│   ├── __init__.py          # Flask 애플리케이션 팩토리
│   ├── extensions.py        # 확장 인스턴스 (db, jwt, csrf, socketio...)
│   ├── api/                 # REST API 블루프린트 (JWT 인증)
│   ├── web/                 # Web UI 블루프린트 (Session + CSRF 인증)
│   ├── services/            # 비즈니스 로직 계층
│   ├── models/              # SQLAlchemy 모델
│   ├── schemas/             # Marshmallow 직렬화/검증
│   ├── utils/               # MijiaAPI 어댑터, 응답 헬퍼, 데코레이터
│   ├── cli/                 # Click CLI 명령
│   └── homekit/             # HomeKit 브릿지
├── mcp_server/              # MCP 서버 (AI 에이전트 도구)
├── config/                  # Flask 설정 (development/testing/production)
├── migrations/              # Alembic 마이그레이션 스크립트
├── tests/                   # pytest 테스트
├── run.py                   # 개발 서버 진입점
├── docs/                    # 상세 문서
└── pyproject.toml           # 프로젝트 설정 & 의존성
```

## 빠른 시작

### 1. 사전 요구사항

- Python 3.10+
- MySQL 5.7+

### 2. 설치

```bash
git clone https://github.com/handsomejustin/mijia-control.git
cd mijia-control

python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

pip install -e ".[dev]"
```

### 3. 설정

`.env.example`을 `.env`로 복사하고 설정을 입력:

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

### 4. 데이터베이스 초기화

```bash
mysql -u root -p -e "CREATE DATABASE mijia CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
flask db upgrade
```

### 5. 실행

```bash
python run.py
```

http://127.0.0.1:5000 에 접속하여 계정을 등록하면 바로 사용할 수 있습니다.

## API 개요

| 모듈 | 접두사 | 설명 |
|------|--------|------|
| 인증 (Session) | `/api/auth/` | 회원가입, 로그인, 로그아웃, 비밀번호 변경 |
| 인증 (JWT) | `/api/auth-jwt/` | JWT 로그인, 리프레시 토큰 |
| Xiaomi 연동 | `/api/xiaomi/` | QR코드 연동, 상태 확인, 연결 해제 |
| 기기 관리 | `/api/devices/` | 목록, 속성 읽기/쓰기, 액션, 카메라 스트림 |
| 홈 관리 | `/api/homes/` | 홈 목록, 상세 |
| 씬 | `/api/scenes/` | 씬 목록, 실행 |
| 그룹 | `/api/groups/` | 그룹 CRUD, 즐겨찾기 |
| 자동화 | `/api/automations/` | 예약 규칙 CRUD, 활성화/비활성화 |
| 에너지 | `/api/energy/` | 에너지 기록, 일/시간/최신 |
| API 토큰 | `/api/tokens/` | 서드파티 연동용 토큰 관리 |

전체 API 문서는 서버 시작 후 `/api/docs/`에서 확인할 수 있습니다.

## MCP 서버 (AI 에이전트 연동)

내장 MCP 서버 — Claude Code, Hermes Agent, OpenClaw 등 MCP 호환 AI 에이전트가 Mijia 기기를 직접 제어할 수 있습니다.

### 설치

```bash
pip install -e ".[mcp]"
```

### 설정

웹 서비스가 실행 중인지 확인(`python run.py`)한 후 토큰을 획득:

```bash
# 방법 1: CLI 로그인 (권장, 토큰 자동 저장)
mijia-control login

# 방법 2: API 로그인
curl -X POST http://127.0.0.1:5000/api/auth/jwt/login \
  -H "Content-Type: application/json" \
  -d '{"username": "사용자이름", "password": "비밀번호"}'
# 반환된 access_token이 MIJIA_TOKEN입니다
```

환경 변수 설정:

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

### Claude Code에서 사용

```bash
# MCP 서버 등록
claude mcp add mijia -- python -m mcp_server

# 대화에서 바로 사용:
# "거실 불 꺼줘"
# "모든 기기의 온라인 상태 확인해줘"
# "귀가 씬 실행해줘"
```

### 사용 가능한 도구

| 도구 | 기능 |
|------|------|
| `list_devices` | 전체 기기 목록 |
| `get_device` | 기기 상세 및 사양 확인 |
| `get_property` | 기기 속성 읽기 |
| `set_property` | 기기 속성 설정 (기기 제어) |
| `run_action` | 기기 액션 실행 |
| `list_scenes` | 씬 목록 |
| `run_scene` | 씬 실행 |
| `list_homes` | 홈 목록 |
| `get_home` | 홈 상세 확인 |

## HomeKit 브릿지 (Apple 홈 & Siri)

HAP-Python으로 Mijia 기기를 Apple 홈에 브릿지 — iPhone/Mac의 홈 앱과 Siri로 제어할 수 있습니다.

### 아키텍처

```
Apple 홈 / Siri  →  HomeKit 브릿지 (HAP-Python)  →  Flask REST API  →  Mijia 기기
                독립 프로세스, 포트 51826               python run.py
```

### 설치

```bash
pip install -e ".[homekit]"
```

> **Windows 사용자**: [Bonjour Print Services](https://developer.apple.com/bonjour/) 설치가 필요합니다.

### 설정

`.env`에 추가 (또는 환경 변수로 설정):

```env
HOMEKIT_ENABLED=true
HOMEKIT_PORT=51826
HOMEKIT_PIN=123-45-678
```

웹 서비스 실행과 JWT 토큰 획득이 필요합니다 (MCP 서버와 동일한 `MIJIA_TOKEN`).

### 실행

```bash
# 먼저 웹 서비스 실행
python run.py

# HomeKit 브릿지 실행 (다른 터미널)
python -m app.homekit
```

### 페어링

1. 스마트폰과 컴퓨터가 **같은 로컬 네트워크**에 있는지 확인
2. iPhone → 홈 앱 → 기기 추가 → 터미널에 표시된 QR코드 스캔 또는 PIN 수동 입력
3. 페어링 완료 후 기기가 "Mijia 스마트홈" 브릿지로 표시됩니다

### iPhone 홈 앱

<p align="center">
  <img src="screenshot/2.png" width="200" alt="HomeKit 홈 앱 - 기기 목록">
  <img src="screenshot/3.png" width="200" alt="HomeKit 홈 앱 - 기기 제어">
</p>

### 지원 기기 유형

| HomeKit 유형 | Mijia 기기 | 기능 |
|---|---|---|
| Lightbulb | 전구, 라이트 스트립 | 켜기/끄기, 밝기, 색온도 |
| Outlet | 플러그, 스마트 스위치 | 켜기/끄기 |
| Switch | 로봇 청소기, 공기청정기 등 | 켜기/끄기 |
| TemperatureSensor | 온습도 센서 | 온도, 습도 읽기 |
| Thermostat | 에어컨 파트너, 제습기 | 켜기/끄기, 목표 온도 |
| HeaterCooler | 히터 | 켜기/끄기, 목표 온도 |

### 커스텀 기기 매핑

기기 모델이 내장 규칙에 없는 경우, 브릿지가 spec_data에서 자동으로 유형을 추론합니다. 추론이 부정확한 경우 `homekit_mapping.yaml`을 생성:

```bash
cp homekit_mapping.yaml.example homekit_mapping.yaml
```

```yaml
# homekit_mapping.yaml
devices:
  zhimi.airp.mb4a: switch           # 모델 정확히 일치
  lumi.sensor_magnet.aq2: ignored   # 불필요한 기기 무시

fallback: auto    # auto=스마트 추론 | switch=모두 스위치 | ignore=알 수 없는 기기 무시
```

사용 가능한 카테고리: `light`, `outlet`, `switch`, `temperature_sensor`, `thermostat`, `heater`, `camera`, `ignored`

## CLI 사용법

venv 설치 및 활성화 후 `mijia-control` 명령을 사용할 수 있습니다 (Flask 컨텍스트 불필요):

```bash
mijia-control --help                           # 도움말 표시
```

> Flask CLI를 통해서도 사용 가능: `flask mijia <command>`

### 사용자 관리

```bash
mijia-control login                            # 로그인 (대화형)
mijia-control logout                           # 로그아웃
mijia-control whoami                           # 현재 사용자 확인
mijia-control xiaomi status                    # Xiaomi 계정 연동 상태
mijia-control xiaomi unlink                    # Xiaomi 계정 연결 해제
```

### 기기 제어

```bash
mijia-control device list                      # 기기 목록
mijia-control device list --home-id <id>       # 홈별 필터
mijia-control device list --refresh            # 강력 새로고침
mijia-control device show <did>                # 기기 상세
mijia-control device get <did> <prop_name>     # 속성 읽기
mijia-control device set <did> <prop_name> <value>  # 속성 설정
mijia-control device action <did> <action_name>     # 액션 실행
```

### 씬 & 홈

```bash
mijia-control scene list                       # 씬 목록
mijia-control scene list --refresh             # 강력 새로고침
mijia-control scene run <scene_id>             # 씬 실행
mijia-control home list                        # 홈 목록
mijia-control home show <home_id>              # 홈 상세
```

## 개발

```bash
ruff check .           # Lint
ruff check --fix .     # 자동 수정
ruff format .          # 포맷
pytest -v              # 테스트 실행
```

## 라이선스

이 프로젝트는 [GPL-3.0](https://www.gnu.org/licenses/gpl-3.0.html) 라이선스로 공개되어 있습니다. 상위 프로젝트 [mijiaAPI](https://github.com/Do1e/mijia-api)의 라이선스를 상속합니다.
