from flask import Blueprint, request
from flask_login import current_user, login_user, logout_user

from app.extensions import limiter
from app.schemas.auth import RegisterSchema, LoginSchema
from app.services.auth_service import AuthService
from app.utils.decorators import auth_required
from app.utils.response import error, success

auth_ns = Blueprint("auth", __name__, url_prefix="/auth")

register_schema = RegisterSchema()
login_schema = LoginSchema()


@auth_ns.route("/register", methods=["POST"])
@limiter.limit("5 per minute")
def register():
    """用户注册
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
              minLength: 2
              maxLength: 64
            password:
              type: string
              minLength: 6
              maxLength: 128
            email:
              type: string
              format: email
    responses:
      201:
        description: 注册成功
      400:
        description: 参数错误或用户名已存在
    """
    try:
        data = register_schema.load(request.get_json(silent=True) or {})
    except Exception as e:
        return error(f"输入验证失败: {e}", 400)

    try:
        user = AuthService.register(data["username"], data["password"], data.get("email"))
        return success({"user_id": user.id, "username": user.username}, "注册成功", 201)
    except ValueError as e:
        return error(str(e), 400)


@auth_ns.route("/login", methods=["POST"])
@limiter.limit("5 per minute")
def login():
    """用户登录（Session）
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
        description: 登录成功
      401:
        description: 用户名或密码错误
    """
    try:
        data = login_schema.load(request.get_json(silent=True) or {})
    except Exception as e:
        return error(f"输入验证失败: {e}", 400)

    try:
        user = AuthService.authenticate(data["username"], data["password"])
        login_user(user)
        return success({"user_id": user.id, "username": user.username, "is_admin": user.is_admin})
    except ValueError as e:
        return error(str(e), 401)


@auth_ns.route("/logout", methods=["POST"])
@limiter.limit("10 per minute")
def logout():
    """退出登录
    ---
    tags:
      - 认证
    responses:
      200:
        description: 已退出登录
    """
    logout_user()
    return success(message="已退出登录")


@auth_ns.route("/me", methods=["GET"])
@auth_required
@limiter.limit("60 per minute")
def me():
    """获取当前用户信息
    ---
    tags:
      - 认证
    security:
      - cookieAuth: []
      - bearerAuth: []
    responses:
      200:
        description: 用户信息
      401:
        description: 未认证
    """
    from app.utils.decorators import get_current_user_id
    user_id = get_current_user_id()
    from app.models.user import User
    user = User.query.get(user_id)
    if not user:
        return error("用户不存在", 404)
    return success({
        "user_id": user.id,
        "username": user.username,
        "email": user.email,
        "display_name": user.display_name,
        "is_admin": user.is_admin,
    })


@auth_ns.route("/change-password", methods=["POST"])
@auth_required
@limiter.limit("3 per minute")
def change_password():
    """修改密码
    ---
    tags:
      - 认证
    security:
      - cookieAuth: []
      - bearerAuth: []
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required: [old_password, new_password]
          properties:
            old_password:
              type: string
            new_password:
              type: string
              minLength: 6
    responses:
      200:
        description: 密码修改成功
      400:
        description: 参数错误
    """
    from app.utils.decorators import get_current_user_id
    data = request.get_json(silent=True) or {}
    old_password = data.get("old_password")
    new_password = data.get("new_password")
    if not old_password or not new_password:
        return error("缺少 old_password 或 new_password", 400)
    try:
        AuthService.change_password(get_current_user_id(), old_password, new_password)
        return success(message="密码修改成功")
    except ValueError as e:
        return error(str(e), 400)
