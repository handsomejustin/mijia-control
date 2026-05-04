from app.extensions import db


class BLEDevice(db.Model):
    __tablename__ = "ble_devices"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    did = db.Column(db.String(64), nullable=False, unique=True)
    mac_address = db.Column(db.String(17), nullable=False)
    bindkey = db.Column(db.String(32), nullable=True)
    model = db.Column(db.String(128), nullable=True)
    capabilities = db.Column(db.JSON, default=list)
    is_enabled = db.Column(db.Boolean, default=True)
    last_seen_at = db.Column(db.DateTime, nullable=True)

    def __repr__(self):
        return f"<BLEDevice {self.did} mac={self.mac_address}>"
