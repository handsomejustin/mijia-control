from datetime import datetime, timezone

from app.extensions import db
from app.models.home_cache import HomeCache
from app.utils.mijia_pool import api_pool


class HomeService:
    @staticmethod
    def list_homes(user_id: int, refresh: bool = False) -> list[dict]:
        if refresh:
            return HomeService._refresh_homes(user_id)

        cached = HomeCache.query.filter_by(user_id=user_id).all()
        if not cached:
            return HomeService._refresh_homes(user_id)

        return [
            {
                "home_id": h.home_id,
                "name": h.name,
                "room_list": h.room_list,
            }
            for h in cached
        ]

    @staticmethod
    def get_home(user_id: int, home_id: str) -> dict:
        cached = HomeCache.query.filter_by(user_id=user_id, home_id=home_id).first()
        if not cached:
            raise ValueError(f"家庭 {home_id} 未找到")
        return {
            "home_id": cached.home_id,
            "name": cached.name,
            "room_list": cached.room_list,
            "raw_data": cached.raw_data,
        }

    @staticmethod
    def get_room_devices(user_id: int, home_id: str, room_id: str) -> dict:
        """获取指定房间下的设备列表"""
        from app.services.device_service import DeviceService

        home = HomeCache.query.filter_by(user_id=user_id, home_id=home_id).first()
        if not home:
            raise ValueError(f"家庭 {home_id} 未找到")

        room = None
        for r in (home.room_list or []):
            if str(r.get("id")) == str(room_id):
                room = r
                break
        if not room:
            raise ValueError(f"房间 {room_id} 未找到")

        room_dids = set(str(d) for d in room.get("dids", []))
        all_devices = DeviceService.list_devices(user_id, home_id=home_id)
        room_devices = [d for d in all_devices if str(d["did"]) in room_dids]

        return {
            "home": {"home_id": home.home_id, "name": home.name},
            "room": {"id": room_id, "name": room.get("name", ""), "icon": room.get("icon", "")},
            "devices": room_devices,
        }

    @staticmethod
    def _refresh_homes(user_id: int) -> list[dict]:
        api = api_pool.get_api(user_id)
        homes_raw = api.get_homes_list()

        for h in homes_raw:
            existing = HomeCache.query.filter_by(user_id=user_id, home_id=str(h["id"])).first()
            room_list = h.get("roomlist", [])
            if existing:
                existing.name = h.get("name", existing.name)
                existing.room_list = room_list
                existing.raw_data = h
                existing.cached_at = datetime.now(timezone.utc)
            else:
                cache = HomeCache(
                    user_id=user_id,
                    home_id=str(h["id"]),
                    name=h.get("name", ""),
                    room_list=room_list,
                    raw_data=h,
                )
                db.session.add(cache)

        db.session.commit()

        return [
            {
                "home_id": h.home_id,
                "name": h.name,
                "room_list": h.room_list,
            }
            for h in HomeCache.query.filter_by(user_id=user_id).all()
        ]
