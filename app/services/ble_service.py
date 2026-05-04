import logging
from datetime import datetime, timedelta, timezone

from app.extensions import db
from app.models.ble_device import BLEDevice
from app.models.ble_reading import BLESensorReading
from app.utils.mijia_pool import api_pool

logger = logging.getLogger(__name__)


class BLEService:
    @staticmethod
    def register_device(user_id: int, did: str, mac_address: str, bindkey: str | None = None) -> dict:
        existing = BLEDevice.query.filter_by(did=did).first()
        if existing:
            raise ValueError(f"设备 {did} 已注册")

        mac_address = mac_address.upper().strip()

        if not bindkey:
            bindkey = BLEService._fetch_bindkey(user_id, did)

        device = BLEDevice(
            user_id=user_id,
            did=did,
            mac_address=mac_address,
            bindkey=bindkey,
            model="lywsd03mmc",
            capabilities=["temperature", "humidity", "battery"],
        )
        db.session.add(device)
        db.session.commit()
        return BLEService._device_to_dict(device)

    @staticmethod
    def list_devices(user_id: int) -> list[dict]:
        devices = BLEDevice.query.filter_by(user_id=user_id).all()
        result = []
        for d in devices:
            info = BLEService._device_to_dict(d)
            latest = BLEService._get_latest_reading(d.id)
            info["latest_reading"] = latest
            result.append(info)
        return result

    @staticmethod
    def get_device(user_id: int, did: str) -> dict:
        device = BLEDevice.query.filter_by(user_id=user_id, did=did).first()
        if not device:
            raise ValueError(f"BLE 设备 {did} 未找到")
        info = BLEService._device_to_dict(device)
        info["latest_reading"] = BLEService._get_latest_reading(device.id)
        return info

    @staticmethod
    def delete_device(user_id: int, did: str) -> None:
        device = BLEDevice.query.filter_by(user_id=user_id, did=did).first()
        if not device:
            raise ValueError(f"BLE 设备 {did} 未找到")
        BLESensorReading.query.filter_by(ble_device_id=device.id).delete()
        db.session.delete(device)
        db.session.commit()

    @staticmethod
    def get_readings(did: str, hours: int = 24, limit: int = 200) -> list[dict]:
        device = BLEDevice.query.filter_by(did=did).first()
        if not device:
            raise ValueError(f"BLE 设备 {did} 未找到")

        since = datetime.now(timezone.utc) - timedelta(hours=hours)
        query = BLESensorReading.query.filter(
            BLESensorReading.ble_device_id == device.id,
            BLESensorReading.recorded_at >= since,
        ).order_by(BLESensorReading.recorded_at.desc())

        readings = query.limit(limit).all()
        return [
            {
                "values": r.values,
                "recorded_at": r.recorded_at.isoformat() if r.recorded_at else None,
            }
            for r in readings
        ]

    @staticmethod
    def ingest_reading(did: str, values: dict) -> dict:
        device = BLEDevice.query.filter_by(did=did, is_enabled=True).first()
        if not device:
            raise ValueError(f"BLE 设备 {did} 未找到或已禁用")

        reading = BLESensorReading(
            ble_device_id=device.id,
            values=values,
        )
        db.session.add(reading)
        device.last_seen_at = datetime.now(timezone.utc)
        db.session.commit()

        BLEService._check_automation_rules(device.user_id, device.did, values)

        return {"device_id": device.id, "values": values}

    @staticmethod
    def refresh_bindkey(user_id: int, did: str, bindkey: str | None = None) -> dict:
        device = BLEDevice.query.filter_by(user_id=user_id, did=did).first()
        if not device:
            raise ValueError(f"BLE 设备 {did} 未找到")

        if not bindkey:
            bindkey = BLEService._fetch_bindkey(user_id, did)

        device.bindkey = bindkey
        db.session.commit()
        return {"did": did, "bindkey": bindkey}

    @staticmethod
    def get_all_enabled_devices() -> list[dict]:
        devices = BLEDevice.query.filter_by(is_enabled=True).all()
        return [
            {
                "did": d.did,
                "mac_address": d.mac_address,
                "bindkey": d.bindkey,
                "model": d.model,
                "capabilities": d.capabilities,
            }
            for d in devices
        ]

    @staticmethod
    def _fetch_bindkey(user_id: int, did: str) -> str | None:
        try:
            api = api_pool.get_api(user_id)
            result = api._request("/v2/device/bltconfig", {"did": did})
            bindkey = result.get("result", {}).get("bindkey") or result.get("result", {}).get("ble_key")
            if bindkey:
                logger.info("成功从云端获取 bindkey: did=%s", did)
                return bindkey
            logger.warning("云端返回的 bindkey 为空: did=%s, response=%s", did, result)
        except Exception as e:
            logger.warning("从云端获取 bindkey 失败: did=%s, error=%s", did, e)
        return None

    @staticmethod
    def _get_latest_reading(ble_device_id: int) -> dict | None:
        reading = (
            BLESensorReading.query.filter_by(ble_device_id=ble_device_id)
            .order_by(BLESensorReading.recorded_at.desc())
            .first()
        )
        if not reading:
            return None
        return {
            "values": reading.values,
            "recorded_at": reading.recorded_at.isoformat() if reading.recorded_at else None,
        }

    @staticmethod
    def _check_automation_rules(user_id: int, did: str, values: dict):
        from app.models.automation_rule import AutomationRule

        rules = AutomationRule.query.filter_by(
            user_id=user_id, trigger_type="ble_sensor", is_enabled=True
        ).all()

        for rule in rules:
            cfg = rule.trigger_config
            if cfg.get("did") != did:
                continue

            metric = cfg.get("metric")
            operator = cfg.get("operator")
            threshold = cfg.get("threshold")
            cooldown = cfg.get("cooldown_seconds", 300)

            if metric not in values:
                continue

            actual = values[metric]
            if not BLEService._evaluate_condition(actual, operator, threshold):
                continue

            if rule.last_triggered_at:
                elapsed = (datetime.now(timezone.utc) - rule.last_triggered_at).total_seconds()
                if elapsed < cooldown:
                    continue

            from app.services.automation_service import AutomationService

            AutomationService.execute_rule(rule)

    @staticmethod
    def _evaluate_condition(actual: float, operator: str, threshold: float) -> bool:
        ops = {
            ">": lambda a, t: a > t,
            ">=": lambda a, t: a >= t,
            "<": lambda a, t: a < t,
            "<=": lambda a, t: a <= t,
            "==": lambda a, t: a == t,
        }
        fn = ops.get(operator)
        return fn(actual, threshold) if fn else False

    @staticmethod
    def _device_to_dict(device: BLEDevice) -> dict:
        return {
            "id": device.id,
            "did": device.did,
            "mac_address": device.mac_address,
            "model": device.model,
            "capabilities": device.capabilities or [],
            "is_enabled": device.is_enabled,
            "last_seen_at": device.last_seen_at.isoformat() if device.last_seen_at else None,
        }
