from functools import wraps

from flask import abort, request
from flask_login import current_user

from app.services.auth_service import AuthService


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            abort(403)
        return f(*args, **kwargs)

    return decorated


def api_token_required(f):
    """验证 Authorization: Bearer <api_token> 中的 API 令牌"""
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return {"success": False, "message": "缺少有效的认证信息"}, 401

        token_str = auth_header[7:]
        try:
            user = AuthService.validate_api_token(token_str)
            request._api_token_user = user
        except ValueError as e:
            return {"success": False, "message": str(e)}, 401

        return f(*args, **kwargs)

    return decorated


def auth_required(f):
    """双轨认证：支持 Session / JWT / API Token，任一通过即可"""
    @wraps(f)
    def decorated(*args, **kwargs):
        # 1. Session 认证（Web 浏览器）
        if current_user.is_authenticated:
            return f(*args, **kwargs)

        # 2. JWT / API Token 认证
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token_str = auth_header[7:]

            # 先尝试 API Token
            try:
                user = AuthService.validate_api_token(token_str)
                request._api_token_user = user
                return f(*args, **kwargs)
            except ValueError:
                pass

            # 再尝试 JWT
            try:
                from flask_jwt_extended import verify_jwt_in_request
                verify_jwt_in_request()
                return f(*args, **kwargs)
            except Exception:
                pass

        return {"success": False, "message": "未认证，请登录或提供有效令牌"}, 401

    return decorated


def get_current_user_id():
    """获取当前用户 ID，兼容 Session / JWT / API Token 三种认证方式"""
    if current_user.is_authenticated:
        return current_user.id

    # API Token 认证
    api_user = getattr(request, "_api_token_user", None)
    if api_user:
        return api_user.id

    # JWT 认证
    try:
        from flask_jwt_extended import get_jwt_identity
        identity = get_jwt_identity()
        if identity:
            return int(identity)
    except Exception:
        pass

    return None
