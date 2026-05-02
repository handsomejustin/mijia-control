"""测试 DeviceService 的超时保护机制。"""

import time
from unittest.mock import MagicMock, patch

import pytest

from app.services.device_service import DeviceService


def _make_device(get_return=None, set_return=None, action_return=None, hang=False):
    """构造 mock mijiaDevice。hang=True 时 get/set/run_action 会阻塞。"""
    device = MagicMock()
    device.prop_list = {}

    if hang:

        def _hang(*args, **kwargs):
            time.sleep(30)

        device.get.side_effect = _hang
        device.set.side_effect = _hang
        device.run_action.side_effect = _hang
    else:
        device.get.return_value = get_return
        device.set.return_value = set_return
        device.run_action.return_value = action_return

    return device


class TestGetPropertyTimeout:
    """get_property 超时保护测试。"""

    @patch("app.services.device_service.mijiaDevice")
    @patch("app.services.device_service.api_pool")
    def test_returns_value_on_success(self, mock_pool, mock_device_cls):
        device = _make_device(get_return=80)
        mock_device_cls.return_value = device
        mock_pool.get_api.return_value = MagicMock()

        result = DeviceService.get_property(1, "did123", "brightness")
        assert result["value"] == 80
        assert result["did"] == "did123"
        assert result["prop_name"] == "brightness"

    @patch("app.services.device_service.mijiaDevice")
    @patch("app.services.device_service.api_pool")
    def test_raises_timeout_on_hang(self, mock_pool, mock_device_cls):
        device = _make_device(hang=True)
        mock_device_cls.return_value = device
        mock_pool.get_api.return_value = MagicMock()

        with pytest.raises(TimeoutError, match="超时"):
            DeviceService.get_property(1, "did123", "brightness", timeout=1)


class TestSetPropertyTimeout:
    """set_property 超时保护测试。"""

    @patch("app.services.device_service.mijiaDevice")
    @patch("app.services.device_service.api_pool")
    def test_returns_value_on_success(self, mock_pool, mock_device_cls):
        device = _make_device()
        mock_device_cls.return_value = device
        mock_pool.get_api.return_value = MagicMock()

        with patch("app.services.device_service._emit_device_update"):
            result = DeviceService.set_property(1, "did123", "brightness", 50)
        assert result["value"] == 50

    @patch("app.services.device_service.mijiaDevice")
    @patch("app.services.device_service.api_pool")
    def test_raises_timeout_on_hang(self, mock_pool, mock_device_cls):
        device = _make_device(hang=True)
        mock_device_cls.return_value = device
        mock_pool.get_api.return_value = MagicMock()

        with pytest.raises(TimeoutError, match="超时"):
            DeviceService.set_property(1, "did123", "brightness", 50, timeout=1)


class TestRunActionTimeout:
    """run_action 超时保护测试。"""

    @patch("app.services.device_service.mijiaDevice")
    @patch("app.services.device_service.api_pool")
    def test_returns_success_on_normal(self, mock_pool, mock_device_cls):
        device = _make_device()
        mock_device_cls.return_value = device
        mock_pool.get_api.return_value = MagicMock()

        with patch("app.services.device_service._emit_device_update"):
            result = DeviceService.run_action(1, "did123", "play")
        assert result["status"] == "executed"

    @patch("app.services.device_service.mijiaDevice")
    @patch("app.services.device_service.api_pool")
    def test_raises_timeout_on_hang(self, mock_pool, mock_device_cls):
        device = _make_device(hang=True)
        mock_device_cls.return_value = device
        mock_pool.get_api.return_value = MagicMock()

        with pytest.raises(TimeoutError, match="超时"):
            DeviceService.run_action(1, "did123", "play", timeout=1)
