"""BLE 蓝牙传感器守护进程。

用法: python -m app.ble
"""

import asyncio
import logging
import sys

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)

from app.ble import run_scanner  # noqa: E402

asyncio.run(run_scanner())
