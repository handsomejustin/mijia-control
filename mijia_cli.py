"""独立 CLI 入口 — 不依赖 Flask app，仅通过 HTTP 调用 API。"""
import json
import os
import sys
from urllib.parse import quote

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

import click

CONFIG_DIR = os.path.expanduser("~/.config/mijia-control")
TOKEN_FILE = os.path.join(CONFIG_DIR, "token.json")


def _did(did):
    """URL-encode DID for use in API paths (handles # and other special chars)."""
    return quote(str(did), safe="")


def _get_base_url():
    return os.environ.get("MIJIA_API_URL", "http://127.0.0.1:5000/api")


def _get_token():
    if os.environ.get("MIJIA_TOKEN"):
        return os.environ["MIJIA_TOKEN"]
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, "r") as f:
            data = json.load(f)
            return data.get("token")
    return None


def _api_request(method, path, data=None, params=None):
    import requests

    token = _get_token()
    if not token:
        click.echo(json.dumps({"error": "未登录，请先运行 mijia-control login"}, ensure_ascii=False))
        sys.exit(1)

    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    url = f"{_get_base_url()}{path}"

    try:
        resp = requests.request(method, url, json=data, params=params, headers=headers)
        result = resp.json()
        click.echo(json.dumps(result, ensure_ascii=False, indent=2))
    except Exception as e:
        click.echo(json.dumps({"error": str(e)}, ensure_ascii=False))
        sys.exit(1)


@click.group()
def cli():
    """米家智能设备控制 CLI"""
    pass


# ── 用户管理 ──

@cli.command("login")
@click.option("--username", prompt=True)
@click.option("--password", prompt=True, hide_input=True)
def login_cmd(username, password):
    """登录系统"""
    import requests

    resp = requests.post(
        f"{_get_base_url()}/auth/jwt/login",
        json={"username": username, "password": password},
    )
    result = resp.json()
    if result.get("success"):
        os.makedirs(CONFIG_DIR, exist_ok=True)
        with open(TOKEN_FILE, "w") as f:
            json.dump({
                "token": result["data"]["access_token"],
                "refresh_token": result["data"]["refresh_token"],
                "username": username,
                "user_id": result["data"]["user_id"],
            }, f)
        click.echo(f"登录成功: {username}")
    else:
        click.echo(json.dumps(result, ensure_ascii=False, indent=2))
        sys.exit(1)


@cli.command("logout")
def logout_cmd():
    """退出登录"""
    if os.path.exists(TOKEN_FILE):
        os.remove(TOKEN_FILE)
    click.echo(json.dumps({"success": True, "message": "已退出登录"}, ensure_ascii=False))


@cli.command("whoami")
def whoami_cmd():
    """查看当前用户"""
    _api_request("GET", "/auth/me")


# ── 小米账号 ──

@cli.group("xiaomi")
def xiaomi_grp():
    """小米账号管理"""
    pass


@xiaomi_grp.command("status")
def xiaomi_status():
    """查看小米账号绑定状态"""
    _api_request("GET", "/xiaomi/status")


@xiaomi_grp.command("unlink")
def xiaomi_unlink():
    """解绑小米账号"""
    _api_request("DELETE", "/xiaomi/unlink")


# ── 设备控制 ──

@cli.group("device")
def device_grp():
    """设备控制"""
    pass


@device_grp.command("list")
@click.option("--home-id", default=None)
@click.option("--refresh", is_flag=True)
def device_list(home_id, refresh):
    """列出设备"""
    params = {}
    if home_id:
        params["home_id"] = home_id
    if refresh:
        params["refresh"] = "true"
    _api_request("GET", "/devices/", params=params)


@device_grp.command("show")
@click.argument("did")
def device_show(did):
    """查看设备详情"""
    _api_request("GET", f"/devices/{_did(did)}")


@device_grp.command("get")
@click.argument("did")
@click.argument("prop_name")
def device_get(did, prop_name):
    """读取设备属性"""
    _api_request("GET", f"/devices/{_did(did)}/props/{prop_name}")


