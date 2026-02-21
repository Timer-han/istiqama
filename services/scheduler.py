"""services/scheduler.py – daily question sender + challenge announcements.

Two independent loops run inside scheduler_task():

1. _run_dispatcher(bot, storage)
   - One SQL query (get_due_participants) → index scan
   - Inactivity check via last_answer_day
   - Sends daily question, updates next_dispatch_at
   - For count-kind: sets FSM state so user reply is routed correctly

2. _run_announcer(bot)
   - Polls get_unannounced_challenges() every tick
   - For each new/launch-ready challenge: sends announcement to ALL users
   - Announcement includes title, description, kind, schedule, duration
   - Inline "Join" button per user in their own language
   - Marks challenge announced=True after sending
"""
from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime, timedelta, date

import pytz
from aiogram import Bot
from aiogram.fsm.storage.base import BaseStorage, StorageKey

import services.db as db
from bot.handlers import build_question_message
from bot.i18n import t, kind_label, user_lang as _user_lang, SUPPORTED_LANGS
from bot.keyboards import challenge_announce_kb
from bot.states import CountAnswerState
from bot.utils import challenge_text

logger = logging.getLogger(__name__)

INACTIVITY_DAYS = 3
ANNOUNCE_RATE   = 0.05   # seconds between announcement messages (~20 msg/s)


async def scheduler_task(
    bot: Bot,
    storage: BaseStorage,
    interval: int = 60,
) -> None:
    logger.info("Scheduler started (interval=%ds)", interval)
    while True:
        try:
            await _run_dispatcher(bot, storage)
            await _run_announcer(bot)
        except Exception:
            logger.exception("Scheduler error")
        await asyncio.sleep(interval)


# ─── Dispatcher ────────────────────────────────────────────────────────────

async def _run_dispatcher(bot: Bot, storage: BaseStorage) -> None:
    expired = await db.deactivate_expired_challenges()
    if expired:
        logger.info("Deactivated %d expired challenge(s)", expired)

    rows = await db.get_due_participants()
    if not rows:
        return

    logger.debug("Dispatcher: %d rows due", len(rows))

    for row in rows:
        user_id      = row["user_id"]
        challenge_id = row["challenge_id"]
        tz_str       = row["timezone"] or "UTC"
        try:
            tz = pytz.timezone(tz_str)
        except Exception:
            tz = pytz.UTC

        now_local   = datetime.now(tz)
        today_local = now_local.date()

        # Guard: already dispatched today?
        last_dispatch: date | None = row["last_dispatch_day"]
        if last_dispatch is not None and last_dispatch >= today_local:
            continue

        # Guard: schedule_time not yet reached?
        meta = row["metadata"]
        if isinstance(meta, str):
            meta = json.loads(meta)
        schedule_time_str: str = meta.get("schedule_time", "06:00")
        try:
            sched_h, sched_m = map(int, schedule_time_str.split(":"))
        except ValueError:
            sched_h, sched_m = 6, 0
        scheduled_time_today = now_local.replace(
            hour=sched_h, minute=sched_m, second=0, microsecond=0)
        if now_local < scheduled_time_today:
            continue

        # Inactivity check
        if _is_inactive(row, today_local, tz):
            logger.info("Auto-kick user_id=%d challenge=%s", user_id, row["slug"])
            await db.set_participant_inactive(user_id, challenge_id)
            continue

        # Build and send question
        user_language = row.get("lang") or "ru"
        challenge_mock = {
            "id": challenge_id, "slug": row["slug"],
            "kind": row["kind"], "metadata": row["metadata"],
        }
        try:
            text, markup = build_question_message(challenge_mock, lang=user_language)
            send_kw: dict = {
                "chat_id": row["telegram_id"], "text": text, "parse_mode": "Markdown"
            }
            if markup:
                send_kw["reply_markup"] = markup
            await bot.send_message(**send_kw)
        except Exception as exc:
            logger.warning("Failed send %s → %d: %s", row["slug"], row["telegram_id"], exc)
            continue

        # Update dispatch metadata
        next_ts = db.next_dispatch_ts(schedule_time_str, tz_str)
        await db.update_after_dispatch(user_id, challenge_id, today_local, next_ts)
        logger.debug("Dispatched %s → user_id=%d", row["slug"], user_id)

        # FSM state for count-kind
        if row["kind"] == "count":
            await _set_count_state(bot, storage, row["telegram_id"], challenge_id)


async def _set_count_state(
    bot: Bot, storage: BaseStorage, telegram_id: int, challenge_id: int
) -> None:
    key = StorageKey(bot_id=bot.id, chat_id=telegram_id, user_id=telegram_id)
    await storage.set_state(key=key, state=CountAnswerState.waiting_for_count)
    await storage.set_data(key=key, data={"active_count_challenge_id": challenge_id})


def _is_inactive(row, today_local: date, tz) -> bool:
    cutoff: date = today_local - timedelta(days=INACTIVITY_DAYS - 1)
    joined_local: date = row["cp_joined_at"].astimezone(tz).date()
    if joined_local >= cutoff:
        return False
    last_answer: date | None = row["last_answer_day"]
    return last_answer is None or last_answer < cutoff


# ─── Announcer ─────────────────────────────────────────────────────────────

async def _run_announcer(bot: Bot) -> None:
    """Send challenge announcement to all users for every unannounced challenge."""
    challenges = await db.get_unannounced_challenges()
    if not challenges:
        return

    # Fetch all users once
    from adapters.storage_postgres import fetch as _fetch
    all_users = await _fetch("SELECT telegram_id, lang FROM users ORDER BY id")

    if not all_users:
        # No registered users yet — skip but don't mark announced,
        # so we retry on next tick when users arrive.
        logger.info("Announcer: no users yet, will retry next tick")
        return

    for challenge in challenges:
        meta = challenge["metadata"]
        if isinstance(meta, str):
            meta = json.loads(meta)

        slug          = challenge["slug"]
        kind          = challenge["kind"]
        schedule_time = meta.get("schedule_time", "?")
        duration      = meta.get("duration_days", "?")
        translations  = meta.get("translations", {})

        sent   = 0
        failed = 0

        for user in all_users:
            lang = (user.get("lang") or "ru") if hasattr(user, "get") else "ru"
            lang = lang if lang in SUPPORTED_LANGS else "ru"

            # challenge_text() returns (title, question); get description separately
            title, _ = challenge_text(challenge, lang)
            tr_block  = translations.get(lang) or translations.get("ru") or {}
            description = tr_block.get("description") or "—"

            text = t(
                "challenge_announce", lang,
                title=title,
                description=description,
                kind=kind_label(kind, lang),
                time=schedule_time,
                days=duration,
            )
            kb = challenge_announce_kb(challenge["id"], lang)
            try:
                await bot.send_message(
                    chat_id=user["telegram_id"],
                    text=text,
                    reply_markup=kb,
                    parse_mode="Markdown",
                )
                sent += 1
            except Exception as exc:
                logger.warning("Announce %s → %d: %s", slug, user["telegram_id"], exc)
                failed += 1
            await asyncio.sleep(ANNOUNCE_RATE)

        await db.mark_challenge_announced(challenge["id"])
        logger.info("Announced '%s': %d sent, %d failed", slug, sent, failed)
