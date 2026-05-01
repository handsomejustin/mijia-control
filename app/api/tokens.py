from flask import Blueprint, request

from app.extensions import db, limiter
from app.models.api_token import ApiToken
from app.schemas.token import CreateTokenSchema
from app.services.auth_service import AuthService
from app.utils.decorators import auth_required, get_current_user_id
from app.utils.response import error, success

tokens_ns = Blueprint("tokens", __name__, url_prefix="/tokens")

create_token_schema = CreateTokenSchema()


@tokens_ns.route("/", methods=["GET"])
@auth_required
@limiter.limit("60 per minute")
def list_tokens():
    """列出当前用户的 API 令牌
    ---
    tags:
      - API 令牌
    security:
      - cookieAuth: []
      - bearerAuth: []
    responses:
      200:
        description: 令牌列表
    """
    user_id = get_current_user_id()
    tokens = ApiToken.query.filter_by(user_id=user_id).all()
    return success([
        {
            "id": t.id,
            "name": t.name,
            "permissions": t.permissions,
            "last_used_at": t.last_used_at.isoformat() if t.last_used_at else None,
            "created_at": t.created_at.isoformat() if t.created_at else None,
            "expires_at": t.expires_at.isoformat() if t.expires_at else None,
        }
        for t in tokens
    ])


@tokens_ns.route("/", methods=["POST"])
@auth_required
@limiter.limit("10 per minute")
def create_token():
    """创建新的 API 令牌（原始 token 仅返回一次）
    ---
    tags:
      - API 令牌
    security:
      - cookieAuth: []
      - bearerAuth: []
    parameters:
      - in: body
        name: body
        schema:
          type: object
          properties:
            name:
              type: string
              maxLength: 64
            permissions:
              type: string
              enum: [read_only, read_write]
              default: read_write
    responses:
      201:
        description: 令牌创建成功
      400:
        description: 参数验证失败
    """
    user_id = get_current_user_id()
    try:
        data = create_token_schema.load(request.get_json(silent=True) or {})
    except Exception as e:
        return error(f"输入验证失败: {e}", 400)

    raw_token, token_obj = AuthService.create_api_token(
        user_id=user_id,
        name=data.get("name"),
        permissions=data.get("permissions", "read_write"),
    )
    return success({
        "token": raw_token,
        "id": token_obj.id,
        "name": token_obj.name,
        "permissions": token_obj.permissions,
    }, "令牌创建成功，请妥善保存原始 token", 201)


@tokens_ns.route("/<int:token_id>", methods=["DELETE"])
@auth_required
@limiter.limit("10 per minute")
def delete_token(token_id):
    """撤销 API 令牌
    ---
    tags:
      - API 令牌
    security:
      - cookieAuth: []
      - bearerAuth: []
    parameters:
      - in: path
        name: token_id
        type: integer
        required: true
    responses:
      200:
        description: 令牌已撤销
      404:
        description: 令牌不存在
    """
    user_id = get_current_user_id()
    token = ApiToken.query.filter_by(id=token_id, user_id=user_id).first()
    if not token:
        return error("令牌不存在", 404)
    db.session.delete(token)
    db.session.commit()
    return success(message="令牌已撤销")
