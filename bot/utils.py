"""bot/utils.py – misc helpers."""
from __future__ import annotations

import json
from typing import Optional

from asyncpg import Record


def challenge_text(challenge, lang: str = "ru") -> tuple[str, str]:
    """Return (title, question) for given lang, fallback to ru."""
    meta = challenge["metadata"]
    if isinstance(meta, str):
        meta = json.loads(meta)
    translations = meta.get("translations", {})
    t = translations.get(lang) or translations.get("ru", {})
    return t.get("title", challenge["slug"]), t.get("question", "")


def challenge_description(challenge, lang: str = "ru") -> str:
    """Return description string (may be empty)."""
    meta = challenge["metadata"]
    if isinstance(meta, str):
        meta = json.loads(meta)
    translations = meta.get("translations", {})
    t = translations.get(lang) or translations.get("ru", {})
    return t.get("description", "")


def challenge_options(challenge, lang: str = "ru") -> list:
    meta = challenge["metadata"]
    if isinstance(meta, str):
        meta = json.loads(meta)
    translations = meta.get("translations", {})
    t = translations.get(lang) or translations.get("ru", {})
    return t.get("options", [])


def challenge_schedule(challenge: Record) -> str:
    meta = challenge["metadata"]
    if isinstance(meta, str):
        meta = json.loads(meta)
    return meta.get("schedule_time", "06:00")


def tz_from_coords(lat: float, lon: float) -> str:
    try:
        from timezonefinder import TimezoneFinder
        tf = TimezoneFinder()
        tz = tf.timezone_at(lat=lat, lng=lon)
        return tz or "UTC"
    except Exception:
        return "UTC"
