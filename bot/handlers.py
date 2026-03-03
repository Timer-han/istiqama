"""bot/handlers.py – user-facing handlers."""
from __future__ import annotations

import json
import logging
from datetime import date

from aiogram import Router, F, Bot
from aiogram.filters import CommandStart, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

import services.db as db
from bot.config import config
from bot.filters import ButtonText
from bot.i18n import t, user_lang as _user_lang, LANG_LABELS
from bot.keyboards import (
    user_main_kb,
    admin_main_kb,
    settings_kb,
    lang_select_kb,
    yes_no_kb,
    scale_1_5_kb,
    poll_kb,
    challenges_list_kb,
)
from bot.states import CountAnswerState
from bot.utils import challenge_text, challenge_options, tz_from_coords

logger = logging.getLogger(__name__)
router = Router()

DEFAULT_TIMEZONE = "Europe/Moscow"


def _main_kb(telegram_id: int, lang: str):
    return admin_main_kb(lang) if telegram_id in config.admin_ids else user_main_kb(lang)


# ─── /start ───────────────────────────────────────────────────────────────

@router.message(CommandStart())
async def cmd_start(msg: Message, state: FSMContext):
    await state.clear()
    tg   = msg.from_user
    user = await db.get_or_create_user(
        telegram_id=tg.id,
        username=tg.username,
        display_name=tg.full_name,
        tz=DEFAULT_TIMEZONE,
    )
    lang = _user_lang(user)
    await msg.answer(t("welcome", lang, name=user["display_name"]),
                     reply_markup=_main_kb(tg.id, lang))


# ─── Statistics ────────────────────────────────────────────────────────────

@router.message(ButtonText("btn_stats"))
async def my_stats(msg: Message, db_user=None, user_lang: str = "ru"):
    if not db_user:
        await msg.answer(t("start_first"))
        return

    participations = await db.fetch(
        """
        SELECT cp.challenge_id, c.slug, c.kind, c.metadata
        FROM challenge_participants cp
        JOIN challenges c ON c.id = cp.challenge_id
        WHERE cp.user_id = $1 AND cp.active = TRUE
        ORDER BY c.id
        """,
        db_user["id"],
    )

    if not participations:
        await msg.answer(t("stats_no_active", user_lang))
        return

    blocks = [t("stats_detail_header", user_lang)]
    for p in participations:
        title, _ = challenge_text(p, user_lang)
        stats    = await db.get_user_challenge_stats(db_user["id"], p["challenge_id"])
        block    = _fmt_user_stats(p["kind"], title, stats, p, user_lang)
        blocks.append(block)

    await msg.answer("\n\n".join(blocks), parse_mode="Markdown")


def _fmt_user_stats(kind: str, title: str, stats: dict, challenge, lang: str) -> str:
    if stats.get("total_days", 0) == 0:
        return f"*{title}*\n{t('stats_no_answers_yet', lang)}"
    if kind == "yes_no":
        return _fmt_yesno(title, stats, lang)
    elif kind == "count":
        return _fmt_count(title, stats, lang)
    elif kind == "scale_1_5":
        return _fmt_scale(title, stats, lang)
    elif kind == "poll":
        return _fmt_poll(title, stats, challenge, lang)
    return f"*{title}*"


def _fmt_yesno(title: str, s: dict, lang: str) -> str:
    total   = s["total_days"]
    yes_all = s.get("yes_count", 0)
    pct_all = round(yes_all / total * 100) if total else 0
    return t("stats_yesno_block", lang,
             title=title,
             yes_7=s.get("yes_7", 0), days_7=s.get("days_7", 0),
             yes_all=yes_all, total_days=total, pct_all=pct_all,
             cur_streak=s.get("current_streak", 0),
             max_streak=s.get("max_streak", 0))


def _fmt_count(title: str, s: dict, lang: str) -> str:
    vals_7  = [v for _, v in s.get("last_7_values", [])]
    return t("stats_count_block", lang,
             title=title,
             avg_7=s.get("avg_7") or "—", sum_7=sum(vals_7) if vals_7 else 0,
             avg_all=s.get("avg_all") or "—",
             sum_all=s.get("sum_all", 0),
             max_val=s.get("max_val") or "—",
             total_days=s.get("total_days", 0))


