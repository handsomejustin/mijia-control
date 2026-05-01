import os

import httpx
from mcp.server.fastmcp import FastMCP

mcp = FastMCP(
    "mijia-control",
    instructions="米家智能家居设备控制 MCP Server。用于控制灯光、空调、扫地机等米家智能设备。",
)

_BASE_URL = os.environ.get("MIJIA_API_URL", "http://127.0.0.1:5000/api")


def _get_token():
    return os.environ.get("MIJIA_TOKEN", "")


def _headers():
    return {"Authorization": f"Bearer {_get_token()}", "Content-Type": "application/json"}


async def _request(method: str, path: str, *, json_data: dict | None = None, params: dict | None = None):
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.request(method, f"{_BASE_URL}{path}", json=json_data, params=params, headers=_headers())
        return resp.json()


# ── 设备管理 ──


@mcp.tool()
async def list_devices(home_id: str | None = None, refresh: bool = False) -> dict:
    """列出所有米家智能设备。返回设备ID、名称、型号、在线状态等信息。

    Args:
        home_id: 按家庭ID过滤，不传则返回全部设备
        refresh: 是否强制刷新设备列表缓存
    """
    params = {}
    if home_id:
        params["home_id"] = home_id
    if refresh:
        params["refresh"] = "true"
    return await _request("GET", "/devices/", params=params)


@mcp.tool()
async def get_device(did: str) -> dict:
    """获取设备详情，包含设备规格、可用属性列表和动作列表。

    Args:
        did: 设备ID
    """
    return await _request("GET", f"/devices/{did}")


# ── 设备属性读写 ──


@mcp.tool()
async def get_property(did: str, prop_name: str) -> dict:
    """读取设备属性值，例如灯光亮度、空调温度、开关状态等。

    Args:
        did: 设备ID
        prop_name: 属性名称，如 power、brightness、temperature
    """
    return await _request("GET", f"/devices/{did}/props/{prop_name}")


@mcp.tool()
async def set_property(did: str, prop_name: str, value) -> dict:
    """设置设备属性值，用于控制设备。例如开灯、调亮度、设温度等。

    Args:
        did: 设备ID
        prop_name: 属性名称，如 power、brightness、temperature
        value: 属性值，类型取决于属性定义。常见值：power 为 "on"/"off"，brightness 为 0-100，temperature 为数字
    """
    return await _request("PUT", f"/devices/{did}/props/{prop_name}", json_data={"value": value})


# ── 设备动作 ──


@mcp.tool()
async def run_action(did: str, action_name: str, value: dict | None = None) -> dict:
    """执行设备动作，例如扫地机开始清扫、播放音乐等。

    Args:
        did: 设备ID
        action_name: 动作名称，如 start-sweep、stop-sweeping
        value: 动作参数，可选
    """
    body = {"value": value} if value is not None else {}
    return await _request("POST", f"/devices/{did}/actions/{action_name}", json_data=body)


# ── 场景管理 ──


@mcp.tool()
async def list_scenes(home_id: str | None = None, refresh: bool = False) -> dict:
    """列出所有米家场景。

    Args:
        home_id: 按家庭ID过滤
        refresh: 是否强制刷新缓存
    """
    params = {}
    if home_id:
        params["home_id"] = home_id
    if refresh:
        params["refresh"] = "true"
    return await _request("GET", "/scenes/", params=params)


@mcp.tool()
async def run_scene(scene_id: str) -> dict:
    """执行一个米家场景，触发该场景中预设的所有设备操作。

    Args:
        scene_id: 场景ID
    """
    return await _request("POST", f"/scenes/{scene_id}/run")


# ── 家庭管理 ──


@mcp.tool()
async def list_homes(refresh: bool = False) -> dict:
    """列出所有家庭及其设备概览。

    Args:
        refresh: 是否强制刷新缓存
    """
    params = {}
    if refresh:
        params["refresh"] = "true"
    return await _request("GET", "/homes/", params=params)


@mcp.tool()
async def get_home(home_id: str) -> dict:
    """获取家庭详情，包含该家庭下的所有设备列表。

    Args:
        home_id: 家庭ID
    """
    return await _request("GET", f"/homes/{home_id}")
