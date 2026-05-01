from datetime import datetime, timezone

from app.extensions import db


class SceneCache(db.Model):
    __tablename__ = "scene_caches"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    home_id = db.Column(db.String(64), nullable=False)
    scene_id = db.Column(db.String(64), nullable=False)
    name = db.Column(db.String(128), nullable=False)
    raw_data = db.Column(db.JSON, nullable=True)
    cached_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (db.UniqueConstraint("user_id", "scene_id", name="uk_scene_caches_user_scene"),)

    def __repr__(self):
        return f"<SceneCache {self.name} scene_id={self.scene_id}>"
