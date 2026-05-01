from flask import Blueprint

from app.extensions import limiter
from app.services.xiaomi_auth_service import XiaomiAuthService
from app.utils.decorators import auth_required, get_current_user_id
from app.utils.response import error, success

xiaomi_ns = Blueprint("xiaomi", __name__, url_prefix="/xiaomi")


@xiaomi_ns.route("/qr-init", methods=["POST"])
@auth_required
@limiter.limit("5 per minute")
def qr_init():
    """生成小米账号绑定二维码
    ---
    tags:
      - 小米账号
    security:
      - cookieAuth: []
      - bearerAuth: []
    responses:
      200:
        description: 返回二维码图片和轮询 ID
    """
    try:
        result = XiaomiAuthService.init_qr_login(get_current_user_id())
        if result.get("status") == "already_valid":
            return success(message="小米账号已绑定且有效")
        return success(result)
    except Exception as e:
        return error(f"QR 码生成失败: {e}", 500)


@xiaomi_ns.route("/qr-poll/<poll_id>", methods=["GET"])
@auth_required
@limiter.limit("60 per minute")
def qr_poll(poll_id):
    """轮询扫码状态
    ---
    tags:
      - 小米账号
    security:
      - cookieAuth: []
      - bearerAuth: []
    parameters:
      - in: path
        name: poll_id
        type: string
        required: true
    responses:
      200:
        description: 扫码状态 (pending/success/timeout/error)
    """
    result = XiaomiAuthService.poll_qr_status(poll_id, get_current_user_id())
    return success(result)


@xiaomi_ns.route("/status", methods=["GET"])
@auth_required
@limiter.limit("60 per minute")
def status():
    """获取小米账号绑定状态
    ---
    tags:
      - 小米账号
    security:
      - cookieAuth: []
      - bearerAuth: []
    responses:
      200:
        description: 绑定状态
    """
    result = XiaomiAuthService.get_status(get_current_user_id())
    return success(result)


@xiaomi_ns.route("/unlink", methods=["DELETE"])
@auth_required
@limiter.limit("5 per minute")
def unlink():
    """解绑小米账号
    ---
    tags:
      - 小米账号
    security:
      - cookieAuth: []
      - bearerAuth: []
    responses:
      200:
        description: 已解绑
    """
    XiaomiAuthService.unlink(get_current_user_id())
    return success(message="已解绑小米账号")