def _fmt_scale(title: str, s: dict, lang: str) -> str:
    dist = s.get("distribution", {})
    bar_parts = [f"{i}★×{dist[i]}" for i in range(1, 6) if dist.get(i, 0)]
    return t("stats_scale_block", lang,
             title=title,
             avg_7=s.get("avg_7") or "—",
             avg_all=s.get("avg_all") or "—",
             max_val=s.get("max_val") or "—",
             dist_str="  ".join(bar_parts) or "—",
             total_days=s.get("total_days", 0))


def _fmt_poll(title: str, s: dict, challenge, lang: str) -> str:
    total   = s.get("total_answers", 0)
    dist    = s.get("distribution", {})
    options = challenge_options({"metadata": challenge["metadata"]}, lang)
    lines   = []
    for idx_str, cnt in sorted(dist.items(), key=lambda x: -x[1]):
        try:
            label = options[int(idx_str)] if int(idx_str) < len(options) else f"#{idx_str}"
        except (ValueError, IndexError):
            label = idx_str
        pct = round(cnt / total * 100) if total else 0
        lines.append(f"  • {label}: {cnt}× ({pct}%)")
    return t("stats_poll_block", lang,
             title=title, total=total,
             dist_str="\n".join(lines) if lines else "—")


# ─── Challenges ────────────────────────────────────────────────────────────

@router.message(ButtonText("btn_challenges"))
async def list_challenges(msg: Message, db_user=None, user_lang: str = "ru"):
    if not db_user:
        await msg.answer(t("start_first"))
        return
    challenges = await db.get_user_challenges(db_user["id"])
    if not challenges:
        await msg.answer(t("no_challenges", user_lang))
        return
    participating = {c["id"] for c in challenges if c["participating"]}
    lines = [t("challenges_header", user_lang)]
    for c in challenges:
        title, _ = challenge_text(c, user_lang)
        status   = "✅" if c["id"] in participating else "➕"
        lines.append(f"{status} *{title}*")
    await msg.answer("\n".join(lines),
                     reply_markup=challenges_list_kb(challenges, participating, lang=user_lang),
                     parse_mode="Markdown")


@router.callback_query(F.data.startswith("challenge:"))
async def handle_challenge_action(cb: CallbackQuery, db_user=None, user_lang: str = "ru"):
    _, action, challenge_id_str = cb.data.split(":", 2)
    challenge_id = int(challenge_id_str)
    if not db_user:
        await cb.answer(t("start_first"), show_alert=True)
        return
    if action == "join":
        joined = await db.join_challenge(db_user["id"], challenge_id, db_user["timezone"])
        await cb.answer(t("joined_challenge", user_lang) if joined
                        else t("already_participating", user_lang))
    elif action == "leave":
        await db.leave_challenge(db_user["id"], challenge_id)
        await cb.answer(t("left_challenge", user_lang))
    challenges    = await db.get_user_challenges(db_user["id"])
    participating = {c["id"] for c in challenges if c["participating"]}
    await cb.message.edit_reply_markup(
        reply_markup=challenges_list_kb(challenges, participating, lang=user_lang))


# ─── Settings ─────────────────────────────────────────────────────────────

@router.message(ButtonText("btn_settings"))
async def settings(msg: Message, db_user=None, user_lang: str = "ru"):
    tz = db_user["timezone"] if db_user else DEFAULT_TIMEZONE
    await msg.answer(
        t("settings_header", user_lang, tz=tz, lang_label=LANG_LABELS[user_lang]),
        parse_mode="Markdown",
        reply_markup=settings_kb(user_lang),
    )


@router.message(ButtonText("btn_back"))
async def settings_back(msg: Message, state: FSMContext, db_user=None, user_lang: str = "ru"):
    await state.clear()
    lang = _user_lang(db_user)
    await msg.answer(t("main_menu_prompt", lang),
                     reply_markup=_main_kb(msg.from_user.id, lang))


@router.message(ButtonText("btn_change_lang"))
async def change_lang_menu(msg: Message, user_lang: str = "ru"):
    await msg.answer(t("lang_select", user_lang), reply_markup=lang_select_kb())


