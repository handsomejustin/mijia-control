from datetime import datetime, timezone

from app.extensions import db


class HomeCache(db.Model):
    __tablename__ = "home_caches"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    home_id = db.Column(db.String(64), nullable=False)
    name = db.Column(db.String(128), nullable=False)
    room_list = db.Column(db.JSON, nullable=True)
    raw_data = db.Column(db.JSON, nullable=True)
    cached_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (db.UniqueConstraint("user_id", "home_id", name="uk_home_caches_user_home"),)

    def __repr__(self):
        return f"<HomeCache {self.name} home_id={self.home_id}>"
