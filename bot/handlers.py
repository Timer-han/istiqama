"""bot/handlers.py – user-facing handlers (fully i18n-aware)."""
from __future__ import annotations

import json
import logging

from aiogram import Router, F
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
    rows = await db.get_user_stats_days(db_user["id"], days=7)
    if not rows:
        await msg.answer(t("stats_empty", user_lang))
        return
    lines = [t("stats_header", user_lang)]
    for r in rows:
        meta = r["metadata"]
        if isinstance(meta, str):
            meta = json.loads(meta)
        tr    = meta.get("translations", {})
        title = (tr.get(user_lang) or tr.get("ru", {})).get("title", r["slug"])
        payload = r["payload"]
        if isinstance(payload, str):
            payload = json.loads(payload)
        val = payload.get("value", "—")
        lines.append(t("stats_row", user_lang, day=r["local_day"], title=title, val=val))
    await msg.answer("\n".join(lines), parse_mode="Markdown")


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
                     reply_markup=challenges_list_kb(challenges, participating),
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
        reply_markup=challenges_list_kb(challenges, participating))


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


# ─── /timezone ────────────────────────────────────────────────────────────

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


# ─── Location ─────────────────────────────────────────────────────────────

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
async def handle_answer(cb: CallbackQuery, db_user=None, user_lang: str = "ru"):
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
    payload_value: str | int = value
    try:
        payload_value = int(value)
    except ValueError:
        pass
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


# ─── Count input — stateful FSM ───────────────────────────────────────────

@router.message(StateFilter(CountAnswerState.waiting_for_count), F.text.regexp(r"^\d+$"))
async def handle_count_input(msg: Message, state: FSMContext, db_user=None, user_lang: str = "ru"):
    data         = await state.get_data()
    challenge_id = data.get("active_count_challenge_id")
    if not challenge_id or not db_user:
        await state.clear()
        return
    count = int(msg.text)
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


@router.message(StateFilter(None), F.text.regexp(r"^\d+$"))
async def handle_count_no_context(msg: Message, db_user=None, user_lang: str = "ru"):
    if not db_user:
        return
    pending = await db.get_pending_count_challenges(db_user["id"], db_user["timezone"])
    if not pending:
        return
    if len(pending) == 1:
        cid   = pending[0]["challenge_id"]
        count = int(msg.text)
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
    else:
        names = "\n".join(f"• {r['slug']}" for r in pending)
        await msg.answer(t("count_multiple_pending", user_lang, list=names))


# ─── build_question_message — used by scheduler ───────────────────────────

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
