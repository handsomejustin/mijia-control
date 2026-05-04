# MijiaPilot

**Mijia × MCP × AI Agent × HomeKit — オールインワン スマートホームブリッジプラットフォーム。**

[中文](README.md) | [English](README_EN.md) | 日本語 | [한국어](README_KO.md) | [Español](README_ES.md)

[![MCP Server](https://glama.ai/mcp/servers/handsomejustin/mijia-control/badges/score.svg)](https://glama.ai/mcp/servers/handsomejustin/mijia-control)

> **謝辞**: 本プロジェクトは [Do1e/mijia-api](https://github.com/Do1e/mijia-api)（mijiaAPI v3.0+）の上に構築されています。
> Xiaomi Cloud とのデバイス通信、プロパティの読み書き、シーンの実行を提供する Python SDK です。

## デモ

![Agent デモ](screenshot/1.png)

![Agent デモ動画](screenshot/demo.gif)

## 機能

- **Webダッシュボード** — デバイス制御、ホーム/シーン管理、エネルギーモニタリング、オートメーションルール、ダークモード、モバイル対応
- **RESTful API** — JWT認証、完全なSwaggerドキュメント（`/api/docs/`）、サードパーティ連携対応
- **CLIツール** — `mijia-control` コマンドライン：ログイン、デバイス一覧、プロパティ読み書き、シーン実行
- **リアルタイム通信** — SocketIOによるデバイス状態変更のプッシュ通知
- **デバイスグループ & お気に入り** — カスタムグルーピング、クイックアクセスお気に入り
- **スケジュールオートメーション** — cron、インターバル、日の出/日の入りトリガー
- **エネルギーダッシュボード** — デバイス別エネルギー追跡（日/時間単位）
- **APIトークン管理** — サードパーティアプリ用アクセストークンの作成・管理
- **MCPサーバー** — 内蔵MCPプロトコル対応。Claude Code、Hermes AgentなどのAIエージェントが直接デバイス制御可能
- **HomeKitブリッジ** — AppleホームアプリとSiriでMijiaデバイスを制御。ライト、コンセント、センサー、サーモスタット等に対応
- **BLE Bluetoothセンサー** — PC BluetoothでXiaomi BLE温湿度計に直接接続、ローカルリアルタイムデータ収集、オートメーション連動
- **マルチユーザー & 権限** — ユーザー登録、管理パネル、レート制限

## 技術スタック

| レイヤー | 技術 |
|----------|------|
| Webフレームワーク | Flask 3.0+ |
| ORM & マイグレーション | SQLAlchemy + Flask-Migrate (Alembic) |
| データベース | MySQL (pymysql) |
| 認証 | Flask-Login (Session) + Flask-JWT-Extended (API) |
| CSRF保護 | Flask-WTF |
| レート制限 | Flask-Limiter |
| リアルタイム | Flask-SocketIO |
| APIドキュメント | Flasgger (Swagger UI) |
| シリアライズ | Marshmallow |
| Mijia SDK | [mijiaAPI](https://github.com/Do1e/mijia-api) >= 3.0 |
| MCPプロトコル | [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk) >= 1.6 |
| HomeKit | [HAP-Python](https://github.com/ikalchev/HAP-python) >= 5.0 |
| BLEスキャン | [bleak](https://github.com/hbldh/bleak) >= 0.22 |
| コード品質 | Ruff (lint + format) |
| テスト | pytest |

## プロジェクト構成

```
├── app/
│   ├── __init__.py          # Flaskアプリケーションファクトリ
│   ├── extensions.py        # 拡張インスタンス (db, jwt, csrf, socketio...)
│   ├── api/                 # REST API ブループリント (JWT認証)
│   ├── web/                 # Web UI ブループリント (Session + CSRF認証)
│   ├── services/            # ビジネスロジック層
│   ├── models/              # SQLAlchemyモデル
│   ├── schemas/             # Marshmallowシリアライズ/バリデーション
│   ├── utils/               # MijiaAPIアダプタ、レスポンスヘルパー、デコレータ
│   ├── cli/                 # Click CLIコマンド
│   ├── homekit/             # HomeKitブリッジ
│   └── ble/                 # BLE Bluetoothセンサーデーモン（独立プロセス）
├── mcp_server/              # MCPサーバー (AIエージェントツール)
├── config/                  # Flask設定 (development/testing/production)
├── migrations/              # Alembicマイグレーションスクリプト
├── tests/                   # pytestテスト
├── run.py                   # 開発サーバーエントリポイント
├── docs/                    # 詳細ドキュメント
└── pyproject.toml           # プロジェクト設定 & 依存関係
```

## クイックスタート

### 1. 前提条件

- Python 3.10+
- MySQL 5.7+

### 2. インストール

```bash
git clone https://github.com/handsomejustin/mijia-control.git
cd mijia-control

python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

pip install -e ".[dev]"
```

### 3. 設定

`.env.example` を `.env` にコピーして設定を記入：

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

### 4. データベース初期化

```bash
mysql -u root -p -e "CREATE DATABASE mijia CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
flask db upgrade
```

### 5. 起動

```bash
python run.py
```

http://127.0.0.1:5000 にアクセスし、アカウント登録後すぐに利用可能です。

## API概要

| モジュール | プレフィックス | 説明 |
|-----------|---------------|------|
| 認証 (Session) | `/api/auth/` | 登録、ログイン、ログアウト、パスワード変更 |
| 認証 (JWT) | `/api/auth-jwt/` | JWTログイン、リフレッシュトークン |
| Xiaomi連携 | `/api/xiaomi/` | QRコード連携、ステータス確認、解除 |
| デバイス | `/api/devices/` | 一覧、プロパティ読み書き、アクション、カメラストリーム |
| ホーム | `/api/homes/` | ホーム一覧、詳細 |
| シーン | `/api/scenes/` | シーン一覧、実行 |
| グループ | `/api/groups/` | グループCRUD、お気に入り |
| オートメーション | `/api/automations/` | スケジュールルールCRUD、有効/無効 |
| エネルギー | `/api/energy/` | エネルギー記録、日/時間/最新 |
| BLEセンサー | `/api/ble/` | BLEデバイス登録、データ報告、履歴照会 |
| APIトークン | `/api/tokens/` | サードパーティ連携用トークン管理 |

完全なAPIドキュメントはサーバー起動後 `/api/docs/` で確認できます。

## MCPサーバー（AIエージェント連携）

内蔵MCPサーバー — Claude Code、Hermes Agent、OpenClawなど、MCP互換のAIエージェントが直接Mijiaデバイスを制御できます。

### インストール

```bash
pip install -e ".[mcp]"
```

### 設定

Webサービスが起動していることを確認し（`python run.py`）、トークンを取得：

```bash
# 方法1: CLIログイン（推奨、トークン自動保存）
mijia-control login

# 方法2: APIログイン
curl -X POST http://127.0.0.1:5000/api/auth/jwt/login \
  -H "Content-Type: application/json" \
  -d '{"username": "ユーザー名", "password": "パスワード"}'
# 返却される access_token が MIJIA_TOKEN です
```

環境変数の設定：

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

### Claude Codeでの使用

```bash
# MCPサーバーを登録
claude mcp add mijia -- python -m mcp_server

# 会話で直接使用可能：
# "リビングの電気を消して"
# "すべてのデバイスのオンライン状態を確認して"
# "帰宅シーンを実行して"
```

### 利用可能ツール

| ツール | 機能 |
|--------|------|
| `list_devices` | 全デバイス一覧 |
| `get_device` | デバイス詳細・仕様確認 |
| `get_property` | デバイスプロパティ読み取り |
| `set_property` | デバイスプロパティ設定（制御） |
| `run_action` | デバイスアクション実行 |
| `list_scenes` | シーン一覧 |
| `run_scene` | シーン実行 |
| `list_homes` | ホーム一覧 |
| `get_home` | ホーム詳細確認 |
| `list_ble_devices` | BLEセンサーデバイス一覧 |
| `get_ble_sensor` | BLEセンサー最新データ取得 |
| `get_ble_readings` | BLEセンサー履歴照会 |

## HomeKitブリッジ（Appleホーム & Siri）

HAP-PythonでMijiaデバイスをAppleホームにブリッジ — iPhone/MacのホームアプリとSiriから制御できます。

### アーキテクチャ

```
Appleホーム / Siri  →  HomeKitブリッジ (HAP-Python)  →  Flask REST API  →  Mijiaデバイス
                   独立プロセス、ポート51826               python run.py
```

### インストール

```bash
pip install -e ".[homekit]"
```

> **Windowsユーザー**: [Bonjour Print Services](https://developer.apple.com/bonjour/) のインストールが必要です。

### 設定

`.env` に追加（または環境変数として設定）：

```env
HOMEKIT_ENABLED=true
HOMEKIT_PORT=51826
HOMEKIT_PIN=123-45-678
```

Webサービスの起動とJWTトークンの取得が必要です（MCPサーバーと同じ `MIJIA_TOKEN`）。

### 起動

```bash
# 先にWebサービスを起動
python run.py

# HomeKitブリッジを起動（別ターミナル）
python -m app.homekit
```

### ペアリング

1. スマホとPCが**同じローカルネットワーク**にあることを確認
2. iPhone → ホームアプリ → デバイス追加 → ターミナルに表示されたQRコードをスキャン、またはPINを手動入力
3. ペアリング完了後、デバイスは「Mijiaスマートホーム」ブリッジとして表示されます

### iPhoneホームアプリ

<p align="center">
  <img src="screenshot/2.png" width="200" alt="HomeKit ホームアプリ - デバイス一覧">
  <img src="screenshot/3.png" width="200" alt="HomeKit ホームアプリ - デバイス制御">
</p>

### 対応デバイスタイプ

| HomeKitタイプ | Mijiaデバイス | 機能 |
|---|---|---|
| Lightbulb | 電球、ライトストリップ | ON/OFF、明るさ、色温度 |
| Outlet | プラグ、スマートスイッチ | ON/OFF |
| Switch | ロボット掃除機、空気清浄機 | ON/OFF |
| TemperatureSensor | 温湿度センサー | 温度、湿度読み取り |
| Thermostat | エアコンパートナー、除湿機 | ON/OFF、目標温度 |
| HeaterCooler | ヒーター | ON/OFF、目標温度 |

### カスタムデバイスマッピング

デバイスモデルが内蔵ルールにない場合、ブリッジはspec_dataから自動的にタイプを推測します。推測が不正確な場合は `homekit_mapping.yaml` を作成：

```bash
cp homekit_mapping.yaml.example homekit_mapping.yaml
```

```yaml
# homekit_mapping.yaml
devices:
  zhimi.airp.mb4a: switch           # モデル完全一致
  lumi.sensor_magnet.aq2: ignored   # 不要なデバイスを無視

fallback: auto    # auto=スマート推測 | switch=すべてスイッチ | ignore=未知を無視
```

利用可能カテゴリ：`light`、`outlet`、`switch`、`temperature_sensor`、`thermostat`、`heater`、`camera`、`ignored`

## BLE Bluetoothセンサー（ローカルデータ収集）

PCのBluetoothでXiaomi BLE温湿度計などに直接接続。追加のBluetoothゲートウェイハードウェア不要。データ表示、履歴照会、オートメーション連動に対応。

### アーキテクチャ

```
BLE温度計  ─BLE broadcast→  BLE Scanner (独立)  ─HTTP POST→  Flask API  →  DB
                             python -m app.ble                    python run.py
```

### インストール

```bash
pip install -e ".[ble]"
```

> Bluetooth機能のあるPCが必要（Windows 10/11は内蔵対応）。

### 設定

`.env`に追加：

```env
BLE_ENABLED=true
```

`MIJIA_TOKEN`が設定済みであることを確認（MCPサーバー/ HomeKitブリッジと共通）。

### 使用手順

```bash
# 1. 近くのBLEデバイスをスキャンしてMACアドレスを発見
mijia-control ble scan

# 2. BLEデバイスを登録（クラウドから暗号化キーを自動取得）
mijia-control ble register --did "blt.3.xxxxx" --mac "A4:C1:38:XX:XX:XX"

# 3. BLEデーモン起動（Webサービスの起動が必要）
python run.py           # ターミナル 1
python -m app.ble       # ターミナル 2

# 4. データ確認
mijia-control ble list
mijia-control ble readings "blt.3.xxxxx" --hours 24
```

### 対応デバイス

| デバイス | モデル | データ |
|----------|--------|--------|
| 米家温湿度センサーミニ | LYWSD03MMC | 温度、湿度、バッテリー |
| 米家温湿度センサー（丸型） | LYWSDCGQ | 温度、湿度、バッテリー |
| 米家温湿度センサー（新品） | MJWSD05MMC | 温度、湿度、バッテリー |

📖 **詳細ドキュメント**：[docs/ble.md](docs/ble.md) — アーキテクチャ、セットアップ、デバッグ、トラブルシューティング、新規デバイス拡張方法。

## CLI使用方法

venvのインストールと有効化後、`mijia-control` コマンドが利用可能（Flaskコンテキスト不要）：

```bash
mijia-control --help                           # ヘルプ表示
```

> Flask CLI経由でも利用可能：`flask mijia <command>`

### ユーザー管理

```bash
mijia-control login                            # ログイン（対話式）
mijia-control logout                           # ログアウト
mijia-control whoami                           # 現在のユーザー確認
mijia-control xiaomi status                    # Xiaomiアカウント連携状態
mijia-control xiaomi unlink                    # Xiaomiアカウント解除
```

### デバイス制御

```bash
mijia-control device list                      # デバイス一覧
mijia-control device list --home-id <id>       # ホームで絞り込み
mijia-control device list --refresh            # 強制リフレッシュ
mijia-control device show <did>                # デバイス詳細
mijia-control device get <did> <prop_name>     # プロパティ読み取り
mijia-control device set <did> <prop_name> <value>  # プロパティ設定
mijia-control device action <did> <action_name>     # アクション実行
```

### シーン & ホーム

```bash
mijia-control scene list                       # シーン一覧
mijia-control scene list --refresh             # 強制リフレッシュ
mijia-control scene run <scene_id>             # シーン実行
mijia-control home list                        # ホーム一覧
mijia-control home show <home_id>              # ホーム詳細
```

### BLE Bluetoothセンサー

```bash
mijia-control ble scan                          # 近くのBLEデバイスをスキャン
mijia-control ble register --did <did> --mac <mac>  # BLEデバイス登録
mijia-control ble list                          # BLEデバイスと最新読み取り値
mijia-control ble readings <did> --hours 24     # 履歴データ照会
```

## 開発

```bash
ruff check .           # Lint
ruff check --fix .     # 自動修正
ruff format .          # フォーマット
pytest -v              # テスト実行
```

## ライセンス

本プロジェクトは [GPL-3.0](https://www.gnu.org/licenses/gpl-3.0.html) ライセンスで公開されています。上流の [mijiaAPI](https://github.com/Do1e/mijia-api) のライセンスを継承しています。
