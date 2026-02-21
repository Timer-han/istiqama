"""bot/middleware.py – Per-request user injection middleware."""
from __future__ import annotations

import logging
from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

import services.db as db
from bot.i18n import user_lang as _user_lang

logger = logging.getLogger(__name__)


class UserMiddleware(BaseMiddleware):
    """
    Loads the current user from DB once per request and injects:
        data["db_user"]   – asyncpg.Record | None
        data["user_lang"] – str ("ru" / "en" / "tt")

    Handlers declare these as keyword arguments:
        async def handler(msg, db_user=None, user_lang: str = "ru"): ...
    """

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        from_user = data.get("event_from_user")
        db_user   = None

        if from_user is not None:
            try:
                db_user = await db.get_user_by_telegram_id(from_user.id)
            except Exception as exc:
                logger.warning("UserMiddleware: DB error for %s: %s", from_user.id, exc)

        data["db_user"]   = db_user
        data["user_lang"] = _user_lang(db_user)
        return await handler(event, data)
