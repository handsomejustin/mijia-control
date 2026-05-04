from datetime import datetime, timezone

from app.extensions import db


class BLESensorReading(db.Model):
    __tablename__ = "ble_sensor_readings"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    ble_device_id = db.Column(
        db.Integer, db.ForeignKey("ble_devices.id", ondelete="CASCADE"), nullable=False, index=True
    )
    values = db.Column(db.JSON, nullable=False)
    recorded_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), index=True)

    __table_args__ = (db.Index("ix_ble_readings_device_recorded", "ble_device_id", "recorded_at"),)

    def __repr__(self):
        return f"<BLESensorReading device_id={self.ble_device_id} values={self.values}>"
