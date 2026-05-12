import secrets
import time
import uuid


def normalize_session_id(raw_session_id: str | None) -> tuple[str, bool]:
    """
    规范化 session id。

    Returns:
        tuple[str, bool]: (session_id, resumed)
    """
    if raw_session_id:
        try:
            return str(uuid.UUID(raw_session_id)), True
        except ValueError as e:
            raise SystemExit(f"无效的 --resume session id: {raw_session_id}\n{e}") from e

    return generate_session_id(), False


def generate_session_id() -> str:
    """
    生成新的 session id。

    优先使用标准库 uuid7；如果运行时不支持，则生成兼容 UUIDv7 布局的 ID。
    """
    if hasattr(uuid, "uuid7"):
        return str(uuid.uuid7())

    # 48-bit Unix epoch milliseconds + UUIDv7 version/variant bits + 74 random bits
    ts_ms = int(time.time() * 1000) & ((1 << 48) - 1)
    rand_a = secrets.randbits(12)
    rand_b = secrets.randbits(62)

    value = ts_ms << 80
    value |= 0x7 << 76
    value |= rand_a << 64
    value |= 0b10 << 62
    value |= rand_b
    return str(uuid.UUID(int=value))
