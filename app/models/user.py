from datetime import datetime, timezone

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from app.extensions import db


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=True)
    password_hash = db.Column(db.String(256), nullable=False)
    display_name = db.Column(db.String(64), nullable=True)
    is_admin = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    last_login_at = db.Column(db.DateTime, nullable=True)

    xiaomi_auth = db.relationship("XiaomiAuth", backref="user", uselist=False, cascade="all, delete-orphan")
    device_caches = db.relationship("DeviceCache", backref="user", cascade="all, delete-orphan")
    home_caches = db.relationship("HomeCache", backref="user", cascade="all, delete-orphan")
    scene_caches = db.relationship("SceneCache", backref="user", cascade="all, delete-orphan")
    api_tokens = db.relationship("ApiToken", backref="user", cascade="all, delete-orphan")
    device_groups = db.relationship("DeviceGroup", backref="user", cascade="all, delete-orphan")
    automation_rules = db.relationship("AutomationRule", backref="user", cascade="all, delete-orphan")
    energy_logs = db.relationship("EnergyLog", backref="user", cascade="all, delete-orphan")

    def set_password(self, password: str):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f"<User {self.username}>"
