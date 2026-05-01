from datetime import datetime, timezone

from app.extensions import db


class XiaomiAuth(db.Model):
    __tablename__ = "xiaomi_auths"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    auth_data = db.Column(db.JSON, nullable=False)
    xiaomi_user_id = db.Column(db.String(64), nullable=True)
    is_valid = db.Column(db.Boolean, default=True)
    expires_at = db.Column(db.DateTime, nullable=True)
    last_refreshed = db.Column(db.DateTime, nullable=True)

    def mark_refreshed(self):
        self.last_refreshed = datetime.now(timezone.utc)
        self.is_valid = True

    def mark_invalid(self):
        self.is_valid = False

    def __repr__(self):
        return f"<XiaomiAuth user_id={self.user_id} valid={self.is_valid}>"
