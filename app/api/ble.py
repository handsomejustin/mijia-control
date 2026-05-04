from flask import Blueprint, request

from app.services.ble_service import BLEService
from app.utils.decorators import auth_required, get_current_user_id
from app.utils.response import error, success

ble_bp = Blueprint("ble", __name__)


@ble_bp.route("/ble/devices", methods=["GET"])
@auth_required
def list_ble_devices():
    user_id = get_current_user_id()
    devices = BLEService.list_devices(user_id)
    return success(data=devices)


@ble_bp.route("/ble/devices", methods=["POST"])
@auth_required
def register_ble_device():
    user_id = get_current_user_id()
    data = request.get_json()
    did = data.get("did")
    mac = data.get("mac_address")
    bindkey = data.get("bindkey")

    if not did or not mac:
        return error("缺少必要字段: did, mac_address", 400)

    try:
        result = BLEService.register_device(user_id, did, mac, bindkey)
        return success(data=result, status_code=201)
    except ValueError as e:
        return error(str(e), 400)


@ble_bp.route("/ble/devices/<path:did>", methods=["GET"])
@auth_required
def get_ble_device(did):
    user_id = get_current_user_id()
    try:
        result = BLEService.get_device(user_id, did)
        return success(data=result)
    except ValueError as e:
        return error(str(e), 404)


@ble_bp.route("/ble/devices/<path:did>", methods=["DELETE"])
@auth_required
def delete_ble_device(did):
    user_id = get_current_user_id()
    try:
        BLEService.delete_device(user_id, did)
        return success(message="BLE 设备已删除")
    except ValueError as e:
        return error(str(e), 404)


@ble_bp.route("/ble/devices/<path:did>/readings", methods=["POST"])
@auth_required
def ingest_ble_reading(did):
    data = request.get_json()
    values = data.get("values")

    if not values:
        return error("缺少必要字段: values", 400)

    try:
        result = BLEService.ingest_reading(did, values)
        return success(data=result)
    except ValueError as e:
        return error(str(e), 400)


@ble_bp.route("/ble/devices/<path:did>/readings", methods=["GET"])
@auth_required
def get_ble_readings(did):
    hours = request.args.get("hours", 24, type=int)
    limit = request.args.get("limit", 200, type=int)

    try:
        readings = BLEService.get_readings(did, hours=hours, limit=limit)
        return success(data=readings)
    except ValueError as e:
        return error(str(e), 404)


@ble_bp.route("/ble/devices/<path:did>/bindkey", methods=["POST"])
@auth_required
def refresh_bindkey(did):
    user_id = get_current_user_id()
    data = request.get_json() or {}
    bindkey = data.get("bindkey")

    try:
        result = BLEService.refresh_bindkey(user_id, did, bindkey)
        return success(data=result)
    except ValueError as e:
        return error(str(e), 404)


@ble_bp.route("/ble/devices/_all_enabled", methods=["GET"])
@auth_required
def get_all_enabled():
    devices = BLEService.get_all_enabled_devices()
    return success(data=devices)
