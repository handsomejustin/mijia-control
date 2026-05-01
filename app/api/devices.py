import re

from flask import Blueprint, request
from mijiaAPI import DeviceGetError, DeviceSetError, DeviceActionError

from app.extensions import limiter
from app.schemas.device import SetPropertySchema, RunActionSchema
from app.services.device_service import DeviceService
from app.utils.decorators import auth_required, get_current_user_id
from app.utils.response import error, success

# 米家 API 错误码 → HTTP 状态码映射
_MIJIA_ERROR_STATUS = {
    -704010000: 403,   # 未授权（设备可能被删除）
    -704030013: 403,   # Property不可读
    -704030023: 403,   # Property不可写
    -704030033: 403,   # Property不可订阅
    -704042011: 503,   # 设备离线
    -704042001: 404,   # Device不存在
    -704090001: 404,   # Device不存在
    -704040003: 404,   # Property不存在
    -704040005: 404,   # Action不存在
    -704040002: 404,   # Service不存在
    -704014006: 404,   # 没找到设备描述
    -704053036: 504,   # 设备操作超时
    -704083036: 504,   # 设备操作超时
    -704220043: 400,   # Property值错误
    -704220025: 400,   # Action参数个数不匹配
    -704220035: 400,   # Action参数错误
    -704053100: 409,   # 设备在当前状态下无法执行此操作
    -704040999: 501,   # 功能未上线
}


def _mijia_error_response(exc):
    """将米家 API 异常映射为合适的 HTTP 响应"""
    match = re.search(r"code:\s*(-?\d+)", str(exc))
    code = int(match.group(1)) if match else None
    status = _MIJIA_ERROR_STATUS.get(code, 500) if code is not None else 500
    return error(str(exc), status)

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


@devices_ns.route("/<did>/stream-info", methods=["GET"])
@auth_required
@limiter.limit("30 per minute")
def get_stream_info(did):
    """获取摄像头流信息（IP、Token）
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
        description: 摄像头设备 ID
    responses:
      200:
        description: 流信息
      404:
        description: 设备未找到
    """
    try:
        result = DeviceService.get_stream_info(get_current_user_id(), did)
        return success(result)
    except ValueError as e:
        return error(str(e), 404)
    except Exception as e:
        return error(str(e), 500)


@devices_ns.route("/go2rtc-config", methods=["GET"])
@auth_required
@limiter.limit("30 per minute")
def get_go2rtc_config():
    """获取用户摄像头的 go2rtc 配置
    ---
    tags:
      - 设备
    security:
      - cookieAuth: []
      - bearerAuth: []
    responses:
      200:
        description: go2rtc YAML 配置
    """
    try:
        result = DeviceService.go2rtc_config(get_current_user_id())
        return success(result)
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
    except DeviceGetError as e:
        return _mijia_error_response(e)
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
    except DeviceSetError as e:
        return _mijia_error_response(e)
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
    except DeviceActionError as e:
        return _mijia_error_response(e)
    except Exception as e:
        return error(str(e), 500)


@devices_ns.route("/<did>/rated_power", methods=["PUT"])
@auth_required
@limiter.limit("30 per minute")
def set_rated_power(did):
    """设置设备额定功率(W)，用于估算能耗
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
      - in: body
        name: body
        required: true
        schema:
          type: object
          required: [rated_power]
          properties:
            rated_power:
              type: number
              description: 额定功率(W)，传 null 清除
    responses:
      200:
        description: 设置成功
      404:
        description: 设备未找到
    """
    data = request.get_json(silent=True) or {}
    rated_power = data.get("rated_power")
    if rated_power is not None:
        try:
            rated_power = float(rated_power)
            if rated_power <= 0:
                return error("rated_power 必须大于 0", 400)
        except (TypeError, ValueError):
            return error("rated_power 必须为数字", 400)
    try:
        result = DeviceService.update_rated_power(get_current_user_id(), did, rated_power)
        return success(result)
    except ValueError as e:
        return error(str(e), 404)
    except Exception as e:
        return error(str(e), 500)
