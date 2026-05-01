from app.extensions import db
from app.models.user import User


class AdminService:
    @staticmethod
    def list_users(page: int = 1, per_page: int = 20) -> dict:
        pagination = User.query.order_by(User.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        return {
            "users": [
                {
                    "id": u.id,
                    "username": u.username,
                    "email": u.email,
                    "display_name": u.display_name,
                    "is_admin": u.is_admin,
                    "is_active": u.is_active,
                    "created_at": u.created_at.isoformat() if u.created_at else None,
                    "last_login_at": u.last_login_at.isoformat() if u.last_login_at else None,
                    "device_count": len(u.device_caches),
                    "home_count": len(u.home_caches),
                }
                for u in pagination.items
            ],
            "total": pagination.total,
            "pages": pagination.pages,
            "page": page,
        }

    @staticmethod
    def toggle_user_active(user_id: int) -> dict:
        user = db.session.get(User, user_id)
        if not user:
            raise ValueError("用户不存在")
        if user.is_admin:
            raise ValueError("不能停用管理员账户")
        user.is_active = not user.is_active
        db.session.commit()
        return {"user_id": user.id, "is_active": user.is_active}

    @staticmethod
    def get_system_stats() -> dict:
        from app.models.device_cache import DeviceCache
        from app.models.home_cache import HomeCache
        from app.models.scene_cache import SceneCache
        from app.models.xiaomi_auth import XiaomiAuth
        from app.models.api_token import ApiToken

        return {
            "total_users": User.query.count(),
            "active_users": User.query.filter_by(is_active=True).count(),
            "admin_users": User.query.filter_by(is_admin=True).count(),
            "total_devices": DeviceCache.query.count(),
            "total_homes": HomeCache.query.count(),
            "total_scenes": SceneCache.query.count(),
            "linked_xiaomi_accounts": XiaomiAuth.query.filter_by(is_valid=True).count(),
            "active_api_tokens": ApiToken.query.count(),
        }