@device_grp.command("set")
@click.argument("did")
@click.argument("prop_name")
@click.argument("value")
def device_set(did, prop_name, value):
    """设置设备属性"""
    try:
        parsed_value = json.loads(value)
    except json.JSONDecodeError:
        if value.lower() == "true":
            parsed_value = True
        elif value.lower() == "false":
            parsed_value = False
        else:
            try:
                parsed_value = int(value)
            except ValueError:
                try:
                    parsed_value = float(value)
                except ValueError:
                    parsed_value = value
    _api_request("PUT", f"/devices/{_did(did)}/props/{prop_name}", data={"value": parsed_value})


@device_grp.command("action")
@click.argument("did")
@click.argument("action_name")
@click.option("--value", default=None)
def device_action(did, action_name, value):
    """执行设备动作"""
    data = {}
    if value:
        try:
            data["value"] = json.loads(value)
        except json.JSONDecodeError:
            data["value"] = value
    _api_request("POST", f"/devices/{_did(did)}/actions/{action_name}", data=data)


# ── 场景管理 ──

@cli.group("scene")
def scene_grp():
    """场景管理"""
    pass


@scene_grp.command("list")
@click.option("--home-id", default=None)
@click.option("--refresh", is_flag=True)
def scene_list(home_id, refresh):
    """列出场景"""
    params = {}
    if home_id:
        params["home_id"] = home_id
    if refresh:
        params["refresh"] = "true"
    _api_request("GET", "/scenes/", params=params)


@scene_grp.command("run")
@click.argument("scene_id")
def scene_run(scene_id):
    """执行场景"""
    _api_request("POST", f"/scenes/{scene_id}/run")


# ── 家庭管理 ──

@cli.group("home")
def home_grp():
    """家庭管理"""
    pass


@home_grp.command("list")
@click.option("--refresh", is_flag=True)
def home_list(refresh):
    """列出家庭"""
    params = {}
    if refresh:
        params["refresh"] = "true"
    _api_request("GET", "/homes/", params=params)


@home_grp.command("show")
@click.argument("home_id")
def home_show(home_id):
    """查看家庭详情"""
    _api_request("GET", f"/homes/{home_id}")


# ── BLE 蓝牙传感器 ──


@cli.group("ble")
def ble_grp():
    """蓝牙传感器管理"""
    pass


@ble_grp.command("list")
def ble_list():
    """列出 BLE 设备及最新读数"""
    _api_request("GET", "/ble/devices")


@ble_grp.command("register")
@click.option("--did", required=True, help="设备 ID，如 blt.3.xxxxx")
@click.option("--mac", required=True, help="设备 MAC 地址，如 AA:BB:CC:DD:EE:FF")
@click.option("--bindkey", default=None, help="绑定密钥（不提供则自动从云端获取）")
def ble_register(did, mac, bindkey):
    """注册 BLE 设备"""
    data = {"did": did, "mac_address": mac}
    if bindkey:
        data["bindkey"] = bindkey
    _api_request("POST", "/ble/devices", data=data)


@ble_grp.command("scan")
@click.option("--timeout", default=10, help="扫描超时（秒）")
def ble_scan(timeout):
    """扫描附近的 BLE 设备，发现 MAC 地址"""
    import asyncio

    try:
        from bleak import BleakScanner
    except ImportError:
        click.echo(json.dumps({"error": "请先安装 bleak: pip install bleak"}, ensure_ascii=False))
        sys.exit(1)

    async def _scan():
        click.echo(f"正在扫描 BLE 设备（{timeout}秒）...")
        devices = await BleakScanner.discover(timeout=timeout)
        results = []
        for d in devices:
            results.append({"name": d.name or "未知", "address": d.address})
        click.echo(json.dumps(results, ensure_ascii=False, indent=2))

    asyncio.run(_scan())


@ble_grp.command("readings")
@click.argument("did")
@click.option("--hours", default=24, help="查询最近 N 小时")
@click.option("--limit", default=50, help="最大返回条数")
def ble_readings(did, hours, limit):
    """查询 BLE 设备历史读数"""
    _api_request("GET", f"/ble/devices/{_did(did)}/readings", params={"hours": hours, "limit": limit})


if __name__ == "__main__":
    cli()
