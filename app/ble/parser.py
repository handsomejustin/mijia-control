import logging
import struct
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

PARSERS: dict[str, "PayloadParser"] = {}


class PayloadParser(ABC):
    model: str
    capabilities: list[str]

    @abstractmethod
    def parse(self, payload: bytes) -> dict: ...


def register_parser(parser_cls: type[PayloadParser]) -> type[PayloadParser]:
    PARSERS[parser_cls.model] = parser_cls()
    return parser_cls


def get_parser(model: str) -> PayloadParser | None:
    return PARSERS.get(model)


def decrypt_payload(encrypted: bytes, bindkey: str, mac: str) -> bytes | None:
    try:
        from Crypto.Cipher import AES
    except ImportError:
        logger.error("pycryptodome 未安装，无法解密 BLE 数据。请运行: pip install pycryptodome")
        return None

    try:
        key = bytes.fromhex(bindkey)
        mac_bytes = bytes.fromhex(mac.replace(":", ""))
        nonce = mac_bytes + encrypted[:4] + encrypted[4:6]

        cipher = AES.new(key, AES.MODE_CCM, nonce=nonce, mac_len=4)
        decrypted = cipher.decrypt_and_verify(encrypted[6:-4], encrypted[-4:])
        return decrypted
    except Exception as e:
        logger.debug("解密失败: %s", e)
        return None


@register_parser
class LYWSD03MMCParser(PayloadParser):
    model = "lywsd03mmc"
    capabilities = ["temperature", "humidity", "battery"]

    def parse(self, payload: bytes) -> dict:
        result = {}
        if len(payload) >= 2:
            temp = struct.unpack_from("<h", payload, 0)[0]
            result["temperature"] = round(temp / 10, 1)
        if len(payload) >= 4:
            humidity = struct.unpack_from("<H", payload, 2)[0]
            result["humidity"] = round(humidity / 10, 1)
        if len(payload) >= 6:
            result["battery"] = payload[5]
        return result


@register_parser
class LYWSDCGQParser(PayloadParser):
    model = "lywswdcgq"
    capabilities = ["temperature", "humidity", "battery"]

    def parse(self, payload: bytes) -> dict:
        result = {}
        if len(payload) >= 2:
            temp = struct.unpack_from("<h", payload, 0)[0]
            result["temperature"] = round(temp / 10, 1)
        if len(payload) >= 4:
            humidity = struct.unpack_from("<H", payload, 2)[0]
            result["humidity"] = round(humidity / 10, 1)
        if len(payload) >= 6:
            result["battery"] = payload[5]
        return result


@register_parser
class MJWSD05MMCParser(PayloadParser):
    model = "mjwsd05mmc"
    capabilities = ["temperature", "humidity", "battery"]

    def parse(self, payload: bytes) -> dict:
        result = {}
        if len(payload) >= 2:
            temp = struct.unpack_from("<h", payload, 0)[0]
            result["temperature"] = round(temp / 10, 1)
        if len(payload) >= 4:
            humidity = struct.unpack_from("<H", payload, 2)[0]
            result["humidity"] = round(humidity / 10, 1)
        if len(payload) >= 6:
            result["battery"] = payload[5]
        return result


@register_parser
class MJWSD06MMCParser(PayloadParser):
    model = "mjwsd06mmc"
    capabilities = ["temperature", "humidity", "battery"]

    def parse(self, payload: bytes) -> dict:
        result = {}
        if len(payload) >= 2:
            temp = struct.unpack_from("<h", payload, 0)[0]
            result["temperature"] = round(temp / 10, 1)
        if len(payload) >= 4:
            humidity = struct.unpack_from("<H", payload, 2)[0]
            result["humidity"] = round(humidity / 10, 1)
        if len(payload) >= 6:
            result["battery"] = payload[5]
        return result
