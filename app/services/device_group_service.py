from app.extensions import db
from app.models.device_cache import DeviceCache
from app.models.device_group import DeviceGroup


class DeviceGroupService:
    @staticmethod
    def list_groups(user_id: int) -> list[dict]:
        groups = DeviceGroup.query.filter_by(user_id=user_id).order_by(DeviceGroup.sort_order, DeviceGroup.id).all()
        result = []
        for g in groups:
            device_count = g.devices.count()
            result.append({
                "id": g.id,
                "name": g.name,
                "icon": g.icon,
                "is_favorite_group": g.is_favorite_group,
                "sort_order": g.sort_order,
                "device_count": device_count,
                "created_at": g.created_at.isoformat() if g.created_at else None,
            })
        return result

    @staticmethod
    def create_group(user_id: int, name: str, icon: str = None) -> dict:
        existing = DeviceGroup.query.filter_by(user_id=user_id, name=name).first()
        if existing:
            raise ValueError(f"分组 '{name}' 已存在")
        group = DeviceGroup(user_id=user_id, name=name, icon=icon)
        db.session.add(group)
        db.session.commit()
        return {"id": group.id, "name": group.name, "icon": group.icon}

    @staticmethod
    def delete_group(user_id: int, group_id: int) -> None:
        group = DeviceGroup.query.filter_by(user_id=user_id, id=group_id).first()
        if not group:
            raise ValueError("分组不存在")
        if group.is_favorite_group:
            raise ValueError("无法删除收藏分组")
        db.session.delete(group)
        db.session.commit()

    @staticmethod
    def add_device(user_id: int, group_id: int, did: str) -> None:
        group = DeviceGroup.query.filter_by(user_id=user_id, id=group_id).first()
        if not group:
            raise ValueError("分组不存在")
        device = DeviceCache.query.filter_by(user_id=user_id, did=did).first()
        if not device:
            raise ValueError("设备不存在")
        if device in group.devices.all():
            return
        group.devices.append(device)
        db.session.commit()

    @staticmethod
    def remove_device(user_id: int, group_id: int, did: str) -> None:
        group = DeviceGroup.query.filter_by(user_id=user_id, id=group_id).first()
        if not group:
            raise ValueError("分组不存在")
        device = DeviceCache.query.filter_by(user_id=user_id, did=did).first()
        if not device:
            raise ValueError("设备不存在")
        if device in group.devices.all():
            group.devices.remove(device)
            db.session.commit()

    @staticmethod
    def toggle_favorite(user_id: int, did: str) -> dict:
        fav_group = DeviceGroup.query.filter_by(user_id=user_id, is_favorite_group=True).first()
        if not fav_group:
            fav_group = DeviceGroup(user_id=user_id, name="收藏", icon="star", is_favorite_group=True)
            db.session.add(fav_group)
            db.session.flush()

        device = DeviceCache.query.filter_by(user_id=user_id, did=did).first()
        if not device:
            raise ValueError("设备不存在")

        if device in fav_group.devices.all():
            fav_group.devices.remove(device)
            db.session.commit()
            return {"did": did, "is_favorite": False}
        else:
            fav_group.devices.append(device)
            db.session.commit()
            return {"did": did, "is_favorite": True}

    @staticmethod
    def is_favorite(user_id: int, did: str) -> bool:
        fav_group = DeviceGroup.query.filter_by(user_id=user_id, is_favorite_group=True).first()
        if not fav_group:
            return False
        device = DeviceCache.query.filter_by(user_id=user_id, did=did).first()
        if not device:
            return False
        return device in fav_group.devices.all()

    @staticmethod
    def get_group_devices(user_id: int, group_id: int) -> list[dict]:
        group = DeviceGroup.query.filter_by(user_id=user_id, id=group_id).first()
        if not group:
            raise ValueError("分组不存在")
        return [
            {
                "did": d.did,
                "name": d.name,
                "model": d.model,
                "is_online": d.is_online,
            }
            for d in group.devices.all()
        ]
