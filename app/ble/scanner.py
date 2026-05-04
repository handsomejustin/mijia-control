import asyncio
import logging
import signal

import httpx

from app.ble.config import (
    BLE_ADAPTER,
    MIJIA_API_URL,
    MIJIA_PASSWORD,
    MIJIA_TOKEN,
    MIJIA_USERNAME,
    XIAOMI_MANUFACTURER_ID,
)
from app.ble.parser import decrypt_payload, get_parser

logger = logging.getLogger(__name__)


class TargetDevice:
    __slots__ = ("did", "mac", "bindkey", "model", "capabilities")

    def __init__(self, did: str, mac: str, bindkey: str | None, model: str, capabilities: list[str]):
        self.did = did
        self.mac = mac.upper()
        self.bindkey = bindkey
        self.model = model
        self.capabilities = capabilities


def _load_targets(api_url: str, token: str) -> list[TargetDevice]:
    resp = httpx.get(
        f"{api_url}/ble/devices/_all_enabled",
        headers={"Authorization": f"Bearer {token}"},
        timeout=15,
    )
    data = resp.json()
    if not data.get("success"):
        raise RuntimeError(f"获取 BLE 设备列表失败: {data.get('message')}")
    devices = data.get("data", [])
    return [
        TargetDevice(
            did=d["did"],
            mac=d["mac_address"],
            bindkey=d.get("bindkey"),
            model=d.get("model", "lywsd03mmc"),
            capabilities=d.get("capabilities", []),
        )
        for d in devices
    ]


def _report_reading(api_url: str, token: str, did: str, values: dict) -> bool:
    try:
        resp = httpx.post(
            f"{api_url}/ble/devices/{did}/readings",
            json={"values": values},
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            timeout=10,
        )
        data = resp.json()
        return data.get("success", False)
    except Exception as e:
        logger.warning("上报读数失败: did=%s, error=%s", did, e)
        return False


def _extract_xiaomi_data(manufacturer_data: dict[int, bytes]) -> bytes | None:
    data = manufacturer_data.get(XIAOMI_MANUFACTURER_ID)
    if not data:
        return None
    # 小米广播包格式: frame_ctrl(2) + product_id(2) + counter(1) + mac(6) + payload
    # 最小长度: 1(类型) + 1(长度) + 2(帧控制) + 2(product_id) + 1(counter) = 7
    if len(data) < 7:
        return None
    return data


async def scan_loop(api_url: str, token: str, adapter: str = ""):
    from bleak import BleakScanner

    logger.info("正在加载目标设备列表...")
    targets = _load_targets(api_url, token)
    if not targets:
        logger.warning("没有已注册的 BLE 设备，等待 30 秒后重试...")
        await asyncio.sleep(30)
        return

    mac_to_target: dict[str, TargetDevice] = {t.mac: t for t in targets}
    logger.info("已加载 %d 台目标设备: %s", len(targets), [t.mac for t in targets])

    logger.info("开始 BLE 扫描 (adapter=%s)...", adapter or "default")
    decrypt_fails_since_last_success = 0

    async with BleakScanner(adapter=adapter) as scanner:
        async for device, advertisement in scanner.advertisement_stream():
            mac = device.address.upper()
            target = mac_to_target.get(mac)
            if not target:
                continue

            raw = _extract_xiaomi_data(advertisement.manufacturer_data)
            if not raw:
                continue

            if not target.bindkey:
                logger.warning("设备 %s (%s) 没有 bindkey，跳过", target.did, target.mac)
                continue

            decrypted = decrypt_payload(raw, target.bindkey, target.mac)
            if decrypted is None:
                decrypt_fails_since_last_success += 1
                if decrypt_fails_since_last_success % 10 == 0:
                    logger.warning("设备 %s 连续 %d 次解密失败", target.did, decrypt_fails_since_last_success)
                continue

            decrypt_fails_since_last_success = 0

            parser = get_parser(target.model)
            if not parser:
                logger.warning("未找到 %s 的解析器，使用通用温度湿度解析", target.model)
                parser = get_parser("lywsd03mmc")

            if not parser:
                continue

            values = parser.parse(decrypted)
            if not values:
                continue

            logger.info(
                "设备 %s (%s): %s",
                target.did,
                target.mac,
                ", ".join(f"{k}={v}" for k, v in values.items()),
            )

            if _report_reading(api_url, token, target.did, values):
                logger.debug("已上报 %s: %s", target.did, values)


def _login(api_url: str, username: str, password: str) -> str | None:
    try:
        resp = httpx.post(
            f"{api_url}/auth/jwt/login",
            json={"username": username, "password": password},
            timeout=30,
        )
        if resp.status_code != 200:
            logger.warning("登录失败 (HTTP %d)", resp.status_code)
            return None
        data = resp.json()
        if not data.get("success"):
            logger.warning("登录失败: %s", data.get("message") or data.get("msg"))
            return None
        token = data.get("data", {}).get("access_token")
        if not token:
            logger.warning("登录成功但未获取到 access_token")
            return None
        return token
    except Exception as e:
        logger.error("登录请求失败: %s", e)
        return None


async def run_scanner():
    from bleak import BleakScanner

    try:
        await BleakScanner.discover(timeout=2, adapter=BLE_ADAPTER or None, return_adv=False)
        logger.info("BLE 适配器检查通过")
    except Exception as e:
        logger.error("BLE 适配器不可用: %s。请确认 PC 蓝牙已开启。", e)
        return

    api_url = MIJIA_API_URL
    token = MIJIA_TOKEN

    if not token and MIJIA_USERNAME and MIJIA_PASSWORD:
        logger.info("未设置 MIJIA_TOKEN，尝试使用用户名密码自动登录...")
        token = _login(api_url, MIJIA_USERNAME, MIJIA_PASSWORD)
        if token:
            logger.info("自动登录成功")
        else:
            logger.error("自动登录失败，请检查 MIJIA_USERNAME 和 MIJIA_PASSWORD")
            return
    elif not token:
        logger.error("未设置 MIJIA_TOKEN，请设置 MIJIA_TOKEN 或同时设置 MIJIA_USERNAME 和 MIJIA_PASSWORD")
        return

    logger.info("BLE Scanner 启动 (API=%s)", api_url)

    stop_event = asyncio.Event()

    def _signal_handler(sig, frame):
        logger.info("收到停止信号，正在关闭...")
        stop_event.set()

    signal.signal(signal.SIGINT, _signal_handler)
    signal.signal(signal.SIGTERM, _signal_handler)

    while not stop_event.is_set():
        try:
            await scan_loop(api_url, token, BLE_ADAPTER)
        except Exception as e:
            logger.error("扫描循环异常: %s", e, exc_info=True)

        if not stop_event.is_set():
            logger.info("30 秒后重新加载设备列表并重启扫描...")
            try:
                await asyncio.wait_for(stop_event.wait(), timeout=30)
            except asyncio.TimeoutError:
                pass

    logger.info("BLE Scanner 已停止")
