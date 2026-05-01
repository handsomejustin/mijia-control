from datetime import datetime, timezone

from app.extensions import db


class AutomationRule(db.Model):
    __tablename__ = "automation_rules"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name = db.Column(db.String(128), nullable=False)
    is_enabled = db.Column(db.Boolean, default=True)
    trigger_type = db.Column(db.String(32), nullable=False)  # cron, interval, sunrise, sunset
    trigger_config = db.Column(db.JSON, nullable=False)  # cron_expr, interval_seconds, etc.
    action_type = db.Column(db.String(32), nullable=False)  # set_property, run_scene
    action_config = db.Column(db.JSON, nullable=False)  # did, prop_name, value, scene_id
    last_triggered_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f"<AutomationRule {self.name} user={self.user_id}>"
