from flask import Blueprint, request

from app.extensions import limiter
from app.services.home_service import HomeService
from app.utils.decorators import auth_required, get_current_user_id
from app.utils.response import error, success

homes_ns = Blueprint("homes", __name__, url_prefix="/homes")


@homes_ns.route("/", methods=["GET"])
@auth_required
@limiter.limit("60 per minute")
def list_homes():
    """获取家庭列表
    ---
    tags:
      - 家庭
    security:
      - cookieAuth: []
      - bearerAuth: []
    parameters:
      - in: query
        name: refresh
        type: boolean
        default: false
    responses:
      200:
        description: 家庭列表
    """
    refresh = request.args.get("refresh", "false").lower() == "true"
    try:
        homes = HomeService.list_homes(get_current_user_id(), refresh=refresh)
        return success(homes)
    except Exception as e:
        return error(str(e), 500)


@homes_ns.route("/<home_id>", methods=["GET"])
@auth_required
@limiter.limit("60 per minute")
def get_home(home_id):
    """获取家庭详情
    ---
    tags:
      - 家庭
    security:
      - cookieAuth: []
      - bearerAuth: []
    parameters:
      - in: path
        name: home_id
        type: string
        required: true
    responses:
      200:
        description: 家庭详情
      404:
        description: 家庭未找到
    """
    try:
        home = HomeService.get_home(get_current_user_id(), home_id)
        return success(home)
    except ValueError as e:
        return error(str(e), 404)
    except Exception as e:
        return error(str(e), 500)
