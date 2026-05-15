import logging
import os
import signal
from urllib.parse import quote

import httpx
from dotenv import load_dotenv
from pyhap.accessory import Bridge
from pyhap.accessory_driver import AccessoryDriver

from app.homekit.accessories import create_accessory

load_dotenv()

logger = logging.getLogger(__name__)

_DEFAULT_PORT = 51826
_DEFAULT_PIN = "123-45-678"
_BRIDGE_NAME = "米家智能家居"
_PERSIST_FILE = "homekit.state"


def _login(api_url: str, username: str, password: str) -> str:
    """通过用户名密码登录，获取 JWT access_token。"""
    resp = httpx.post(
        f"{api_url}/auth/jwt/login",
        json={"username": username, "password": password},
        timeout=30,
    )
    if resp.status_code != 200:
        try:
            body = resp.json()
            msg = body.get("msg") or body.get("error") or body.get("message")
        except Exception:
            msg = resp.text[:200]
        raise RuntimeError(f"登录失败 (HTTP {resp.status_code}): {msg}")
    data = resp.json()
    if not data.get("success"):
        msg = data.get("msg") or data.get("error") or data.get("message")
        raise RuntimeError(f"登录失败: {msg}")
    token = data.get("data", {}).get("access_token")
    if not token:
        raise RuntimeError("登录成功但未获取到 access_token")
    return token


def _fetch_devices(api_url: str, token: str) -> list[dict]:
    """从 Flask API 获取设备列表。"""
    resp = httpx.get(
        f"{api_url}/devices/",
        headers={"Authorization": f"Bearer {token}"},
        timeout=30,
    )

    if resp.status_code != 200:
        try:
            body = resp.json()
            msg = body.get("msg") or body.get("error") or body.get("message")
        except Exception:
            msg = resp.text[:200]
        raise RuntimeError(f"获取设备列表失败 (HTTP {resp.status_code}): {msg}")

    data = resp.json()
    if not data.get("success"):
        msg = data.get("msg") or data.get("error") or data.get("message")
        raise RuntimeError(f"获取设备列表失败: {msg}")
    return data.get("data", [])


def _fetch_device_detail(api_url: str, token: str, did: str) -> dict | None:
    """从 Flask API 获取设备详情（包含 spec_data）。"""
    try:
        resp = httpx.get(
            f"{api_url}/devices/{quote(did)}",
            headers={"Authorization": f"Bearer {token}"},
            timeout=15,
        )
        data = resp.json()
        if data.get("success"):
            return data.get("data")
    except Exception as e:
        logger.warning("获取设备详情 %s 失败: %s", did, e)
    return None


def start_homekit_bridge(
    api_url: str | None = None,
    token: str | None = None,
    username: str | None = None,
    password: str | None = None,
    port: int | None = None,
    pin: str | None = None,
    persist_file: str | None = None,
):
    """启动 HomeKit Bridge 服务器。

    Args:
        api_url: Flask API 地址，默认从 MIJIA_API_URL 环境变量读取
        token: JWT Token，默认从 MIJIA_TOKEN 环境变量读取
        username: 登录用户名，用于自动获取 token（从 MIJIA_USERNAME 环境变量读取）
        password: 登录密码，用于自动获取 token（从 MIJIA_PASSWORD 环境变量读取）
        port: HAP 服务端口，默认 51826
        pin: 配对 PIN 码，默认 123-45-678
        persist_file: HAP 状态持久化文件路径
    """
    api_url = api_url or os.environ.get("MIJIA_API_URL", "http://127.0.0.1:5000/api")
    token = token or os.environ.get("MIJIA_TOKEN", "")
    username = username or os.environ.get("MIJIA_USERNAME", "")
    password = password or os.environ.get("MIJIA_PASSWORD", "")
    port = port or int(os.environ.get("HOMEKIT_PORT", _DEFAULT_PORT))
    pin = pin or os.environ.get("HOMEKIT_PIN", _DEFAULT_PIN)
    persist_file = (
        persist_file
        or os.environ.get("HOMEKIT_PERSIST_FILE")
        or os.path.join(os.path.dirname(__file__), "..", "..", _PERSIST_FILE)
    )

    if not token and username and password:
        logger.info("自动登录获取 JWT token...")
        token = _login(api_url, username, password)
        logger.info("登录成功")

    if not token:
        raise ValueError("未设置 MIJIA_TOKEN，请设置 MIJIA_TOKEN 或同时设置 MIJIA_USERNAME 和 MIJIA_PASSWORD")

    logger.info("正在启动 HomeKit Bridge (端口=%d, PIN=%s)...", port, pin)
    logger.info("API 地址: %s", api_url)

    driver = AccessoryDriver(port=port, persist_file=persist_file)

    driver.state.pin = pin.replace("-", "")
    bridge = Bridge(driver, _BRIDGE_NAME)

    try:
        devices = _fetch_devices(api_url, token)
    except RuntimeError as e:
        if "HTTP 401" in str(e) and username and password:
            logger.warning("Token 已过期，自动重新登录...")
            token = _login(api_url, username, password)
            logger.info("重新登录成功")
            devices = _fetch_devices(api_url, token)
        else:
            raise
    logger.info("发现 %d 台设备", len(devices))

    aid = 2  # aid=1 预留给 Bridge 自身
    added = 0
    for device in devices:
        if not device.get("is_online", True):
            logger.debug("跳过离线设备: %s (%s)", device.get("name"), device.get("did"))
            continue

        # 确保 spec_data 已加载（详情 API 会自动填充）
        if not device.get("spec_data"):
            detail = _fetch_device_detail(api_url, token, device["did"])
            if detail:
                device = detail

        accessory = create_accessory(driver, device, api_url, token, aid=aid)
        if accessory:
            bridge.add_accessory(accessory)
            added += 1
            logger.info(
                "添加设备: %s (model=%s, aid=%d)",
                device.get("name"),
                device.get("model"),
                aid,
            )
        aid += 1

    logger.info("成功桥接 %d 台设备到 HomeKit", added)

    driver.add_accessory(bridge)

    signal.signal(signal.SIGTERM, driver.signal_handler)
    signal.signal(signal.SIGINT, driver.signal_handler)

    logger.info("HomeKit Bridge 已启动，在 iPhone 家庭 App 中搜索 '%s' 即可配对", _BRIDGE_NAME)
    driver.start()
