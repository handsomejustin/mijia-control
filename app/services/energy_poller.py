import logging
import threading
import time

from mijiaAPI import mijiaDevice

from app.models.device_cache import DeviceCache
from app.services.energy_service import EnergyService
from app.utils.mijia_pool import api_pool

logger = logging.getLogger(__name__)

POLL_INTERVAL_SECONDS = 300  # 5 分钟


def _estimate_power(device: DeviceCache, api) -> float | None:
    """根据设备属性估算当前功率(W)。"""
    spec = device.spec_data or {}
    prop_names = {p.get("name") for p in spec.get("properties", [])}
    has_on = "on" in prop_names
    has_brightness = "brightness" in prop_names

    dev = mijiaDevice(api, did=device.did)

    if has_on:
        is_on = dev.get("on")
        if not is_on:
            return 0.0

    brightness = None
    if has_brightness:
        try:
            brightness = dev.get("brightness")
        except Exception:
            pass

    if brightness is not None:
        return round(device.rated_power * brightness / 100, 2)
    return device.rated_power


def poll_once(app):
    """单次轮询：遍历所有配置了额定功率的设备，采集并记录估算功耗。"""
    with app.app_context():
        devices = DeviceCache.query.filter(DeviceCache.rated_power.isnot(None)).all()
        if not devices:
            return

        for device in devices:
            try:
                api = api_pool.get_api(device.user_id)
                power = _estimate_power(device, api)
                if power is not None:
                    EnergyService.log_energy(
                        device.user_id, device.did, "estimated_power", power, unit="W"
                    )
            except Exception:
                logger.debug("能耗轮询跳过设备 %s", device.did, exc_info=True)


def _poll_loop(app):
    """后台轮询主循环。"""
    while True:
        try:
            poll_once(app)
        except Exception:
            logger.error("能耗轮询异常", exc_info=True)
        time.sleep(POLL_INTERVAL_SECONDS)


def start_energy_poller(app):
    """启动能耗后台轮询线程（daemon，随主进程退出）。"""
    thread = threading.Thread(target=_poll_loop, args=(app,), daemon=True)
    thread.start()
    logger.info("能耗轮询线程已启动，间隔 %ds", POLL_INTERVAL_SECONDS)
