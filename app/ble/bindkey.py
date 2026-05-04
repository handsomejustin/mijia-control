import logging

import httpx

from app.ble.config import MIJIA_API_URL, MIJIA_TOKEN

logger = logging.getLogger(__name__)


def fetch_bindkey_from_api(did: str, api_url: str | None = None, token: str | None = None) -> str | None:
    api_url = api_url or MIJIA_API_URL
    token = token or MIJIA_TOKEN

    if not token:
        logger.error("未设置 MIJIA_TOKEN，无法获取 bindkey")
        return None

    try:
        resp = httpx.post(
            f"{api_url}/ble/devices/{did}/bindkey",
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            timeout=15,
        )
        data = resp.json()
        if data.get("success") and data.get("data", {}).get("bindkey"):
            return data["data"]["bindkey"]
        logger.warning("API 返回的 bindkey 为空: %s", data)
    except Exception as e:
        logger.warning("通过 API 获取 bindkey 失败: %s", e)
    return None
