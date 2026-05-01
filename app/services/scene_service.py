from datetime import datetime, timezone

from app.extensions import db
from app.models.scene_cache import SceneCache
from app.utils.mijia_pool import api_pool


class SceneService:
    @staticmethod
    def list_scenes(user_id: int, home_id: str = None, refresh: bool = False) -> list[dict]:
        if refresh:
            return SceneService._refresh_scenes(user_id)

        query = SceneCache.query.filter_by(user_id=user_id)
        if home_id:
            query = query.filter_by(home_id=home_id)
        cached = query.all()

        if not cached:
            return SceneService._refresh_scenes(user_id)

        return [
            {
                "scene_id": s.scene_id,
                "name": s.name,
                "home_id": s.home_id,
            }
            for s in cached
        ]

    @staticmethod
    def run_scene(user_id: int, scene_id: str) -> dict:
        api = api_pool.get_api(user_id)
        scene = SceneCache.query.filter_by(user_id=user_id, scene_id=scene_id).first()
        home_id = scene.home_id if scene else None
        api.run_scene(scene_id=scene_id, home_id=home_id)
        return {"scene_id": scene_id, "status": "executed"}

    @staticmethod
    def _refresh_scenes(user_id: int) -> list[dict]:
        api = api_pool.get_api(user_id)
        scenes_raw = api.get_scenes_list()

        for s in scenes_raw:
            existing = SceneCache.query.filter_by(user_id=user_id, scene_id=str(s.get("scene_id", s.get("id", "")))).first()
            if existing:
                existing.name = s.get("name", existing.name)
                existing.home_id = str(s.get("home_id", existing.home_id))
                existing.raw_data = s
                existing.cached_at = datetime.now(timezone.utc)
            else:
                cache = SceneCache(
                    user_id=user_id,
                    home_id=str(s.get("home_id", "")),
                    scene_id=str(s.get("scene_id", s.get("id", ""))),
                    name=s.get("name", ""),
                    raw_data=s,
                )
                db.session.add(cache)

        db.session.commit()

        return [
            {
                "scene_id": s.scene_id,
                "name": s.name,
                "home_id": s.home_id,
            }
            for s in SceneCache.query.filter_by(user_id=user_id).all()
        ]
