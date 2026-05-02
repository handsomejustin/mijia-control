import pytest
import yaml

from app.homekit.mapper import (
    DeviceCategory,
    _extract_prop_names,
    _infer_from_spec,
    map_device,
)


def _spec(*props):
    """构造 spec_data，props 为属性名列表。"""
    return {"properties": [{"name": p, "type": "bool"} for p in props]}


# --- _extract_prop_names ---


class TestExtractPropNames:
    def test_none(self):
        assert _extract_prop_names(None) == set()

    def test_empty(self):
        assert _extract_prop_names({}) == set()
        assert _extract_prop_names({"properties": []}) == set()

    def test_basic(self):
        result = _extract_prop_names(_spec("on", "brightness"))
        assert result == {"on", "brightness"}


# --- _infer_from_spec ---


class TestInferFromSpec:
    def test_none(self):
        assert _infer_from_spec(None) is None

    def test_empty(self):
        assert _infer_from_spec({}) is None

    def test_brightness_is_light(self):
        assert _infer_from_spec(_spec("on", "brightness")) == DeviceCategory.LIGHT

    def test_power_only_is_switch(self):
        assert _infer_from_spec(_spec("on")) == DeviceCategory.SWITCH

    def test_temp_target_power_is_thermostat(self):
        assert _infer_from_spec(_spec("on", "temperature", "target-temperature")) == DeviceCategory.THERMOSTAT

    def test_temp_target_no_power_is_heater(self):
        assert _infer_from_spec(_spec("temperature", "target-temperature")) == DeviceCategory.HEATER

    def test_temp_no_power_is_sensor(self):
        assert _infer_from_spec(_spec("temperature")) == DeviceCategory.TEMPERATURE_SENSOR

    def test_humidity_no_power_is_sensor(self):
        assert _infer_from_spec(_spec("relative-humidity")) == DeviceCategory.TEMPERATURE_SENSOR

    def test_humidity_with_power_is_switch(self):
        assert _infer_from_spec(_spec("on", "relative-humidity")) == DeviceCategory.SWITCH


# --- map_device (built-in rules) ---


class TestMapDeviceBuiltIn:
    @pytest.mark.parametrize(
        "model, expected",
        [
            ("yeelink.light.ceil26", DeviceCategory.LIGHT),
            ("philips.light.bulb", DeviceCategory.LIGHT),
            ("chuangmi.plug.m1", DeviceCategory.OUTLET),
            ("lumi.switch.aq2", DeviceCategory.OUTLET),
            ("zhimi.airpurifier.mb4a", DeviceCategory.SWITCH),
            ("roborock.vacuum.s5", DeviceCategory.SWITCH),
            ("acpartner.v3", DeviceCategory.THERMOSTAT),
            ("heater.za1", DeviceCategory.HEATER),
            ("ht.sen.ht1", DeviceCategory.TEMPERATURE_SENSOR),
            ("chuangmi.camera.21h", DeviceCategory.CAMERA),
            ("router.xxx", DeviceCategory.IGNORED),
            ("cardvr.xxx", DeviceCategory.IGNORED),
            ("kettle.xxx", DeviceCategory.IGNORED),
        ],
    )
    def test_known_models(self, model, expected):
        result = map_device({"model": model, "did": "test"})
        assert result == expected

    def test_empty_model(self):
        assert map_device({"model": "", "did": "test", "spec_data": _spec("on")}) == DeviceCategory.SWITCH

    def test_unknown_model_with_spec(self):
        result = map_device({"model": "unknown.brand.xyz", "did": "test", "spec_data": _spec("brightness")})
        assert result == DeviceCategory.LIGHT

    def test_unknown_model_without_spec(self):
        result = map_device({"model": "unknown.brand.xyz", "did": "test"})
        assert result == DeviceCategory.SWITCH


# --- map_device (user config override) ---


class TestMapDeviceUserConfig:
    def test_user_override(self, tmp_path, monkeypatch):
        config = {"devices": {"custom.model.v1": "light"}, "fallback": "auto"}
        config_file = tmp_path / "homekit_mapping.yaml"
        config_file.write_text(yaml.dump(config), encoding="utf-8")

        import app.homekit.mapper as m
        monkeypatch.setattr(m, "_YAML_PATH", str(config_file))
        monkeypatch.setattr(m, "_cached_config", None)

        result = map_device({"model": "custom.model.v1", "did": "test"})
        assert result == DeviceCategory.LIGHT

    def test_user_ignore(self, tmp_path, monkeypatch):
        config = {"devices": {"noise.model": "ignored"}, "fallback": "auto"}
        config_file = tmp_path / "homekit_mapping.yaml"
        config_file.write_text(yaml.dump(config), encoding="utf-8")

        import app.homekit.mapper as m
        monkeypatch.setattr(m, "_YAML_PATH", str(config_file))
        monkeypatch.setattr(m, "_cached_config", None)

        result = map_device({"model": "noise.model", "did": "test"})
        assert result == DeviceCategory.IGNORED

    def test_fallback_ignore(self, tmp_path, monkeypatch):
        config = {"fallback": "ignore"}
        config_file = tmp_path / "homekit_mapping.yaml"
        config_file.write_text(yaml.dump(config), encoding="utf-8")

        import app.homekit.mapper as m
        monkeypatch.setattr(m, "_YAML_PATH", str(config_file))
        monkeypatch.setattr(m, "_cached_config", None)

        result = map_device({"model": "totally.unknown", "did": "test"})
        assert result == DeviceCategory.IGNORED

    def test_invalid_category_ignored(self, tmp_path, monkeypatch):
        config = {"devices": {"bad.model": "nonexistent"}}
        config_file = tmp_path / "homekit_mapping.yaml"
        config_file.write_text(yaml.dump(config), encoding="utf-8")

        import app.homekit.mapper as m
        monkeypatch.setattr(m, "_YAML_PATH", str(config_file))
        monkeypatch.setattr(m, "_cached_config", None)

        # invalid category falls through to spec_data inference
        result = map_device({"model": "bad.model", "did": "test", "spec_data": _spec("on")})
        assert result == DeviceCategory.SWITCH
