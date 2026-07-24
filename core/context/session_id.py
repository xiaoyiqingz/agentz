import secrets
import time
import uuid


def normalize_session_id(raw_session_id: str | None) -> tuple[str, bool]:
    """Normalize a resume ID or generate a new session ID.

    Returns:
        ``(session_id, resumed)``.
    """
    if raw_session_id:
        try:
            return str(uuid.UUID(raw_session_id)), True
        except ValueError as exc:
            raise SystemExit(f"无效的 --resume session id: {raw_session_id}\n{exc}") from exc

    return generate_session_id(), False


def generate_session_id() -> str:
    """Generate a UUIDv7-compatible session ID."""
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