@router.callback_query(F.data.startswith("set_lang:"))
async def set_lang(cb: CallbackQuery, db_user=None):
    lang_code = cb.data.split(":")[1]
    if not db_user:
        await cb.answer(t("start_first"), show_alert=True)
        return
    await db.update_user_lang(db_user["id"], lang_code)
    label = LANG_LABELS.get(lang_code, lang_code)
    await cb.answer(t("lang_set", lang_code, lang_label=label))
    await cb.message.edit_text(t("lang_set", lang_code, lang_label=label))


@router.message(F.text.startswith("/timezone "))
async def set_timezone(msg: Message, db_user=None, user_lang: str = "ru"):
    tz_str = msg.text.split(" ", 1)[1].strip()
    try:
        import pytz; pytz.timezone(tz_str)
    except Exception:
        await msg.answer(t("tz_invalid", user_lang), parse_mode="Markdown")
        return
    if not db_user:
        await msg.answer(t("start_first"))
        return
    await db.update_user_timezone(db_user["id"], tz_str)
    await msg.answer(t("tz_updated", user_lang, tz=tz_str), parse_mode="Markdown")


@router.message(F.location)
async def handle_location(msg: Message, db_user=None, user_lang: str = "ru"):
    if not db_user:
        await msg.answer(t("start_first"))
        return
    lat    = msg.location.latitude
    lon    = msg.location.longitude
    tz_str = tz_from_coords(lat, lon) or DEFAULT_TIMEZONE
    await db.update_user_location(user_id=db_user["id"], lat=lat, lon=lon, tz=tz_str)
    await db.refresh_dispatch_times_for_user(db_user["id"], tz_str)
    await msg.answer(t("location_received", user_lang, tz=tz_str),
                     parse_mode="Markdown",
                     reply_markup=_main_kb(msg.from_user.id, user_lang))


# ─── Inline answers (yes_no / scale / poll) ───────────────────────────────

@router.callback_query(F.data.startswith("ans:"))
async def handle_answer(
    cb: CallbackQuery,
    bot: Bot,
    state: FSMContext,
    db_user=None,
    user_lang: str = "ru",
):
    parts        = cb.data.split(":")
    challenge_id = int(parts[1])
    value        = parts[2]
    if not db_user:
        await cb.answer(t("start_first"), show_alert=True)
        return
    challenge = await db.get_challenge_by_id(challenge_id)
    if not challenge:
        await cb.answer(t("challenge_not_found", user_lang), show_alert=True)
        return

    try:
        payload_value: str | int = int(value)
    except ValueError:
        payload_value = value

    today = db.local_day_for_tz(db_user["timezone"])
    event = await db.record_event(
        user_id=db_user["id"], challenge_id=challenge_id,
        tz_str=db_user["timezone"], payload={"value": payload_value},
    )
    if event is None:
        await cb.answer(t("already_answered", user_lang), show_alert=True)
        return

    title, _ = challenge_text(challenge, user_lang)
    await cb.answer(t("answer_toast", user_lang))
    await cb.message.edit_text(
        t("answer_recorded", user_lang, value=value, title=title),
        parse_mode="Markdown")

    # Пометить в очереди как отвеченный → разблокировать следующий вопрос
    await db.mark_queue_answered(db_user["id"], challenge_id, today)
    await _maybe_send_next(bot, state, db_user, challenge_id, today, user_lang)


# ─── Count input — stateful FSM ───────────────────────────────────────────

@router.message(StateFilter(CountAnswerState.waiting_for_count), F.text.regexp(r"^\d+$"))
async def handle_count_input(
    msg: Message,
    bot: Bot,
    state: FSMContext,
    db_user=None,
    user_lang: str = "ru",
):
    data         = await state.get_data()
    challenge_id = data.get("active_count_challenge_id")
    if not challenge_id or not db_user:
        await state.clear()
        return

    count = int(msg.text)
    today = db.local_day_for_tz(db_user["timezone"])
    event = await db.record_event(
        user_id=db_user["id"], challenge_id=challenge_id,
        tz_str=db_user["timezone"], payload={"value": count},
    )
    await state.clear()
    if event is None:
        await msg.answer(t("count_already_answered", user_lang))
        return

    challenge = await db.get_challenge_by_id(challenge_id)
    title, _  = challenge_text(challenge, user_lang)
    await msg.answer(t("count_recorded", user_lang, count=count, title=title),
                     parse_mode="Markdown")

    await db.mark_queue_answered(db_user["id"], challenge_id, today)
    await _maybe_send_next(bot, state, db_user, challenge_id, today, user_lang)


