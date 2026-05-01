import logging

from flask_login import current_user
from flask_socketio import emit, join_room, leave_room

from app.extensions import socketio

logger = logging.getLogger(__name__)


@socketio.on("connect")
def handle_connect():
    if current_user.is_authenticated:
        join_room(f"user_{current_user.id}")
        emit("connected", {"status": "ok"})
        logger.debug(f"SocketIO: user_{current_user.id} connected")
    else:
        return False


@socketio.on("disconnect")
def handle_disconnect():
    if current_user.is_authenticated:
        leave_room(f"user_{current_user.id}")
        logger.debug(f"SocketIO: user_{current_user.id} disconnected")


@socketio.on("subscribe_device")
def handle_subscribe_device(data):
    if current_user.is_authenticated:
        did = data.get("did")
        if did:
            from app.models.device_cache import DeviceCache
            device = DeviceCache.query.filter_by(user_id=current_user.id, did=did).first()
            if device:
                join_room(f"device_{did}")


@socketio.on("unsubscribe_device")
def handle_unsubscribe_device(data):
    if current_user.is_authenticated:
        did = data.get("did")
        if did:
            from app.models.device_cache import DeviceCache
            device = DeviceCache.query.filter_by(user_id=current_user.id, did=did).first()
            if device:
                leave_room(f"device_{did}")


def emit_device_update(user_id, did, update_type, data):
    """向用户房间推送设备更新事件"""
    socketio.emit(
        "device_update",
        {"did": did, "type": update_type, "data": data},
        room=f"user_{user_id}",
    )


def emit_qr_status(poll_id, status, detail=None):
    """向 QR 轮询房间推送扫码状态"""
    payload = {"status": status}
    if detail:
        payload["detail"] = detail
    socketio.emit("qr_status", payload, room=f"qr_{poll_id}")


def register_socketio(app):
    """在应用上下文中注册 SocketIO 事件处理（确保 login_manager 已初始化）"""
    pass
