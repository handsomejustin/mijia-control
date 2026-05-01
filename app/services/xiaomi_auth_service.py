import json
import logging
import threading
import uuid
from datetime import datetime, timedelta, timezone

from mijiaAPI import mijiaAPI

from app.extensions import db
from app.models.xiaomi_auth import XiaomiAuth
from app.utils.mijia_pool import api_pool

logger = logging.getLogger(__name__)

_poll_store: dict[str, dict] = {}


def _create_bare_api() -> mijiaAPI:
    """创建一个无 auth_data 的 mijiaAPI 实例，用于发起 QR 登录。"""
    import locale

    api = mijiaAPI.__new__(mijiaAPI)
    api.auth_data = {}
    api.auth_data_path = None
    api._available_cache = None
    api._available_cache_time = 0
    api.locale = locale.getlocale()[0] if locale.getlocale()[0] else "zh_CN"
    if "_" not in api.locale:
        api.locale = "zh_CN"
    api.api_base_url = "https://api.mijia.tech/app"
    api.login_url = "https://account.xiaomi.com/longPolling/loginUrl"
    api.service_login_url = (
        f"https://account.xiaomi.com/pass/serviceLogin?_json=true&sid=mijia&_locale={api.locale}"
    )
    # QR 登录流程中 _get_location 只有在 code==0 时才用到 session，
    # 新用户 auth_data 为空，code 不会为 0，所以不需要 _init_session
    api.session = None
    return api


class XiaomiAuthService:
    @staticmethod
    def get_status(user_id: int) -> dict:
        auth = XiaomiAuth.query.filter_by(user_id=user_id).first()
        if not auth:
            return {"linked": False}
        return {
            "linked": True,
            "is_valid": auth.is_valid,
            "xiaomi_user_id": auth.xiaomi_user_id,
            "last_refreshed": auth.last_refreshed.isoformat() if auth.last_refreshed else None,
            "expires_at": auth.expires_at.isoformat() if auth.expires_at else None,
        }

    @staticmethod
    def init_qr_login(user_id: int) -> dict:
        api = _create_bare_api()

        location_data = api._get_location()
        if location_data.get("code", -1) == 0:
            return {"status": "already_valid"}

        from urllib import parse
        import time
        import requests

        location_data.update({
            "theme": "",
            "bizDeviceType": "",
            "_hasLogo": "false",
            "_qrsize": "240",
            "_dc": str(int(time.time() * 1000)),
        })

        url = api.login_url + "?" + parse.urlencode(location_data)
        headers = {
            "User-Agent": api.user_agent,
            "Accept-Encoding": "gzip",
            "Content-Type": "application/x-www-form-urlencoded",
            "Connection": "keep-alive",
        }
        login_ret = requests.get(url, headers=headers)
        login_data = api._handle_ret(login_ret)

        poll_id = str(uuid.uuid4())
        _poll_store[poll_id] = {
            "status": "pending",
            "lp_url": login_data["lp"],
            "qr_url": login_data["qr"],
            "login_url": login_data["loginUrl"],
            "headers": headers,
            "user_id": user_id,
            "result": None,
        }

        # 获取当前 app 实例，传给后台线程
        from flask import current_app
        app = current_app._get_current_object()

        thread = threading.Thread(target=_poll_xiaomi_qr, args=(poll_id, app), daemon=True)
        thread.start()

        import qrcode
        from io import BytesIO
        import base64

        qr = qrcode.QRCode(border=1, box_size=10)
        qr.add_data(login_data["loginUrl"])
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        buf = BytesIO()
        img.save(buf, format="PNG")
        qr_base64 = base64.b64encode(buf.getvalue()).decode()

        return {
            "poll_id": poll_id,
            "qr_url": login_data["qr"],
            "qr_image": f"data:image/png;base64,{qr_base64}",
            "ws_room": f"qr_{poll_id}",
        }

    @staticmethod
    def poll_qr_status(poll_id: str, user_id: int = None) -> dict:
        entry = _poll_store.get(poll_id)
        if not entry:
            return {"status": "not_found"}
        if user_id is not None and entry.get("user_id") != user_id:
            return {"status": "not_found"}
        result = {"status": entry["status"]}
        if entry.get("result"):
            result["detail"] = entry["result"]
        return result

    @staticmethod
    def unlink(user_id: int) -> bool:
        auth = XiaomiAuth.query.filter_by(user_id=user_id).first()
        if auth:
            db.session.delete(auth)
            db.session.commit()
            api_pool.invalidate(user_id)
        return True


def _poll_xiaomi_qr(poll_id: str, app):
    """在后台线程中轮询小米 QR 扫码结果。需要 app 实例来创建上下文。"""
    import requests

    entry = _poll_store.get(poll_id)
    if not entry:
        return

    session = requests.Session()
    try:
        lp_ret = session.get(entry["lp_url"], headers=entry["headers"], timeout=120)

        api_temp = _create_bare_api()
        lp_data = api_temp._handle_ret(lp_ret)

        auth_keys = ["psecurity", "nonce", "ssecurity", "passToken", "userId", "cUserId"]
        auth_data = {}
        for key in auth_keys:
            auth_data[key] = lp_data[key]

        callback_url = lp_data["location"]
        session.get(callback_url, headers=entry["headers"])
        cookies = session.cookies.get_dict()
        auth_data.update(cookies)
        auth_data.update({
            "expireTime": int((datetime.now(timezone.utc) + timedelta(days=30)).timestamp() * 1000),
        })

        user_id = entry["user_id"]

        # 在 Flask 应用上下文中操作数据库
        with app.app_context():
            existing = XiaomiAuth.query.filter_by(user_id=user_id).first()
            if existing:
                existing.auth_data = auth_data
                existing.is_valid = True
                existing.xiaomi_user_id = auth_data.get("userId")
                existing.expires_at = datetime.now(timezone.utc) + timedelta(days=30)
                existing.mark_refreshed()
            else:
                xiaomi_auth = XiaomiAuth(
                    user_id=user_id,
                    auth_data=auth_data,
                    xiaomi_user_id=auth_data.get("userId"),
                    expires_at=datetime.now(timezone.utc) + timedelta(days=30),
                )
                xiaomi_auth.mark_refreshed()
                db.session.add(xiaomi_auth)

            db.session.commit()
            api_pool.create_from_auth_data(user_id, auth_data)

        entry["status"] = "success"
        _emit_qr_status(poll_id, "success")

    except requests.exceptions.Timeout:
        entry["status"] = "timeout"
        _emit_qr_status(poll_id, "timeout")
    except Exception as e:
        logger.exception(f"QR login poll failed for poll_id={poll_id}")
        entry["status"] = "error"
        entry["result"] = str(e)
        _emit_qr_status(poll_id, "error", detail=str(e))


def _emit_qr_status(poll_id, status, detail=None):
    try:
        from app.web.socketio import emit_qr_status
        emit_qr_status(poll_id, status, detail)
    except Exception:
        pass
