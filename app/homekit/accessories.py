import logging

import httpx
from pyhap import const as hap_const
from pyhap.accessory import Accessory

from app.homekit.mapper import DeviceCategory

logger = logging.getLogger(__name__)

_POLL_INTERVAL = 10  # seconds between state polls

# 属性名候选列表（按优先级排序，用于自动发现）
_POWER_PROPS = ["on", "power", "switch"]
_BRIGHTNESS_PROPS = ["brightness"]
_COLORTEMP_PROPS = ["color_temperature", "color-temp", "color_temp"]
_CURR_TEMP_PROPS = ["temperature", "environment-temperature", "current-temperature"]
_TARGET_TEMP_PROPS = ["target-temperature", "target_temperature"]
_HUMIDITY_PROPS = ["relative-humidity", "humidity"]


def _discover_prop(spec_data: dict | None, candidates: list[str]) -> str | None:
    """从 spec_data 中查找第一个匹配的属性名。"""
    if not spec_data:
        return None
    prop_names = _extract_prop_names(spec_data)
    for c in candidates:
        if c in prop_names:
            return c
    return None


def _discover_prop_type(spec_data: dict | None, prop_name: str) -> str | None:
    """获取属性的 type 字段。"""
    if not spec_data:
        return None
    for prop in spec_data.get("properties", []):
        if prop.get("name") == prop_name:
            return prop.get("type")
    return None


def _extract_prop_names(spec_data: dict) -> set[str]:
    """从 spec_data 中提取所有属性名。"""
    names = set()
    if not spec_data:
        return names
    for prop in spec_data.get("properties", []):
        name = prop.get("name")
        if name:
            names.add(name)
    return names


class _MijiaAccessory(Accessory):
    """Base class for all mijia device accessories."""

    def __init__(self, driver, display_name, aid, api_url: str, token: str, did: str, **kwargs):
        super().__init__(driver, display_name, aid=aid)
        self._api_url = api_url
        self._token = token
        self._did = did

    def _api_get(self, path: str) -> dict | None:
        try:
            resp = httpx.get(
                f"{self._api_url}{path}",
                headers={"Authorization": f"Bearer {self._token}"},
                timeout=10,
            )
            data = resp.json()
            return data.get("data")
        except Exception as e:
            logger.warning("API GET %s failed: %s", path, e)
            return None

    def _api_put(self, path: str, value) -> dict | None:
        try:
            resp = httpx.put(
                f"{self._api_url}{path}",
                json={"value": value},
                headers={"Authorization": f"Bearer {self._token}", "Content-Type": "application/json"},
                timeout=10,
            )
            data = resp.json()
            return data.get("data")
        except Exception as e:
            logger.warning("API PUT %s failed: %s", path, e)
            return None


def _is_bool_prop(spec_data, prop_name):
    return _discover_prop_type(spec_data, prop_name) == "bool"


def _power_value(spec_data, prop_name, homekit_on):
    """将 HomeKit On/Off 转换为设备属性值。"""
    if _is_bool_prop(spec_data, prop_name):
        return bool(homekit_on)
    return "on" if homekit_on else "off"


def _is_power_on(spec_data, prop_name, value):
    """判断设备返回值是否为 On 状态。"""
    if _is_bool_prop(spec_data, prop_name):
        return bool(value)
    return value == "on"


class MijiaLight(_MijiaAccessory):
    """灯光设备 → HomeKit Lightbulb."""

    category = hap_const.CATEGORY_LIGHTBULB

    def __init__(self, driver, display_name, aid, api_url, token, did, spec_data=None, **kwargs):
        super().__init__(driver, display_name, aid, api_url, token, did)

        self._spec_data = spec_data
        self._power_prop = _discover_prop(spec_data, _POWER_PROPS) or "power"
        self._brightness_prop = _discover_prop(spec_data, _BRIGHTNESS_PROPS) or "brightness"

        optional_chars = ["Brightness"]

        self._has_colortemp = False
        self._colortemp_prop = _discover_prop(spec_data, _COLORTEMP_PROPS)
        if self._colortemp_prop:
            self._has_colortemp = True
            optional_chars.append("ColorTemperature")

        serv = self.add_preload_service("Lightbulb", chars=optional_chars)
        self.char_on = serv.configure_char("On", value=False)
        self.char_brightness = serv.configure_char("Brightness", value=100)
        if self._has_colortemp:
            self.char_colortemp = serv.configure_char("ColorTemperature", value=200)

        serv.setter_callback = self._set_chars

    def _set_chars(self, char_values):
        if "On" in char_values:
            self._api_put(
                f"/devices/{self._did}/props/{self._power_prop}",
                _power_value(self._spec_data, self._power_prop, char_values["On"]),
            )
        if "Brightness" in char_values:
            self._api_put(f"/devices/{self._did}/props/{self._brightness_prop}", char_values["Brightness"])
        if "ColorTemperature" in char_values and self._has_colortemp:
            self._api_put(f"/devices/{self._did}/props/{self._colortemp_prop}", char_values["ColorTemperature"])

    @Accessory.run_at_interval(_POLL_INTERVAL)
    def run(self):
        result = self._api_get(f"/devices/{self._did}/props/{self._power_prop}")
        if result and result.get("value") is not None:
            self.char_on.set_value(_is_power_on(self._spec_data, self._power_prop, result["value"]))

        result = self._api_get(f"/devices/{self._did}/props/{self._brightness_prop}")
        if result and result.get("value") is not None:
            self.char_brightness.set_value(int(result["value"]))


