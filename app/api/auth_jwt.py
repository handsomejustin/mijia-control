from flask import Blueprint, request
from flask_jwt_extended import create_access_token, create_refresh_token, get_jwt_identity, jwt_required

from app.extensions import limiter
from app.schemas.auth import JwtLoginSchema
from app.services.auth_service import AuthService
from app.utils.response import error, success

auth_jwt_ns = Blueprint("auth_jwt", __name__, url_prefix="/auth/jwt")

jwt_login_schema = JwtLoginSchema()


@auth_jwt_ns.route("/login", methods=["POST"])
@limiter.limit("10 per minute")
def jwt_login():
    """JWT 登录（获取 access_token + refresh_token）
    ---
    tags:
      - 认证
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required: [username, password]
          properties:
            username:
              type: string
            password:
              type: string
    responses:
      200:
        description: 返回 JWT 令牌
        schema:
          type: object
          properties:
            access_token:
              type: string
            refresh_token:
              type: string
      401:
        description: 用户名或密码错误
    """
    try:
        data = jwt_login_schema.load(request.get_json(silent=True) or {})
    except Exception as e:
        return error(f"输入验证失败: {e}", 400)

    try:
        user = AuthService.authenticate(data["username"], data["password"])
        access_token = create_access_token(identity=str(user.id))
        refresh_token = create_refresh_token(identity=str(user.id))
        return success({
            "access_token": access_token,
            "refresh_token": refresh_token,
            "user_id": user.id,
            "username": user.username,
        })
    except ValueError as e:
        return error(str(e), 401)


@auth_jwt_ns.route("/refresh", methods=["POST"])
@jwt_required(refresh=True)
@limiter.limit("10 per minute")
def jwt_refresh():
    """刷新 access_token
    ---
    tags:
      - 认证
    security:
      - bearerAuth: []
    responses:
      200:
        description: 返回新的 access_token
      401:
        description: refresh_token 无效或过期
    """
    identity = get_jwt_identity()
    access_token = create_access_token(identity=identity)
    return success({"access_token": access_token})
