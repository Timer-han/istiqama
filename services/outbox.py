"""services/outbox.py – admin broadcast sender with rate limiting."""
from __future__ import annotations

import asyncio
import logging

from aiogram import Bot

import services.db as db
from adapters.storage_postgres import fetch, get_pool

logger = logging.getLogger(__name__)

RATE_LIMIT = 20        # messages per second (Telegram limit ~30/s, be conservative)
SLEEP_SECONDS = 5


async def outbox_task(bot: Bot) -> None:
    logger.info("Outbox task started")
    while True:
        try:
            await _process_outbox(bot)
        except Exception as exc:
            logger.exception("Outbox error: %s", exc)
        await asyncio.sleep(SLEEP_SECONDS)


async def _process_outbox(bot: Bot) -> None:
    async with get_pool().acquire() as con:
        messages = await con.fetch(
            """
            SELECT * FROM outbox_messages
            WHERE status='pending'
              AND (scheduled_at IS NULL OR scheduled_at <= NOW())
            ORDER BY id
            LIMIT 5
            FOR UPDATE SKIP LOCKED
            """
        )

    for msg in messages:
        await db.mark_outbox_sending(msg["id"])
        try:
            if msg["target"] == "all":
                await _broadcast_all(bot, msg["text"])
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


async def _broadcast_all(bot: Bot, text: str) -> None:
    from adapters.storage_postgres import fetch
    users = await fetch("SELECT telegram_id FROM users")
    delay = 1.0 / RATE_LIMIT

    for user in users:
        try:
            await bot.send_message(chat_id=user["telegram_id"], text=text, parse_mode="Markdown")
        except Exception as e:
            logger.warning("Broadcast to %d failed: %s", user["telegram_id"], e)
        await asyncio.sleep(delay)
