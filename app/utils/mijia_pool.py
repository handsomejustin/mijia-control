import json
import tempfile
import threading
from pathlib import Path

from mijiaAPI import mijiaAPI

from app.extensions import db
from app.models.xiaomi_auth import XiaomiAuth


class MijiaAPIAdapter:
    """包装 mijiaAPI，支持从 auth_data dict 直接初始化，无需文件 I/O。"""

    def __init__(self, auth_data: dict):
        self._api = mijiaAPI.__new__(mijiaAPI)
        self._api.auth_data = auth_data
        self._api.auth_data_path = Path(tempfile.mkdtemp()) / "auth.json"
        self._api._available_cache = None
        self._api._available_cache_time = 0
        import locale

        self._api.locale = locale.getlocale()[0] if locale.getlocale()[0] else "zh_CN"
        if "_" not in self._api.locale:
            self._api.locale = "zh_CN"
        self._api.api_base_url = "https://api.mijia.tech/app"
        self._api.login_url = "https://account.xiaomi.com/longPolling/loginUrl"
        self._api.service_login_url = (
            f"https://account.xiaomi.com/pass/serviceLogin?_json=true&sid=mijia&_locale={self._api.locale}"
        )
        self._api._init_session()

    @property
    def api(self) -> mijiaAPI:
        return self._api

    @property
    def available(self) -> bool:
        return self._api.available

    @property
    def auth_data(self) -> dict:
        return self._api.auth_data

    def refresh_token(self) -> dict:
        result = self._api._refresh_token()
        return result


class MijiaAPIPool:
    """管理每用户的 mijiaAPI 实例，支持自动刷新和持久化。"""

    def __init__(self):
        self._pool: dict[int, MijiaAPIAdapter] = {}
        self._lock = threading.Lock()

    def get_api(self, user_id: int) -> mijiaAPI:
        with self._lock:
            adapter = self._pool.get(user_id)
            if adapter and adapter.available:
                return adapter.api

            xiaomi_auth = db.session.query(XiaomiAuth).filter_by(user_id=user_id).first()
            if not xiaomi_auth or not xiaomi_auth.auth_data:
                raise ValueError(f"用户 {user_id} 未绑定小米账号")

            auth_data = xiaomi_auth.auth_data
            if isinstance(auth_data, str):
                auth_data = json.loads(auth_data)

            adapter = MijiaAPIAdapter(auth_data)
            self._pool[user_id] = adapter

            if not adapter.available:
                try:
                    adapter.refresh_token()
                    self._persist_auth_data(user_id, adapter.auth_data)
                    xiaomi_auth.mark_refreshed()
                    db.session.commit()
                except Exception:
                    xiaomi_auth.mark_invalid()
                    db.session.commit()
                    self._pool.pop(user_id, None)
                    raise

            return adapter.api

    def invalidate(self, user_id: int):
        with self._lock:
            self._pool.pop(user_id, None)

    def refresh_if_needed(self, user_id: int) -> mijiaAPI:
        with self._lock:
            adapter = self._pool.get(user_id)
            if adapter and adapter.available:
                return adapter.api

            del self._pool[user_id]
        return self.get_api(user_id)

    def _persist_auth_data(self, user_id: int, auth_data: dict):
        xiaomi_auth = db.session.query(XiaomiAuth).filter_by(user_id=user_id).first()
        if xiaomi_auth:
            xiaomi_auth.auth_data = auth_data
            xiaomi_auth.mark_refreshed()

    def create_from_auth_data(self, user_id: int, auth_data: dict) -> mijiaAPI:
        with self._lock:
            self._pool.pop(user_id, None)
            adapter = MijiaAPIAdapter(auth_data)
            self._pool[user_id] = adapter
            return adapter.api


api_pool = MijiaAPIPool()
