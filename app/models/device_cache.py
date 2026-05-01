from datetime import datetime, timezone

from app.extensions import db


class DeviceCache(db.Model):
    __tablename__ = "device_caches"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    home_id = db.Column(db.String(64), nullable=True)
    did = db.Column(db.String(64), nullable=False)
    name = db.Column(db.String(128), nullable=False)
    model = db.Column(db.String(128), nullable=True)
    is_online = db.Column(db.Boolean, default=True)
    spec_data = db.Column(db.JSON, nullable=True)
    raw_data = db.Column(db.JSON, nullable=True)
    rated_power = db.Column(db.Float, nullable=True, comment="额定功率(W)，用于估算能耗")
    cached_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (db.UniqueConstraint("user_id", "did", name="uk_device_caches_user_did"),)

    def __repr__(self):
        return f"<DeviceCache {self.name} did={self.did}>"
