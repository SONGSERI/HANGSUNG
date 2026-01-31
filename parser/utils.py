# utils.py
import hashlib

def make_hash(*args) -> str:
    raw = "|".join(map(str, args))
    return hashlib.sha256(raw.encode()).hexdigest()

def time_to_seconds(time_str: str) -> int:
    """
    HH:MM:SS → seconds
    """
    h, m, s = map(int, time_str.split(":"))
    return h * 3600 + m * 60 + s
