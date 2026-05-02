from flask import Blueprint, request

from app.services.automation_service import AutomationService
from app.utils.decorators import auth_required
from app.utils.response import error, success

automations_bp = Blueprint("automations", __name__)


@automations_bp.route("/automations", methods=["GET"])
@auth_required
def list_rules():
    from app.utils.decorators import get_current_user_id
    rules = AutomationService.list_rules(get_current_user_id())
    return success(data=rules)


@automations_bp.route("/automations", methods=["POST"])
@auth_required
def create_rule():
    from app.utils.decorators import get_current_user_id
    data = request.get_json()
    try:
        result = AutomationService.create_rule(get_current_user_id(), data)
        return success(data=result)
    except ValueError as e:
        return error(str(e), 400)


@automations_bp.route("/automations/<int:rule_id>", methods=["PUT"])
@auth_required
def update_rule(rule_id):
    from app.utils.decorators import get_current_user_id
    data = request.get_json()
    try:
        result = AutomationService.update_rule(get_current_user_id(), rule_id, data)
        return success(data=result)
    except ValueError as e:
        return error(str(e), 400)


@automations_bp.route("/automations/<int:rule_id>", methods=["DELETE"])
@auth_required
def delete_rule(rule_id):
    from app.utils.decorators import get_current_user_id
    try:
        AutomationService.delete_rule(get_current_user_id(), rule_id)
        return success(message="规则已删除")
    except ValueError as e:
        return error(str(e), 400)


@automations_bp.route("/automations/<int:rule_id>/toggle", methods=["POST"])
@auth_required
def toggle_rule(rule_id):
    from app.utils.decorators import get_current_user_id
    try:
        result = AutomationService.toggle_rule(get_current_user_id(), rule_id)
        return success(data=result)
    except ValueError as e:
        return error(str(e), 400)
