import os

from dotenv import load_dotenv

load_dotenv()

MIJIA_API_URL = os.environ.get("MIJIA_API_URL", "http://127.0.0.1:5000/api")
MIJIA_TOKEN = os.environ.get("MIJIA_TOKEN", "")
BLE_ADAPTER = os.environ.get("BLE_ADAPTER", "")
BLE_SCAN_TIMEOUT = int(os.environ.get("BLE_SCAN_TIMEOUT", "30"))
OFFLINE_THRESHOLD_SECONDS = int(os.environ.get("BLE_OFFLINE_THRESHOLD", "1800"))

XIAOMI_MANUFACTURER_ID = 0x0959
