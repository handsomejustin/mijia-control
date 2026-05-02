from flask import Blueprint, request

from app.services.energy_service import EnergyService
from app.utils.decorators import auth_required
from app.utils.response import error, success

energy_bp = Blueprint("energy", __name__)


@energy_bp.route("/energy/<did>/log", methods=["POST"])
@auth_required
def log_energy(did):
    from app.utils.decorators import get_current_user_id
    data = request.get_json()
    prop_name = data.get("prop_name")
    value = data.get("value")
    if prop_name is None or value is None:
        return error("缺少 prop_name 或 value", 400)
    try:
        result = EnergyService.log_energy(get_current_user_id(), did, prop_name, float(value), unit=data.get("unit"))
        return success(data=result)
    except (ValueError, TypeError) as e:
        return error(str(e), 400)


@energy_bp.route("/energy/<did>/daily", methods=["GET"])
@auth_required
def daily_stats(did):
    from app.utils.decorators import get_current_user_id
    days = request.args.get("days", 7, type=int)
    stats = EnergyService.get_daily_stats(get_current_user_id(), did, days=min(days, 90))
    return success(data=stats)


@energy_bp.route("/energy/<did>/hourly", methods=["GET"])
@auth_required
def hourly_stats(did):
    from app.utils.decorators import get_current_user_id
    hours = request.args.get("hours", 24, type=int)
    stats = EnergyService.get_hourly_stats(get_current_user_id(), did, hours=min(hours, 168))
    return success(data=stats)


@energy_bp.route("/energy/<did>/latest", methods=["GET"])
@auth_required
def latest_logs(did):
    from app.utils.decorators import get_current_user_id
    prop_name = request.args.get("prop_name")
    limit = request.args.get("limit", 100, type=int)
    logs = EnergyService.get_latest(get_current_user_id(), did, prop_name=prop_name, limit=min(limit, 1000))
    return success(data=logs)


@energy_bp.route("/energy/<did>/props", methods=["GET"])
@auth_required
def energy_props(did):
    from app.utils.decorators import get_current_user_id
    props = EnergyService.get_device_energy_props(get_current_user_id(), did)
    return success(data=props)