@router.message(StateFilter(None), F.text.regexp(r"^\d+$"))
async def handle_count_no_context(
    msg: Message,
    bot: Bot,
    state: FSMContext,
    db_user=None,
    user_lang: str = "ru",
):
    if not db_user:
        return
    pending = await db.get_pending_count_challenges(db_user["id"], db_user["timezone"])
    if not pending:
        return

    if len(pending) == 1:
        cid   = pending[0]["challenge_id"]
        count = int(msg.text)
        today = db.local_day_for_tz(db_user["timezone"])
        event = await db.record_event(
            user_id=db_user["id"], challenge_id=cid,
            tz_str=db_user["timezone"], payload={"value": count},
        )
        if event is None:
            await msg.answer(t("count_already_answered", user_lang))
            return
        challenge = await db.get_challenge_by_id(cid)
        title, _  = challenge_text(challenge, user_lang)
        await msg.answer(t("count_recorded", user_lang, count=count, title=title),
                         parse_mode="Markdown")
        await db.mark_queue_answered(db_user["id"], cid, today)
        await _maybe_send_next(bot, state, db_user, cid, today, user_lang)
    else:
        names = "\n".join(f"• {r['slug']}" for r in pending)
        await msg.answer(t("count_multiple_pending", user_lang, list=names))


# ─── Отправить следующий вопрос в цепочке ─────────────────────────────────

async def _maybe_send_next(
    bot: Bot,
    state: FSMContext,
    db_user,
    answered_challenge_id: int,
    today: date,
    user_lang: str,
) -> None:
    """
    После ответа на answered_challenge_id:
    - Проверить, есть ли следующий НЕОТПРАВЛЕННЫЙ вопрос в том же батче.
    - Если есть — отправить и пометить sent_at.
    - Если нет — ничего не делать.
    - Не запускать для ответов за прошлые дни (get_next_after_answer проверяет сам).
    """
    next_item = await db.get_next_after_answer(
        db_user["id"], answered_challenge_id, today
    )
    if not next_item:
        return

    challenge_mock = {
        "id":       next_item["challenge_id"],
        "slug":     next_item["slug"],
        "kind":     next_item["kind"],
        "metadata": next_item["metadata"],
    }
    text, markup = build_question_message(challenge_mock, lang=user_lang)
    send_kw: dict = {
        "chat_id": db_user["telegram_id"],
        "text": text,
        "parse_mode": "Markdown",
    }
    if markup:
        send_kw["reply_markup"] = markup

    try:
        await bot.send_message(**send_kw)
    except Exception as exc:
        logger.warning("Failed to send next queued question: %s", exc)
        return

    await db.mark_queue_sent(next_item["queue_id"])
    await db.mark_last_dispatch_day(db_user["id"], next_item["challenge_id"], today)
    logger.info(
        "Chain: sent %s → user_id=%d after answer to challenge_id=%d",
        next_item["slug"], db_user["id"], answered_challenge_id,
    )

    if next_item["kind"] == "count":
        await state.set_state(CountAnswerState.waiting_for_count)
        await state.set_data({"active_count_challenge_id": next_item["challenge_id"]})
    else:
        await state.clear()


# ─── build_question_message ───────────────────────────────────────────────

def build_question_message(challenge: dict, lang: str = "ru") -> tuple[str, object | None]:
    title, question = challenge_text(challenge, lang)
    kind   = challenge["kind"]
    cid    = challenge["id"]
    text   = f"🕌 *{title}*\n\n{question}"
    markup = None
    if kind == "yes_no":
        markup = yes_no_kb(cid, lang)
    elif kind == "scale_1_5":
        markup = scale_1_5_kb(cid)
    elif kind == "poll":
        options = challenge_options(challenge, lang)
        if options:
            markup = poll_kb(cid, options)
    elif kind == "count":
        text += t("count_prompt", lang)
    return text, markup