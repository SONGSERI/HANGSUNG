# utils.py
import hashlib

def make_hash(*args) -> str:
    raw = "|".join(map(str, args))
    return hashlib.sha256(raw.encode()).hexdigest()

def parse_bool(value, default: bool = False) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"true", "1", "y", "yes", "t"}:
            return True
        if normalized in {"false", "0", "n", "no", "f"}:
            return False
    return default

def time_to_seconds(time_str: str) -> int:
    # HH:MM:SS → seconds
    h, m, s = map(int, time_str.split(":"))
    return h * 3600 + m * 60 + s
