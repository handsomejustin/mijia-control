from datetime import datetime, timezone

from app.extensions import db
from app.models.api_token import ApiToken
from app.models.user import User


class AuthService:
    @staticmethod
    def register(username: str, password: str, email: str = None) -> User:
        if User.query.filter_by(username=username).first():
            raise ValueError(f"用户名 '{username}' 已存在")
        if email and User.query.filter_by(email=email).first():
            raise ValueError(f"邮箱 '{email}' 已被使用")
        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        return user

    @staticmethod
    def authenticate(username: str, password: str) -> User:
        user = User.query.filter_by(username=username).first()
        if not user or not user.check_password(password):
            raise ValueError("用户名或密码错误")
        if not user.is_active:
            raise ValueError("账户已被停用")
        user.last_login_at = datetime.now(timezone.utc)
        db.session.commit()
        return user

    @staticmethod
    def create_api_token(user_id: int, name: str = None, permissions: str = "read_write") -> tuple[str, ApiToken]:
        raw_token, token_hash = ApiToken.generate_token()
        token = ApiToken(user_id=user_id, token_hash=token_hash, name=name, permissions=permissions)
        db.session.add(token)
        db.session.commit()
        return raw_token, token

    @staticmethod
    def change_password(user_id: int, old_password: str, new_password: str) -> None:
        user = User.query.get(user_id)
        if not user:
            raise ValueError("用户不存在")
        if not user.check_password(old_password):
            raise ValueError("旧密码不正确")
        if len(new_password) < 6:
            raise ValueError("新密码长度至少 6 位")
        user.set_password(new_password)
        db.session.commit()

    @staticmethod
    def validate_api_token(raw_token: str) -> User:
        token_hash = ApiToken.hash_token(raw_token)
        token = ApiToken.query.filter_by(token_hash=token_hash).first()
        if not token:
            raise ValueError("无效的 API 令牌")
        if token.is_expired():
            raise ValueError("API 令牌已过期")
        token.touch()
        db.session.commit()
        return token.user
