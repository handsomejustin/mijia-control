from datetime import datetime, timezone

from app.extensions import db

device_group_members = db.Table(
    "device_group_members",
    db.Column("group_id", db.Integer, db.ForeignKey("device_groups.id", ondelete="CASCADE"), primary_key=True),
    db.Column("device_id", db.Integer, db.ForeignKey("device_caches.id", ondelete="CASCADE"), primary_key=True),
)


class DeviceGroup(db.Model):
    __tablename__ = "device_groups"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name = db.Column(db.String(64), nullable=False)
    icon = db.Column(db.String(32), nullable=True)
    is_favorite_group = db.Column(db.Boolean, default=False)
    sort_order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    devices = db.relationship("DeviceCache", secondary=device_group_members, backref=db.backref("groups", lazy="dynamic"), lazy="dynamic")

    __table_args__ = (db.UniqueConstraint("user_id", "name", name="uk_device_groups_user_name"),)

    def __repr__(self):
        return f"<DeviceGroup {self.name} user={self.user_id}>"
