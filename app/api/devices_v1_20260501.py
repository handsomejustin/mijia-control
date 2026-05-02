from flask import Blueprint, request

from app.extensions import limiter
from app.schemas.device import RunActionSchema, SetPropertySchema
from app.services.device_service import DeviceService
from app.utils.decorators import auth_required, get_current_user_id
from app.utils.response import error, success

devices_ns = Blueprint("devices", __name__, url_prefix="/devices")

set_prop_schema = SetPropertySchema()
run_action_schema = RunActionSchema()


@devices_ns.route("/", methods=["GET"])
@auth_required
@limiter.limit("60 per minute")
def list_devices():
    """获取设备列表
    ---
    tags:
      - 设备
    security:
      - cookieAuth: []
      - bearerAuth: []
    parameters:
      - in: query
        name: home_id
        type: string
        description: 按家庭 ID 过滤
      - in: query
        name: refresh
        type: boolean
        default: false
        description: 是否强制刷新缓存
    responses:
      200:
        description: 设备列表
    """
    home_id = request.args.get("home_id")
    refresh = request.args.get("refresh", "false").lower() == "true"
    try:
        devices = DeviceService.list_devices(get_current_user_id(), home_id=home_id, refresh=refresh)
        return success(devices)
    except Exception as e:
        return error(str(e), 500)


@devices_ns.route("/<did>", methods=["GET"])
@auth_required
@limiter.limit("60 per minute")
def get_device(did):
    """获取设备详情及规格
    ---
    tags:
      - 设备
    security:
      - cookieAuth: []
      - bearerAuth: []
    parameters:
      - in: path
        name: did
        type: string
        required: true
        description: 设备 ID
    responses:
      200:
        description: 设备详情
      404:
        description: 设备未找到
    """
    try:
        device = DeviceService.get_device(get_current_user_id(), did)
        return success(device)
    except ValueError as e:
        return error(str(e), 404)
    except Exception as e:
        return error(str(e), 500)


@devices_ns.route("/<did>/props/<prop_name>", methods=["GET"])
@auth_required
@limiter.limit("60 per minute")
def get_property(did, prop_name):
    """读取设备属性值
    ---
    tags:
      - 设备
    security:
      - cookieAuth: []
      - bearerAuth: []
    parameters:
      - in: path
        name: did
        type: string
        required: true
      - in: path
        name: prop_name
        type: string
        required: true
        description: 属性名称
    responses:
      200:
        description: 属性值
    """
    try:
        result = DeviceService.get_property(get_current_user_id(), did, prop_name)
        return success(result)
    except Exception as e:
        return error(str(e), 500)


@devices_ns.route("/<did>/props/<prop_name>", methods=["PUT"])
@auth_required
@limiter.limit("30 per minute")
def set_property(did, prop_name):
    """设置设备属性值
    ---
    tags:
      - 设备
    security:
      - cookieAuth: []
      - bearerAuth: []
    parameters:
      - in: path
        name: did
        type: string
        required: true
      - in: path
        name: prop_name
        type: string
        required: true
      - in: body
        name: body
        required: true
        schema:
          type: object
          required: [value]
          properties:
            value:
              description: 属性值（类型取决于属性定义）
    responses:
      200:
        description: 设置成功
      400:
        description: 参数验证失败
    """
    try:
        data = set_prop_schema.load(request.get_json(silent=True) or {})
    except Exception as e:
        return error(f"输入验证失败: {e}", 400)
    try:
        result = DeviceService.set_property(get_current_user_id(), did, prop_name, data["value"])
        return success(result)
    except Exception as e:
        return error(str(e), 500)


@devices_ns.route("/<did>/actions/<action_name>", methods=["POST"])
@auth_required
@limiter.limit("30 per minute")
def run_action(did, action_name):
    """执行设备动作
    ---
    tags:
      - 设备
    security:
      - cookieAuth: []
      - bearerAuth: []
    parameters:
      - in: path
        name: did
        type: string
        required: true
      - in: path
        name: action_name
        type: string
        required: true
      - in: body
        name: body
        schema:
          type: object
          properties:
            value:
              description: 动作参数（可选）
    responses:
      200:
        description: 执行成功
      400:
        description: 参数验证失败
    """
    try:
        data = run_action_schema.load(request.get_json(silent=True) or {})
    except Exception as e:
        return error(f"输入验证失败: {e}", 400)
    try:
        result = DeviceService.run_action(get_current_user_id(), did, action_name, data.get("value"))
        return success(result)
    except Exception as e:
        return error(str(e), 500)
