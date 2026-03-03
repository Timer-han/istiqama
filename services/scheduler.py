"""services/scheduler.py – daily question sender + challenge announcements."""
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
from bot.i18n import t, kind_label, SUPPORTED_LANGS
from bot.keyboards import challenge_announce_kb
from bot.states import CountAnswerState
from bot.utils import challenge_text

logger = logging.getLogger(__name__)

INACTIVITY_DAYS = 3
ANNOUNCE_RATE   = 0.05


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
                await db.ensure_event_partitions(months_ahead=3)
                _last_partition_check = today
                logger.info("Partition check done for %s", today)

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

    # ── Phase 1: фильтрация, группировка по user → batches ─────────────────
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

        # schedule_time ещё не наступило
        try:
            sh, sm = map(int, schedule_time_str.split(":"))
        except ValueError:
            sh, sm = 6, 0
        if now_local < now_local.replace(hour=sh, minute=sm, second=0, microsecond=0):
            continue

        # Инактивность → авто-кик
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

    # ── Phase 2: добавить в очередь + обновить next_dispatch_at ─────────────
    #
    # ВАЖНО: next_dispatch_at обновляется здесь, ДО отправки.
    # Это гарантирует, что следующий тик шедулера не подберёт
    # того же пользователя, даже если Phase 3 выбросит исключение.

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

    # ── Phase 3: отправить первый вопрос батча (если нет неотвеченного) ──────

    for user_id, udata in users.items():
        today = udata["today"]

        for schedule_time in udata["batches"]:
            # Есть отправленный-но-неотвеченный → ждём ответа
            if await db.has_unanswered_in_batch(user_id, today, schedule_time):
                logger.debug(
                    "user_id=%d batch=%s: unanswered question pending, skipping",
                    user_id, schedule_time,
                )
                continue

            next_item = await db.get_next_unsent(user_id, today, schedule_time)
            if not next_item:
                logger.debug(
                    "user_id=%d batch=%s: no unsent items left",
                    user_id, schedule_time,
                )
                continue

            await _send_queue_item(bot, storage, udata, next_item, today)


async def _send_queue_item(
    bot: Bot,
    storage: BaseStorage,
    udata: dict,
    item,
    today: date,
) -> bool:
    """
    Отправить вопрос из очереди.
    Возвращает True при успехе.

    Порядок операций:
      1. Отправить сообщение
      2. Пометить sent_at (ТОЛЬКО если отправка успешна)
      3. Обновить last_dispatch_day
      4. Для count — поставить FSM
    """
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

    # Только после успешной отправки — обновляем БД
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
    cutoff       = today_local - timedelta(days=INACTIVITY_DAYS - 1)
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
            await asyncio.sleep(ANNOUNCE_RATE)

        await db.mark_challenge_announced(challenge["id"])
        logger.info("Announced '%s': %d sent, %d failed", slug, sent, failed)