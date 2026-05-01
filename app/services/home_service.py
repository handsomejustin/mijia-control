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