class MijiaOutlet(_MijiaAccessory):
    """插座/开关 → HomeKit Outlet."""

    category = hap_const.CATEGORY_OUTLET

    def __init__(self, driver, display_name, aid, api_url, token, did, spec_data=None, **kwargs):
        super().__init__(driver, display_name, aid, api_url, token, did)
        self._power_prop = _discover_prop(spec_data, _POWER_PROPS) or "power"
        self._spec_data = spec_data

        serv = self.add_preload_service("Outlet")
        self.char_on = serv.configure_char("On", value=False)
        self.char_in_use = serv.configure_char("OutletInUse", value=False)
        serv.setter_callback = self._set_chars

    def _set_chars(self, char_values):
        if "On" in char_values:
            self._api_put(
                f"/devices/{self._did}/props/{self._power_prop}",
                _power_value(self._spec_data, self._power_prop, char_values["On"]),
            )

    @Accessory.run_at_interval(_POLL_INTERVAL)
    def run(self):
        result = self._api_get(f"/devices/{self._did}/props/{self._power_prop}")
        if result and result.get("value") is not None:
            is_on = _is_power_on(self._spec_data, self._power_prop, result["value"])
            self.char_on.set_value(is_on)
            self.char_in_use.set_value(is_on)


class MijiaSwitch(_MijiaAccessory):
    """通用开关设备 → HomeKit Switch."""

    category = hap_const.CATEGORY_SWITCH

    def __init__(self, driver, display_name, aid, api_url, token, did, spec_data=None, **kwargs):
        super().__init__(driver, display_name, aid, api_url, token, did)
        self._power_prop = _discover_prop(spec_data, _POWER_PROPS) or "power"
        self._spec_data = spec_data

        serv = self.add_preload_service("Switch")
        self.char_on = serv.configure_char("On", value=False)
        serv.setter_callback = self._set_chars

    def _set_chars(self, char_values):
        if "On" in char_values:
            self._api_put(
                f"/devices/{self._did}/props/{self._power_prop}",
                _power_value(self._spec_data, self._power_prop, char_values["On"]),
            )

    @Accessory.run_at_interval(_POLL_INTERVAL)
    def run(self):
        result = self._api_get(f"/devices/{self._did}/props/{self._power_prop}")
        if result and result.get("value") is not None:
            self.char_on.set_value(_is_power_on(self._spec_data, self._power_prop, result["value"]))


class MijiaTemperatureSensor(_MijiaAccessory):
    """温湿度传感器 → HomeKit TemperatureSensor + HumiditySensor."""

    category = hap_const.CATEGORY_SENSOR

    def __init__(self, driver, display_name, aid, api_url, token, did, spec_data=None, **kwargs):
        super().__init__(driver, display_name, aid, api_url, token, did)
        self._temp_prop = _discover_prop(spec_data, _CURR_TEMP_PROPS) or "temperature"
        self._humidity_prop = _discover_prop(spec_data, _HUMIDITY_PROPS) or "humidity"

        temp_serv = self.add_preload_service("TemperatureSensor")
        self.char_temp = temp_serv.configure_char("CurrentTemperature", value=0)

        if self._humidity_prop:
            hum_serv = self.add_preload_service("HumiditySensor")
            self.char_humidity = hum_serv.configure_char("CurrentRelativeHumidity", value=0)
        else:
            self.char_humidity = None

    @Accessory.run_at_interval(_POLL_INTERVAL)
    def run(self):
        result = self._api_get(f"/devices/{self._did}/props/{self._temp_prop}")
        if result and result.get("value") is not None:
            self.char_temp.set_value(float(result["value"]))

        if self.char_humidity and self._humidity_prop:
            result = self._api_get(f"/devices/{self._did}/props/{self._humidity_prop}")
            if result and result.get("value") is not None:
                self.char_humidity.set_value(float(result["value"]))


