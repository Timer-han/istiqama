"""services/scheduler.py – daily question sender + challenge announcements + motivation broadcast."""
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
from bot.i18n import t, kind_label, SUPPORTED_LANGS, get_daily_motivation
from bot.keyboards import challenge_announce_kb
from bot.states import CountAnswerState
from bot.utils import challenge_text
from constants import (
    SCHEDULER_INACTIVITY_DAYS,
    SCHEDULER_ANNOUNCE_RATE,
    DB_PARTITION_MONTHS_AHEAD,
    DB_DUE_PARTICIPANTS_LIMIT,
)

logger = logging.getLogger(__name__)

# Seconds between motivation messages to stay under Telegram rate limits
_MOTIVATION_RATE = 0.05


async def scheduler_task(
    bot: Bot,
    storage: BaseStorage,
    interval: int = 60,
) -> None:
    logger.info("Scheduler started (interval=%ds)", interval)
    _last_partition_check: date | None = None

    while True:
        try:
            today = date.today()
            if _last_partition_check != today:
                await db.ensure_event_partitions(months_ahead=DB_PARTITION_MONTHS_AHEAD)
                _last_partition_check = today
                logger.info("Partition check done for %s", today)

            await _run_dispatcher(bot, storage)
            await _run_announcer(bot)
        except Exception:
            logger.exception("Scheduler error")
        await asyncio.sleep(interval)


async def daily_motivation_task(bot: Bot) -> None:
    """Runs every minute; sends motivation broadcast when configured time arrives."""
    logger.info("Daily motivation task started")
    while True:
        try:
            await _check_and_send_motivation(bot)
        except Exception:
            logger.exception("Daily motivation error")
        await asyncio.sleep(60)


async def _check_and_send_motivation(bot: Bot) -> None:
    settings = await db.get_motivation_settings()
    if not settings.get("enabled"):
        return

    send_time = settings.get("send_time", "08:00")
    try:
        h, m = map(int, send_time.split(":"))
    except Exception:
        return

    now_utc = datetime.now(pytz.UTC)
    today_str = now_utc.date().isoformat()

    # Already sent today?
    if settings.get("last_sent_date") == today_str:
        return

    # Is it the right minute?
    if now_utc.hour != h or now_utc.minute != m:
        return

    await _send_daily_motivation(bot)

    settings["last_sent_date"] = today_str
    await db.save_motivation_settings(settings)


async def send_motivation_now(bot: Bot) -> tuple[int, int]:
    """Force-send the motivation broadcast immediately. Returns (sent, failed)."""
    return await _send_daily_motivation(bot)


async def _send_daily_motivation(bot: Bot) -> tuple[int, int]:
    """Send daily motivation message to all users. Returns (sent, failed)."""
    users = await db.get_all_users_with_lang()
    if not users:
        return 0, 0

    active_count = await db.get_total_active_participants()
    sent = failed = 0

    for user in users:
        lang = (user.get("lang") or "ru") if hasattr(user, "get") else "ru"
        lang = lang if lang in SUPPORTED_LANGS else "ru"

        message = get_daily_motivation(lang)
        text = t("motivation_broadcast", lang, count=active_count, message=message)

        try:
            await bot.send_message(
                chat_id=user["telegram_id"],
                text=text,
                parse_mode="Markdown",
            )
            sent += 1
        except Exception as exc:
            logger.debug("Motivation → %d: %s", user["telegram_id"], exc)
            failed += 1
        await asyncio.sleep(_MOTIVATION_RATE)

    logger.info("Motivation broadcast: %d sent, %d failed", sent, failed)
    return sent, failed


# ─── Dispatcher ────────────────────────────────────────────────────────────

