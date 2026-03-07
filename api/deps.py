"""api/deps.py – FastAPI dependency: parse X-Telegram-Init-Data → DB user."""
from __future__ import annotations

from fastapi import Request, HTTPException
from asyncpg import Record

import services.db as db
from bot.config import config
from api.auth import verify_init_data


async def get_current_user(request: Request) -> Record:
    """
    Reads the X-Telegram-Init-Data header, validates it via HMAC,
    fetches (or creates) the corresponding DB user, and returns the record.

    Raises HTTP 401 on any validation failure.
    """
    init_data = request.headers.get("X-Telegram-Init-Data", "").strip()
    if not init_data:
        raise HTTPException(status_code=401, detail="Missing X-Telegram-Init-Data")

    parsed = verify_init_data(init_data, config.bot_token)
    if parsed is None:
        raise HTTPException(status_code=401, detail="Invalid initData signature")

    tg_user = parsed.get("tg_user", {})
    telegram_id = tg_user.get("id")
    if not telegram_id:
        raise HTTPException(status_code=401, detail="No user id in initData")

    # Get existing user from DB
    user = await db.get_user_by_telegram_id(int(telegram_id))

    if user is None:
        # Auto-create: user opened the Mini App without /start yet
        first = tg_user.get("first_name", "")
        last = tg_user.get("last_name", "")
        display = (first + (" " + last if last else "")).strip() or "User"
        user = await db.get_or_create_user(
            telegram_id=int(telegram_id),
            username=tg_user.get("username"),
            display_name=display,
            tz="Europe/Moscow",
        )

    if user is None:
        raise HTTPException(status_code=401, detail="Could not resolve user")

    return user
