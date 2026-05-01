from flask import Blueprint, request

from app.extensions import limiter
from app.services.scene_service import SceneService
from app.utils.decorators import auth_required, get_current_user_id
from app.utils.response import error, success

scenes_ns = Blueprint("scenes", __name__, url_prefix="/scenes")


@scenes_ns.route("/", methods=["GET"])
@auth_required
@limiter.limit("60 per minute")
def list_scenes():
    """获取场景列表
    ---
    tags:
      - 场景
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
    responses:
      200:
        description: 场景列表
    """
    home_id = request.args.get("home_id")
    refresh = request.args.get("refresh", "false").lower() == "true"
    try:
        scenes = SceneService.list_scenes(get_current_user_id(), home_id=home_id, refresh=refresh)
        return success(scenes)
    except Exception as e:
        return error(str(e), 500)


@scenes_ns.route("/<scene_id>/run", methods=["POST"])
@auth_required
@limiter.limit("30 per minute")
def run_scene(scene_id):
    """执行场景
    ---
    tags:
      - 场景
    security:
      - cookieAuth: []
      - bearerAuth: []
    parameters:
      - in: path
        name: scene_id
        type: string
        required: true
    responses:
      200:
        description: 执行成功
    """
    try:
        result = SceneService.run_scene(get_current_user_id(), scene_id)
        return success(result)
    except Exception as e:
        return error(str(e), 500)