async def _run_dispatcher(bot: Bot, storage: BaseStorage) -> None:
    expired = await db.deactivate_expired_challenges()
    if expired:
        logger.info("Deactivated %d expired challenge(s)", expired)

    rows = await db.get_due_participants(limit=DB_DUE_PARTICIPANTS_LIMIT)
    if not rows:
        return

    logger.debug("Dispatcher: %d rows due", len(rows))

    users: dict[int, dict] = {}

    for row in rows:
        user_id = row["user_id"]
        tz_str  = row["timezone"] or "UTC"
        try:
            tz = pytz.timezone(tz_str)
        except Exception:
            tz = pytz.UTC

        now_local   = datetime.now(tz)
        today_local = now_local.date()

        meta = row["metadata"]
        if isinstance(meta, str):
            meta = json.loads(meta)
        schedule_time_str = meta.get("schedule_time", "06:00")

        try:
            sh, sm = map(int, schedule_time_str.split(":"))
        except ValueError:
            sh, sm = 6, 0
        if now_local < now_local.replace(hour=sh, minute=sm, second=0, microsecond=0):
            continue

        if _is_inactive(row, today_local, tz):
            logger.info("Auto-kick user_id=%d challenge=%s", user_id, row["slug"])
            await db.set_participant_inactive(user_id, row["challenge_id"])
            continue

        if user_id not in users:
            users[user_id] = {
                "user_id":     user_id,
                "telegram_id": row["telegram_id"],
                "lang":        row["lang"] or "ru",
                "tz_str":      tz_str,
                "today":       today_local,
                "batches":     {},
            }
        users[user_id]["batches"].setdefault(schedule_time_str, []).append(row)

    if not users:
        return

    for user_id, udata in users.items():
        today  = udata["today"]
        tz_str = udata["tz_str"]

        await db.clear_stale_queue(user_id, today)

        for schedule_time, batch_rows in udata["batches"].items():
            batch_rows.sort(key=lambda r: r["challenge_id"])
            next_ts = db.next_dispatch_ts(schedule_time, tz_str)

            for position, row in enumerate(batch_rows, start=1):
                await db.enqueue_question(
                    user_id          = user_id,
                    challenge_id     = row["challenge_id"],
                    day              = today,
                    schedule_time    = schedule_time,
                    position         = position,
                    next_dispatch_ts = next_ts,
                )

    for user_id, udata in users.items():
        today = udata["today"]

        if await db.has_any_unanswered_today(user_id, today):
            logger.debug("user_id=%d: unanswered question pending, skipping", user_id)
            continue

        sent_one = False
        for schedule_time in sorted(udata["batches"]):
            if sent_one:
                break
            next_item = await db.get_next_unsent(user_id, today, schedule_time)
            if not next_item:
                continue
            await _send_queue_item(bot, storage, udata, next_item, today)
            sent_one = True


async def _send_queue_item(
    bot: Bot,
    storage: BaseStorage,
    udata: dict,
    item,
    today: date,
) -> bool:
    user_id     = udata["user_id"]
    telegram_id = udata["telegram_id"]
    lang        = udata["lang"]

    challenge_mock = {
        "id":       item["challenge_id"],
        "slug":     item["slug"],
        "kind":     item["kind"],
        "metadata": item["metadata"],
    }
    text, markup = build_question_message(challenge_mock, lang=lang)
    send_kw: dict = {"chat_id": telegram_id, "text": text, "parse_mode": "Markdown"}
    if markup:
        send_kw["reply_markup"] = markup

    try:
        await bot.send_message(**send_kw)
    except Exception as exc:
        logger.warning("Failed send %s → %d: %s", item["slug"], telegram_id, exc)
        return False

    await db.mark_queue_sent(item["queue_id"])
    await db.mark_last_dispatch_day(user_id, item["challenge_id"], today)
    logger.info("Sent %s → user_id=%d", item["slug"], user_id)

    if item["kind"] == "count":
        await _set_count_state(bot, storage, telegram_id, item["challenge_id"])

    return True


async def _set_count_state(
    bot: Bot, storage: BaseStorage, telegram_id: int, challenge_id: int
) -> None:
    key = StorageKey(bot_id=bot.id, chat_id=telegram_id, user_id=telegram_id)
    await storage.set_state(key=key, state=CountAnswerState.waiting_for_count)
    await storage.set_data(key=key, data={"active_count_challenge_id": challenge_id})


def _is_inactive(row, today_local: date, tz) -> bool:
    cutoff       = today_local - timedelta(days=SCHEDULER_INACTIVITY_DAYS - 1)
    joined_local = row["cp_joined_at"].astimezone(tz).date()
    if joined_local >= cutoff:
        return False
    last_answer: date | None = row["last_answer_day"]
    return last_answer is None or last_answer < cutoff


# ─── Announcer ─────────────────────────────────────────────────────────────

async def _run_announcer(bot: Bot) -> None:
    challenges = await db.get_unannounced_challenges()
    if not challenges:
        return

    from adapters.storage_postgres import fetch as _fetch
    all_users = await _fetch("SELECT telegram_id, lang FROM users ORDER BY id")

    if not all_users:
        logger.info("Announcer: no users yet, retrying next tick")
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
        sent = failed = 0

        for user in all_users:
            lang = (user.get("lang") or "ru") if hasattr(user, "get") else "ru"
            lang = lang if lang in SUPPORTED_LANGS else "ru"

            title, _    = challenge_text(challenge, lang)
            tr_block    = translations.get(lang) or translations.get("ru") or {}
            description = tr_block.get("description") or "—"

            text = t("challenge_announce", lang,
                     title=title, description=description,
                     kind=kind_label(kind, lang),
                     time=schedule_time, days=duration)
            kb = challenge_announce_kb(challenge["id"], lang)
            try:
                await bot.send_message(
                    chat_id=user["telegram_id"],
                    text=text, reply_markup=kb, parse_mode="Markdown",
                )
                sent += 1
            except Exception as exc:
                logger.warning("Announce %s → %d: %s", slug, user["telegram_id"], exc)
                failed += 1
            await asyncio.sleep(SCHEDULER_ANNOUNCE_RATE)

        await db.mark_challenge_announced(challenge["id"])
        logger.info("Announced '%s': %d sent, %d failed", slug, sent, failed)