class MijiaThermostat(_MijiaAccessory):
    """空调伴侣/温控设备 → HomeKit Thermostat."""

    category = hap_const.CATEGORY_THERMOSTAT

    def __init__(self, driver, display_name, aid, api_url, token, did, spec_data=None, **kwargs):
        super().__init__(driver, display_name, aid, api_url, token, did)
        self._power_prop = _discover_prop(spec_data, _POWER_PROPS) or "power"
        self._target_temp_prop = _discover_prop(spec_data, _TARGET_TEMP_PROPS) or "target-temperature"
        self._spec_data = spec_data

        serv = self.add_preload_service("Thermostat")
        self.char_current_temp = serv.configure_char("CurrentTemperature", value=0)
        self.char_target_temp = serv.configure_char("TargetTemperature", value=25)
        self.char_current_state = serv.configure_char("CurrentHeatingCoolingState", value=0)
        self.char_target_state = serv.configure_char("TargetHeatingCoolingState", value=0)
        serv.configure_char("TemperatureDisplayUnits", value=0)
        serv.setter_callback = self._set_chars

    def _set_chars(self, char_values):
        if "TargetTemperature" in char_values:
            self._api_put(f"/devices/{self._did}/props/{self._target_temp_prop}", char_values["TargetTemperature"])
        if "TargetHeatingCoolingState" in char_values:
            self._api_put(
                f"/devices/{self._did}/props/{self._power_prop}",
                _power_value(self._spec_data, self._power_prop, char_values["TargetHeatingCoolingState"] != 0),
            )

    @Accessory.run_at_interval(_POLL_INTERVAL)
    def run(self):
        result = self._api_get(f"/devices/{self._did}/props/{self._power_prop}")
        if result and result.get("value") is not None:
            is_on = _is_power_on(self._spec_data, self._power_prop, result["value"])
            self.char_current_state.set_value(1 if is_on else 0)


class MijiaHeater(_MijiaAccessory):
    """取暖器 → HomeKit HeaterCooler."""

    category = hap_const.CATEGORY_HEATER

    def __init__(self, driver, display_name, aid, api_url, token, did, spec_data=None, **kwargs):
        super().__init__(driver, display_name, aid, api_url, token, did)
        self._power_prop = _discover_prop(spec_data, _POWER_PROPS) or "power"
        self._curr_temp_prop = _discover_prop(spec_data, _CURR_TEMP_PROPS) or "temperature"
        self._target_temp_prop = _discover_prop(spec_data, _TARGET_TEMP_PROPS) or "target-temperature"
        self._spec_data = spec_data

        serv = self.add_preload_service("HeaterCooler", chars=["HeatingThresholdTemperature"])
        self.char_active = serv.configure_char("Active", value=0)
        self.char_current_temp = serv.configure_char("CurrentTemperature", value=0)
        serv.configure_char("CurrentHeaterCoolerState", value=1)
        serv.configure_char("TargetHeaterCoolerState", value=0)
        self.char_target_temp = serv.configure_char("HeatingThresholdTemperature", value=20)
        serv.setter_callback = self._set_chars

    def _set_chars(self, char_values):
        if "Active" in char_values:
            self._api_put(
                f"/devices/{self._did}/props/{self._power_prop}",
                _power_value(self._spec_data, self._power_prop, char_values["Active"]),
            )
        if "HeatingThresholdTemperature" in char_values:
            self._api_put(
                f"/devices/{self._did}/props/{self._target_temp_prop}",
                char_values["HeatingThresholdTemperature"],
            )

    @Accessory.run_at_interval(_POLL_INTERVAL)
    def run(self):
        result = self._api_get(f"/devices/{self._did}/props/{self._curr_temp_prop}")
        if result and result.get("value") is not None:
            self.char_current_temp.set_value(float(result["value"]))

        result = self._api_get(f"/devices/{self._did}/props/{self._power_prop}")
        if result and result.get("value") is not None:
            self.char_active.set_value(1 if _is_power_on(self._spec_data, self._power_prop, result["value"]) else 0)


# 类别 → Accessory 类的映射
CATEGORY_TO_ACCESSORY: dict[DeviceCategory, type[_MijiaAccessory]] = {
    DeviceCategory.LIGHT: MijiaLight,
    DeviceCategory.OUTLET: MijiaOutlet,
    DeviceCategory.SWITCH: MijiaSwitch,
    DeviceCategory.TEMPERATURE_SENSOR: MijiaTemperatureSensor,
    DeviceCategory.HUMIDITY_SENSOR: MijiaTemperatureSensor,
    DeviceCategory.THERMOSTAT: MijiaThermostat,
    DeviceCategory.HEATER: MijiaHeater,
    # CAMERA 暂不支持（需要 RTP 流，后续配合 go2rtc 实现）
}


def create_accessory(driver, device_info: dict, api_url: str, token: str, aid: int) -> _MijiaAccessory | None:
    """根据设备信息创建对应的 HomeKit Accessory 实例。

    Args:
        driver: HAP AccessoryDriver
        device_info: 设备信息 dict（did, name, model, spec_data 等）
        api_url: Flask API 基础 URL
        token: JWT Token
        aid: Accessory ID（在 Bridge 内必须唯一）
    """
    from app.homekit.mapper import map_device

    category = map_device(device_info)
    if category == DeviceCategory.IGNORED:
        return None

    accessory_cls = CATEGORY_TO_ACCESSORY.get(category)
    if not accessory_cls:
        return None

    return accessory_cls(
        driver,
        device_info.get("name", "Unknown"),
        aid=aid,
        api_url=api_url,
        token=token,
        did=device_info["did"],
        spec_data=device_info.get("spec_data"),
    )
