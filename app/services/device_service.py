from datetime import datetime, timezone

from mijiaAPI import mijiaAPI, mijiaDevice, get_device_info

from app.extensions import db
from app.models.device_cache import DeviceCache
from app.utils.mijia_pool import api_pool

# 摄像头型号前缀
_CAMERA_MODEL_PREFIXES = ("chuangmi.camera.", "mijia.camera.", "isa.camera.")


class DeviceService:
    @staticmethod
    def list_devices(user_id: int, home_id: str = None, refresh: bool = False) -> list[dict]:
        if refresh:
            return DeviceService._refresh_devices(user_id, home_id)

        query = DeviceCache.query.filter_by(user_id=user_id)
        if home_id:
            query = query.filter_by(home_id=home_id)
        cached = query.all()

        if not cached:
            return DeviceService._refresh_devices(user_id, home_id)

        return [
            {
                "did": d.did,
                "name": d.name,
                "model": d.model,
                "home_id": d.home_id,
                "is_online": d.is_online,
                "spec_data": d.spec_data,
                "rated_power": d.rated_power,
            }
            for d in cached
        ]

    @staticmethod
    def get_device(user_id: int, did: str) -> dict:
        cached = DeviceCache.query.filter_by(user_id=user_id, did=did).first()
        if not cached:
            raise ValueError(f"设备 {did} 未找到")

        spec_data = cached.spec_data
        if not spec_data:
            api = api_pool.get_api(user_id)
            spec_data = get_device_info(cached.model)
            cached.spec_data = spec_data
            db.session.commit()

        is_camera = any(cached.model.startswith(p) for p in _CAMERA_MODEL_PREFIXES)
        raw = cached.raw_data or {}

        return {
            "did": cached.did,
            "name": cached.name,
            "model": cached.model,
            "home_id": cached.home_id,
            "is_online": cached.is_online,
            "is_camera": is_camera,
            "camera_ip": raw.get("localip") if is_camera else None,
            "spec_data": spec_data,
            "rated_power": cached.rated_power,
        }

    @staticmethod
    def get_stream_info(user_id: int, did: str) -> dict:
        """获取摄像头设备的流信息（IP、Token 等），供 go2rtc 使用"""
        cached = DeviceCache.query.filter_by(user_id=user_id, did=did).first()
        if not cached:
            raise ValueError(f"设备 {did} 未找到")

        is_camera = any(cached.model.startswith(p) for p in _CAMERA_MODEL_PREFIXES)
        if not is_camera:
            raise ValueError(f"设备 {cached.name} 不是摄像头型号")

        raw = cached.raw_data or {}
        localip = raw.get("localip")
        token = raw.get("token")

        if not localip or not token:
            raise ValueError(f"摄像头 {cached.name} 缺少 IP 或 Token 信息，请刷新设备列表")

        return {
            "did": cached.did,
            "name": cached.name,
            "model": cached.model,
            "localip": localip,
            "token": token,
            "is_online": cached.is_online,
        }

    @staticmethod
    def go2rtc_config(user_id: int) -> dict:
        """为用户的所有摄像头生成 go2rtc 配置"""
        cameras = []
        for prefix in _CAMERA_MODEL_PREFIXES:
            devices = DeviceCache.query.filter(
                DeviceCache.user_id == user_id,
                DeviceCache.model.like(f"{prefix}%"),
            ).all()
            cameras.extend(devices)

        streams = {}
        for cam in cameras:
            raw = cam.raw_data or {}
            localip = raw.get("localip")
            token = raw.get("token")
            if localip and token:
                stream_name = cam.name.replace(" ", "_")
                streams[stream_name] = f"xiaomi://{token}@{localip}"

        return {"streams": streams}

    @staticmethod
    def get_property(user_id: int, did: str, prop_name: str) -> dict:
        api = api_pool.get_api(user_id)
        device = mijiaDevice(api, did=did)
        value = device.get(prop_name)
        prop_info = device.prop_list.get(prop_name)
        return {
            "did": did,
            "prop_name": prop_name,
            "value": value,
            "unit": prop_info.unit if prop_info else None,
        }

    @staticmethod
    def set_property(user_id: int, did: str, prop_name: str, value) -> dict:
        api = api_pool.get_api(user_id)
        device = mijiaDevice(api, did=did)
        device.set(prop_name, value)
        _emit_device_update(user_id, did, "property_change", {"prop_name": prop_name, "value": value})
        return {"did": did, "prop_name": prop_name, "value": value}

    @staticmethod
    def run_action(user_id: int, did: str, action_name: str, value=None) -> dict:
        api = api_pool.get_api(user_id)
        device = mijiaDevice(api, did=did)
        kwargs = {"value": value} if value is not None else {}
        device.run_action(action_name, **kwargs)
        _emit_device_update(user_id, did, "action_executed", {"action_name": action_name, "status": "executed"})
        return {"did": did, "action_name": action_name, "status": "executed"}

    @staticmethod
    def update_rated_power(user_id: int, did: str, rated_power: float | None) -> dict:
        cached = DeviceCache.query.filter_by(user_id=user_id, did=did).first()
        if not cached:
            raise ValueError(f"设备 {did} 未找到")
        cached.rated_power = rated_power
        db.session.commit()
        return {"did": did, "rated_power": rated_power}

    @staticmethod
    def _refresh_devices(user_id: int, home_id: str = None) -> list[dict]:
        api = api_pool.get_api(user_id)

        if home_id:
            devices_raw = api.get_devices_list(home_id=home_id)
        else:
            devices_raw = api.get_devices_list()

        for d in devices_raw:
            existing = DeviceCache.query.filter_by(user_id=user_id, did=d["did"]).first()
            if existing:
                existing.name = d.get("name", existing.name)
                existing.model = d.get("model", existing.model)
                existing.home_id = d.get("home_id", existing.home_id)
                existing.is_online = d.get("isOnline", existing.is_online)
                existing.raw_data = d
                existing.cached_at = datetime.now(timezone.utc)
            else:
                cache = DeviceCache(
                    user_id=user_id,
                    did=d["did"],
                    name=d.get("name", ""),
                    model=d.get("model", ""),
                    home_id=d.get("home_id"),
                    is_online=d.get("isOnline", True),
                    raw_data=d,
                )
                db.session.add(cache)

        db.session.commit()

        query = DeviceCache.query.filter_by(user_id=user_id)
        if home_id:
            query = query.filter_by(home_id=home_id)
        return [
            {
                "did": d.did,
                "name": d.name,
                "model": d.model,
                "home_id": d.home_id,
                "is_online": d.is_online,
            }
            for d in query.all()
        ]


def _emit_device_update(user_id, did, update_type, data):
    try:
        from app.web.socketio import emit_device_update
        emit_device_update(user_id, did, update_type, data)
    except Exception:
        pass
