"""HomeKit Bridge 启动入口。

用法: python -m app.homekit
"""
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)

# E402: logging 配置必须在 import 之前
from app.homekit import start_homekit_bridge  # noqa: E402

start_homekit_bridge()
