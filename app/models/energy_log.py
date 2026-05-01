from datetime import datetime, timezone

from app.extensions import db


class EnergyLog(db.Model):
    __tablename__ = "energy_logs"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    did = db.Column(db.String(64), nullable=False)
    prop_name = db.Column(db.String(64), nullable=False)
    value = db.Column(db.Float, nullable=False)
    unit = db.Column(db.String(16), nullable=True)
    logged_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), index=True)

    __table_args__ = (db.Index("ix_energy_logs_user_did_logged", "user_id", "did", "logged_at"),)

    def __repr__(self):
        return f"<EnergyLog {self.did} {self.prop_name}={self.value}>"
