"""测试 DeviceService 的超时保护与重试机制。"""

import time
from concurrent.futures import TimeoutError as FuturesTimeoutError
from unittest.mock import MagicMock, patch

import pytest

from app.services.device_service import DeviceService, MIJIA_CALL_TIMEOUT, MIJIA_CALL_RETRIES


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


class TestTimeoutConstants:
    """验证超时与重试常量。"""

    def test_default_timeout_is_20(self):
        assert MIJIA_CALL_TIMEOUT == 20

    def test_default_retries_is_1(self):
        assert MIJIA_CALL_RETRIES == 1


class TestRetryMechanism:
    """_call_with_timeout 重试机制测试。"""

    def test_succeeds_on_first_try(self):
        from app.services.device_service import _call_with_timeout

        result = _call_with_timeout(lambda: 42, timeout=2, retries=1)
        assert result == 42

    def test_succeeds_on_retry_after_timeout(self):
        from app.services.device_service import _call_with_timeout

        call_count = 0

        def flaky_fn():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                time.sleep(5)  # 会触发超时
            return "ok"

        result = _call_with_timeout(flaky_fn, timeout=1, retries=1)
        assert result == "ok"
        assert call_count == 2

    def test_exhausts_retries_and_raises(self):
        from app.services.device_service import _call_with_timeout

        def slow_fn():
            time.sleep(5)

        with pytest.raises(TimeoutError, match="超时"):
            _call_with_timeout(slow_fn, timeout=1, retries=1)

    def test_zero_retries_no_retry(self):
        from app.services.device_service import _call_with_timeout

        call_count = 0

        def slow_fn():
            nonlocal call_count
            call_count += 1
            time.sleep(5)

        with pytest.raises(TimeoutError, match="超时"):
            _call_with_timeout(slow_fn, timeout=1, retries=0)
        assert call_count == 1

    def test_non_timeout_error_not_retried(self):
        from app.services.device_service import _call_with_timeout

        call_count = 0

        def bad_fn():
            nonlocal call_count
            call_count += 1
            raise ValueError("bad")

        with pytest.raises(ValueError, match="bad"):
            _call_with_timeout(bad_fn, timeout=2, retries=2)
        assert call_count == 1
