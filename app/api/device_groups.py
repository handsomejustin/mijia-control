from flask import Blueprint, request

from app.services.device_group_service import DeviceGroupService
from app.utils.decorators import auth_required
from app.utils.response import error, success

device_groups_bp = Blueprint("device_groups", __name__)


@device_groups_bp.route("/groups", methods=["GET"])
@auth_required
def list_groups():
    from app.utils.decorators import get_current_user_id
    groups = DeviceGroupService.list_groups(get_current_user_id())
    return success(data=groups)


@device_groups_bp.route("/groups", methods=["POST"])
@auth_required
def create_group():
    from app.utils.decorators import get_current_user_id
    data = request.get_json()
    name = data.get("name")
    if not name:
        return error("分组名称不能为空", 400)
    try:
        result = DeviceGroupService.create_group(get_current_user_id(), name, icon=data.get("icon"))
        return success(data=result)
    except ValueError as e:
        return error(str(e), 400)


@device_groups_bp.route("/groups/<int:group_id>", methods=["DELETE"])
@auth_required
def delete_group(group_id):
    from app.utils.decorators import get_current_user_id
    try:
        DeviceGroupService.delete_group(get_current_user_id(), group_id)
        return success(message="分组已删除")
    except ValueError as e:
        return error(str(e), 400)


@device_groups_bp.route("/groups/<int:group_id>/devices/<did>", methods=["POST"])
@auth_required
def add_device_to_group(group_id, did):
    from app.utils.decorators import get_current_user_id
    try:
        DeviceGroupService.add_device(get_current_user_id(), group_id, did)
        return success(message="设备已添加到分组")
    except ValueError as e:
        return error(str(e), 400)


@device_groups_bp.route("/groups/<int:group_id>/devices/<did>", methods=["DELETE"])
@auth_required
def remove_device_from_group(group_id, did):
    from app.utils.decorators import get_current_user_id
    try:
        DeviceGroupService.remove_device(get_current_user_id(), group_id, did)
        return success(message="设备已从分组移除")
    except ValueError as e:
        return error(str(e), 400)


@device_groups_bp.route("/devices/<did>/favorite", methods=["POST"])
@auth_required
def toggle_favorite(did):
    from app.utils.decorators import get_current_user_id
    try:
        result = DeviceGroupService.toggle_favorite(get_current_user_id(), did)
        return success(data=result)
    except ValueError as e:
        return error(str(e), 400)


@device_groups_bp.route("/devices/<did>/favorite", methods=["GET"])
@auth_required
def check_favorite(did):
    from app.utils.decorators import get_current_user_id
    is_fav = DeviceGroupService.is_favorite(get_current_user_id(), did)
    return success(data={"did": did, "is_favorite": is_fav})
