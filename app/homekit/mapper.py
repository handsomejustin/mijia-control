import logging
import os
from enum import StrEnum

import yaml

logger = logging.getLogger(__name__)

_YAML_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "homekit_mapping.yaml")


class DeviceCategory(StrEnum):
    LIGHT = "light"
    OUTLET = "outlet"
    TEMPERATURE_SENSOR = "temperature_sensor"
    HUMIDITY_SENSOR = "humidity_sensor"
    THERMOSTAT = "thermostat"
    SWITCH = "switch"
    CAMERA = "camera"
    HEATER = "heater"
    IGNORED = "ignored"


# model 关键词 → 设备类别映射（按优先级排序，匹配即停）
_MODEL_RULES: list[tuple[str, DeviceCategory]] = [
    # 摄像头
    ("chuangmi.camera", DeviceCategory.CAMERA),
    ("mijia.camera", DeviceCategory.CAMERA),
    ("isa.camera", DeviceCategory.CAMERA),
    # 灯光
    ("yeelink.light", DeviceCategory.LIGHT),
    ("philips.light", DeviceCategory.LIGHT),
    ("mijia.light", DeviceCategory.LIGHT),
    ("lumi.light", DeviceCategory.LIGHT),
    # 空调伴侣
    ("acpartner", DeviceCategory.THERMOSTAT),
    ("aircondition", DeviceCategory.THERMOSTAT),
    # 温湿度传感器
    ("ht.sen", DeviceCategory.TEMPERATURE_SENSOR),
    ("weather.v1", DeviceCategory.TEMPERATURE_SENSOR),
    ("sensor_ht", DeviceCategory.TEMPERATURE_SENSOR),
    # 取暖器
    ("heater", DeviceCategory.HEATER),
    # 除湿机
    ("derh", DeviceCategory.THERMOSTAT),
    # 插座/开关
    ("chuangmi.plug", DeviceCategory.OUTLET),
    ("zimi.plug", DeviceCategory.OUTLET),
    ("qmi.powerstrip", DeviceCategory.OUTLET),
    ("lumi.switch", DeviceCategory.OUTLET),
    ("lumi.ctrl_neutral", DeviceCategory.OUTLET),
    # 空气净化器
    ("zhimi.airpurifier", DeviceCategory.SWITCH),
    ("roidmi.airpurifier", DeviceCategory.SWITCH),
    # 扫地机
    ("roborock.vacuum", DeviceCategory.SWITCH),
    ("mijia.vacuum", DeviceCategory.SWITCH),
    # 不适合桥接到 HomeKit 的设备
    ("router", DeviceCategory.IGNORED),
    ("cardvr", DeviceCategory.IGNORED),
    ("kettle", DeviceCategory.IGNORED),
]


def _extract_prop_names(spec_data: dict | None) -> set[str]:
    if not spec_data:
        return set()
    names = set()
    for prop in spec_data.get("properties", []):
        name = prop.get("name")
        if name:
            names.add(name)
    return names


def _infer_from_spec(spec_data: dict | None) -> DeviceCategory | None:
    """从 spec_data 属性推断设备类别（model 未匹配时的智能回退）。"""
    props = _extract_prop_names(spec_data)
    has_power = bool(props & {"on", "power", "switch"})
    has_brightness = bool(props & {"brightness"})
    has_temp = bool(props & {"temperature", "environment-temperature", "current-temperature"})
    has_humidity = bool(props & {"relative-humidity", "humidity"})
    has_target_temp = bool(props & {"target-temperature", "target_temperature"})

    if has_brightness:
        return DeviceCategory.LIGHT
    if has_temp and has_target_temp and has_power:
        return DeviceCategory.THERMOSTAT
    if has_temp and has_target_temp:
        return DeviceCategory.HEATER
    if has_temp and not has_power:
        return DeviceCategory.TEMPERATURE_SENSOR
    if has_humidity and not has_power:
        return DeviceCategory.TEMPERATURE_SENSOR
    if has_power:
        return DeviceCategory.SWITCH
    return None


_cached_config: dict | None = None
_config_mtime: float = 0.0


def _load_user_config() -> dict:
    """加载用户自定义映射配置，带 mtime 缓存。"""
    global _cached_config, _config_mtime

    if not os.path.isfile(_YAML_PATH):
        return {}

    try:
        mtime = os.path.getmtime(_YAML_PATH)
        if _cached_config is not None and mtime == _config_mtime:
            return _cached_config

        with open(_YAML_PATH, encoding="utf-8") as f:
            config = yaml.safe_load(f) or {}

        _cached_config = config
        _config_mtime = mtime
        return config
    except Exception as e:
        logger.warning("加载 %s 失败: %s", _YAML_PATH, e)
        return {}


def map_device(device_info: dict) -> DeviceCategory:
    """根据设备信息判断 HomeKit 设备类别。

    优先级链：用户自定义 > 内置 model 规则 > spec_data 推断 > 兜底策略。

    Args:
        device_info: 设备信息 dict，包含 "model" 和可选的 "spec_data"
    """
    model = (device_info.get("model") or "").lower()

    # 1. 用户自定义规则（精确 model 匹配）
    user_config = _load_user_config()
    user_devices = user_config.get("devices") or {}
    if model in user_devices:
        try:
            return DeviceCategory(user_devices[model])
        except ValueError:
            logger.warning("用户配置中 %s 的类别 '%s' 无效", model, user_devices[model])

    # 2. 内置 model 规则（子串匹配）
    for keyword, category in _MODEL_RULES:
        if keyword in model:
            return category

    # 3. spec_data 智能推断
    fallback = user_config.get("fallback", "auto")
    if fallback == "auto":
        inferred = _infer_from_spec(device_info.get("spec_data"))
        if inferred:
            logger.info("设备 %s (model=%s) 通过 spec_data 推断为 %s", device_info.get("did"), model, inferred.value)
            return inferred

    # 4. 最终兜底
    if model:
        logger.info("设备 %s (model=%s) 未匹配任何规则，使用兜底策略: %s", device_info.get("did"), model, fallback)
    return DeviceCategory.IGNORED if fallback == "ignore" else DeviceCategory.SWITCH
