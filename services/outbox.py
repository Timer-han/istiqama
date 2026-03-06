"""services/outbox.py – admin broadcast sender with rate limiting."""
from __future__ import annotations

import asyncio
import logging

from aiogram import Bot

import services.db as db
from adapters.storage_postgres import fetch
from constants import OUTBOX_RATE_LIMIT, OUTBOX_PROCESS_LIMIT, OUTBOX_SLEEP_SECONDS

logger = logging.getLogger(__name__)


async def outbox_task(bot: Bot, rate_limit: int = OUTBOX_RATE_LIMIT) -> None:
    logger.info("Outbox task started (rate_limit=%d msg/s)", rate_limit)
    while True:
        try:
            await _process_outbox(bot, rate_limit=rate_limit)
        except Exception as exc:
            logger.exception("Outbox error: %s", exc)
        await asyncio.sleep(OUTBOX_SLEEP_SECONDS)


async def _process_outbox(bot: Bot, rate_limit: int = OUTBOX_RATE_LIMIT) -> None:
    messages = await db.get_pending_outbox(limit=OUTBOX_PROCESS_LIMIT)

    for msg in messages:
        await db.mark_outbox_sending(msg["id"])
        try:
            if msg["target"] == "all":
                await _broadcast_all(bot, msg["text"], rate_limit=rate_limit)
            else:
                await bot.send_message(
                    chat_id=int(msg["target"]),
                    text=msg["text"],
                    parse_mode="Markdown",
                )
            await db.mark_outbox_sent(msg["id"])
        except Exception as e:
            logger.error("Outbox msg %d failed: %s", msg["id"], e)
            await db.mark_outbox_failed(msg["id"])


async def _broadcast_all(bot: Bot, text: str, rate_limit: int = OUTBOX_RATE_LIMIT) -> None:
    users = await fetch("SELECT telegram_id FROM users")
    delay = 1.0 / rate_limit

    for user in users:
        try:
            await bot.send_message(
                chat_id=user["telegram_id"],
                text=text,
                parse_mode="Markdown",
            )
        except Exception as e:
            logger.warning("Broadcast to %d failed: %s", user["telegram_id"], e)
        await asyncio.sleep(delay)