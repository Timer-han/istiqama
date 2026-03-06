"""bot/admin_handlers.py – admin panel (fully i18n-aware)."""
from __future__ import annotations

import json
import logging
import re
from datetime import datetime, timezone

import pytz
from aiogram import Router, F
from aiogram.filters import Filter, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

import services.db as db
from bot.config import config
from bot.i18n import t, user_lang as _user_lang, LANG_LABELS, kind_label

from bot.keyboards import (
    admin_panel_kb,
    admin_challenges_list_kb,
    admin_challenge_mgmt_kb,
    admin_translation_lang_kb,
    back_to_panel_kb,
    cancel_kb,
    confirm_create_kb,
    edit_field_kb,
    launch_time_kb,
)
from bot.states import ChallengeCreateForm, ChallengeTranslateForm, BroadcastForm
from bot.utils import challenge_text

logger = logging.getLogger(__name__)
router = Router()

_SLUG_RE = re.compile(r'^[a-z0-9][a-z0-9\-]{0,46}[a-z0-9]$|^[a-z0-9]$')


# ─── Admin filter ──────────────────────────────────────────────────────────

class IsAdmin(Filter):
    async def __call__(self, event: Message | CallbackQuery) -> bool:
        uid = getattr(event.from_user, "id", None)
        return uid in config.admin_ids

router.message.filter(IsAdmin())
router.callback_query.filter(IsAdmin())


# ─── Helpers ──────────────────────────────────────────────────────────────

def _is_valid_slug(text: str) -> bool:
    try:
        text.encode("ascii")
    except UnicodeEncodeError:
        return False
    return bool(_SLUG_RE.match(text))


def _challenge_card(c, meta: dict, lang: str = "ru") -> str:
    title, question = challenge_text(c, lang)
    tr          = meta.get("translations", {}).get(lang) or meta.get("translations", {}).get("ru", {})
    description = tr.get("description", "") or "—"
    schedule    = meta.get("schedule_time", "?")
    duration    = meta.get("duration_days", "?")
    status_str  = t("adm_ch_status_active", lang) if c["active"] else t("adm_ch_status_inactive", lang)
    launch_at   = meta.get("launch_at")
    launch_str  = f"\nЗапуск: `{launch_at}`" if launch_at else ""
    return (
        f"🧩 *{title}*\n_{description}_\n\n"
        f"Slug: `{c['slug']}`\nТип: `{c['kind']}`\n"
        f"Время: `{schedule}`\nДлительность: {duration} дней\n"
        f"Статус: {status_str}{launch_str}\n\n"
        f"Вопрос: _{question}_"
    )


def _build_review(data: dict, lang: str = "ru") -> str:
    desc     = data.get("description_ru") or "—"
    kl       = kind_label(data.get("kind", ""), lang)
    launch   = data.get("launch_at_display") or t("adm_wiz_review_now", lang)
    options  = data.get("options_ru", [])

    text = t("adm_wiz_review", lang,
             slug=data.get("slug", "?"),
             title=data.get("title_ru", "?"),
             desc=desc, kind=kl,
             question=data.get("question_ru", "?"),
             time=data.get("schedule_time", "?"),
             days=data.get("duration_days", "?"),
             launch=launch)

    if options:
        options_lines = "\n".join(f"  • {o}" for o in options)
        text += f"\n\n{t('adm_wiz_options_preview', lang)}\n{options_lines}"

    return text


async def _show_review(target, state: FSMContext, lang: str = "ru") -> None:
    data = await state.get_data()
    text = _build_review(data, lang)
    kb   = confirm_create_kb(lang)
    if isinstance(target, CallbackQuery):
        await target.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")
        await target.answer()
    else:
        await target.answer(text, reply_markup=kb, parse_mode="Markdown")


# ─── Panel ────────────────────────────────────────────────────────────────

@router.message(F.text.in_({t("btn_admin_panel", lang) for lang in ("ru", "en", "tt")}))
async def admin_panel(msg: Message, user_lang: str = "ru"):
    await msg.answer(t("adm_panel_title", user_lang),
                     reply_markup=admin_panel_kb(user_lang), parse_mode="Markdown")


@router.callback_query(F.data == "adm:panel")
async def adm_panel_cb(cb: CallbackQuery, user_lang: str = "ru"):
    await cb.message.edit_text(t("adm_panel_title", user_lang),
                                reply_markup=admin_panel_kb(user_lang), parse_mode="Markdown")
    await cb.answer()


# ─── Stats ────────────────────────────────────────────────────────────────

@router.callback_query(F.data == "adm:stats")
async def adm_stats(cb: CallbackQuery, user_lang: str = "ru"):
    stats = await db.get_admin_stats()
    header = t("adm_stats_header", user_lang,
                total=stats["total_users"], today=stats["active_today"])
    rows = []
    for c in stats["challenges"]:
        meta = c["metadata"]
        if isinstance(meta, str):
            meta = json.loads(meta)
        tr    = meta.get("translations", {})
        title = (tr.get(user_lang) or tr.get("ru", {})).get("title", c["slug"])
        avg   = f"{c['sum_counts'] / c['responses']:.1f}" if c["responses"] else "0"
        rows.append(t("adm_stats_row", user_lang,
                      title=title, resp=c["responses"], avg=avg, max=c["max_count"]))

    kb = InlineKeyboardBuilder()
    for c in stats["challenges"]:
        meta = c["metadata"]
        if isinstance(meta, str):
            meta = json.loads(meta)
        tr    = meta.get("translations", {})
        title = (tr.get(user_lang) or tr.get("ru", {})).get("title", c["slug"])
        kb.button(
            text=f"🔍 {title}",
            callback_data=f"adm:ch:detail:{c['id']}",
        )
    kb.button(text=t("btn_nav_back", user_lang), callback_data="adm:panel")
    kb.adjust(1)

    await cb.message.edit_text(
        header + "".join(rows),
        reply_markup=kb.as_markup(),
        parse_mode="Markdown",
    )
    await cb.answer()


# ─── Challenge list ────────────────────────────────────────────────────────

@router.callback_query(F.data == "adm:challenges")
async def adm_challenges(cb: CallbackQuery, user_lang: str = "ru"):
    challenges = await db.fetch_all_challenges()
    await cb.message.edit_text(
        t("adm_challenges_title", user_lang),
        reply_markup=admin_challenges_list_kb(challenges, user_lang),
        parse_mode="Markdown",
    )
    await cb.answer()


@router.callback_query(F.data.startswith("adm:ch:view:"))
async def adm_challenge_view(cb: CallbackQuery, user_lang: str = "ru"):
    challenge_id = int(cb.data.split(":")[-1])
    c = await db.get_challenge_by_id(challenge_id)
    if not c:
        await cb.answer(t("adm_ch_not_found", user_lang), show_alert=True)
        return
    meta = c["metadata"]
    if isinstance(meta, str):
        meta = json.loads(meta)
    await cb.message.edit_text(
        _challenge_card(c, meta, user_lang),
        reply_markup=admin_challenge_mgmt_kb(challenge_id, c["active"], user_lang),
        parse_mode="Markdown",
    )
    await cb.answer()


@router.callback_query(F.data.startswith("adm:ch:toggle:"))
async def adm_toggle_challenge(cb: CallbackQuery, user_lang: str = "ru"):
    challenge_id = int(cb.data.split(":")[-1])
    c = await db.get_challenge_by_id(challenge_id)
    if not c:
        await cb.answer(t("adm_ch_not_found", user_lang), show_alert=True)
        return
    new_active = not c["active"]
    await db.toggle_challenge_active(challenge_id, new_active)
    c2   = await db.get_challenge_by_id(challenge_id)
    meta = c2["metadata"]
    if isinstance(meta, str):
        meta = json.loads(meta)
    await cb.message.edit_text(
        _challenge_card(c2, meta, user_lang),
        reply_markup=admin_challenge_mgmt_kb(challenge_id, c2["active"], user_lang),
        parse_mode="Markdown",
    )
    msg = t("adm_ch_toggled_active" if new_active else "adm_ch_toggled_inactive", user_lang)
    await cb.answer(msg)


@router.callback_query(F.data.startswith("adm:ch:delete:"))
async def adm_delete_challenge(cb: CallbackQuery, user_lang: str = "ru"):
    challenge_id = int(cb.data.split(":")[-1])
    await db.delete_challenge(challenge_id)
    challenges = await db.fetch_all_challenges()
    await cb.message.edit_text(
        t("adm_challenges_title", user_lang),
        reply_markup=admin_challenges_list_kb(challenges, user_lang),
        parse_mode="Markdown",
    )
    await cb.answer(t("adm_ch_deleted", user_lang))


@router.callback_query(F.data.startswith("adm:ch:stats:"))
async def adm_challenge_stats(cb: CallbackQuery, user_lang: str = "ru"):
    from datetime import date as _date
    challenge_id = int(cb.data.split(":")[-1])
    today        = _date.today()
    stats        = await db.get_challenge_stats(challenge_id, today)
    c            = await db.get_challenge_by_id(challenge_id)
    title, _     = challenge_text(c, user_lang)
    if stats and stats["total_responses"]:
        avg  = f"{stats['sum_counts'] / stats['total_responses']:.1f}"
        text = t("adm_ch_stats_today", user_lang,
                 title=title, resp=stats["total_responses"],
                 avg=avg, max=stats["max_count"])
    else:
        text = t("adm_ch_stats_empty", user_lang, title=title)
    await cb.message.edit_text(
        text,
        reply_markup=admin_challenge_mgmt_kb(challenge_id, c["active"], user_lang),
        parse_mode="Markdown",
    )
    await cb.answer()


@router.callback_query(F.data.startswith("adm:ch:detail:"))
async def adm_challenge_detail(cb: CallbackQuery, user_lang: str = "ru"):
    challenge_id = int(cb.data.split(":")[-1])
    c = await db.get_challenge_by_id(challenge_id)
    if not c:
        await cb.answer(t("adm_ch_not_found", user_lang), show_alert=True)
        return

    detail = await db.get_admin_challenge_detail(challenge_id)
    lang   = user_lang
    na     = t("adm_na", lang)

    title, _ = challenge_text(c, lang)
    kind     = detail["kind"]

    lines = [t("adm_detail_header", lang, title=title)]

    lines.append(t("adm_detail_participants", lang,
                   active=detail["active_participants"],
                   total=detail["total_participants"],
                   today=detail["answered_today"],
                   rate=detail["response_rate_today"],
                   week=detail["answered_week"]))

    if kind == "yes_no":
        today_pct = detail.get("yes_pct_today")
        week_pct  = detail.get("yes_pct_week")
        lines.append(t("adm_detail_yesno", lang,
                       today_pct=today_pct if today_pct is not None else na,
                       week_pct=week_pct   if week_pct  is not None else na))

    elif kind in ("count", "scale_1_5"):
        lines.append(t("adm_detail_count", lang,
                       avg_today=detail.get("avg_today") or na,
                       avg_week=detail.get("avg_week")   or na,
                       max_ever=detail.get("max_ever")   or na))

    elif kind == "poll":
        dist = detail.get("distribution_week", {})
        if dist:
            meta = c["metadata"]
            if isinstance(meta, str):
                meta = json.loads(meta)
            tr      = meta.get("translations", {})
            options = (tr.get(lang) or tr.get("ru", {})).get("options", [])
            dist_lines = []
            total_poll = sum(dist.values())
            for opt_idx, cnt in sorted(dist.items(), key=lambda x: -x[1]):
                try:
                    label = options[int(opt_idx)] if int(opt_idx) < len(options) else f"#{opt_idx}"
                except (ValueError, IndexError):
                    label = opt_idx
                pct = round(cnt / total_poll * 100) if total_poll else 0
                dist_lines.append(f"  • {label}: {cnt}× ({pct}%)")
            lines.append("📋 За неделю:\n" + "\n".join(dist_lines) + "\n")

    daily = detail.get("daily_7", [])
    if daily:
        lines.append(t("adm_detail_daily_header", lang))
        for row in daily:
            day_str = str(row["day"])
            if kind == "yes_no" and row["yes_pct"] is not None:
                lines.append(t("adm_detail_daily_row_yesno", lang,
                               day=day_str, count=row["count"], yes_pct=row["yes_pct"]))
            elif kind in ("count", "scale_1_5") and row["avg_val"] is not None:
                lines.append(t("adm_detail_daily_row_count", lang,
                               day=day_str, count=row["count"], avg_val=row["avg_val"]))
            else:
                lines.append(t("adm_detail_daily_row_plain", lang,
                               day=day_str, count=row["count"]))

    top = detail.get("top_users", [])
    if top:
        lines.append(t("adm_detail_top_header", lang))
        for i, u in enumerate(top, start=1):
            lines.append(t("adm_detail_top_row", lang,
                           pos=i, name=u["name"],
                           answers=u["total_answers"], avg=u["avg_val"]))

    text = "\n".join(lines)

    from aiogram.utils.keyboard import InlineKeyboardBuilder as _IKB
    kb = _IKB()
    kb.button(text=t("btn_nav_back", lang), callback_data=f"adm:ch:view:{challenge_id}")
    await cb.message.edit_text(text, reply_markup=kb.as_markup(), parse_mode="Markdown")
    await cb.answer()


# ─── Create challenge wizard ───────────────────────────────────────────────

@router.callback_query(F.data == "adm:ch:create")
async def adm_create_start(cb: CallbackQuery, state: FSMContext, user_lang: str = "ru"):
    await state.clear()
    await state.set_state(ChallengeCreateForm.slug)
    await state.update_data(wizard_lang=user_lang)
    await cb.message.edit_text(
        t("adm_wiz_start", user_lang),
        reply_markup=cancel_kb(user_lang), parse_mode="Markdown",
    )
    await cb.answer()


async def _wlang(state: FSMContext, fallback: str = "ru") -> str:
    d = await state.get_data()
    return d.get("wizard_lang", fallback)


# Step 1 – slug
@router.message(ChallengeCreateForm.slug)
async def create_slug(msg: Message, state: FSMContext, user_lang: str = "ru"):
    lang = await _wlang(state, user_lang)
    raw  = msg.text.strip().lower()
    if not _is_valid_slug(raw):
        await msg.answer(t("adm_wiz_slug_invalid", lang), parse_mode="Markdown")
        return
    data         = await state.get_data()
    editing_slug = data.get("slug")
    if editing_slug != raw:
        if await db.get_challenge_by_slug(raw):
            await msg.answer(t("adm_wiz_slug_taken", lang))
            return
    await state.update_data(slug=raw)
    if data.get("edit_mode"):
        await state.update_data(edit_mode=False)
        await _show_review(msg, state, lang)
        return
    await state.set_state(ChallengeCreateForm.title_ru)
    await msg.answer(t("adm_wiz_title", lang, slug=raw),
                     reply_markup=cancel_kb(lang), parse_mode="Markdown")


# Step 2 – title
@router.message(ChallengeCreateForm.title_ru)
async def create_title(msg: Message, state: FSMContext, user_lang: str = "ru"):
    lang  = await _wlang(state, user_lang)
    title = msg.text.strip()
    if not 2 <= len(title) <= 80:
        await msg.answer("❌ 2–80 символов.")
        return
    await state.update_data(title_ru=title)
    data = await state.get_data()
    if data.get("edit_mode"):
        await state.update_data(edit_mode=False)
        await _show_review(msg, state, lang)
        return
    await state.set_state(ChallengeCreateForm.description_ru)
    kb = InlineKeyboardBuilder()
    kb.button(text=t("adm_wiz_skip", lang), callback_data="adm:ch:skip_desc")
    kb.button(text=t("btn_cancel",   lang), callback_data="adm:ch:cancel_create")
    kb.adjust(1)
    await msg.answer(t("adm_wiz_description", lang, title=title),
                     reply_markup=kb.as_markup(), parse_mode="Markdown")


# Step 3 – description (optional)
@router.message(ChallengeCreateForm.description_ru)
async def create_description(msg: Message, state: FSMContext, user_lang: str = "ru"):
    lang = await _wlang(state, user_lang)
    desc = msg.text.strip()
    if len(desc) > 600:
        await msg.answer("❌ Max 600 chars.")
        return
    await state.update_data(description_ru=desc)
    await _after_description(msg, state, lang)


@router.callback_query(ChallengeCreateForm.description_ru, F.data == "adm:ch:skip_desc")
async def skip_description(cb: CallbackQuery, state: FSMContext, user_lang: str = "ru"):
    lang = await _wlang(state, user_lang)
    await state.update_data(description_ru="")
    await _after_description(cb, state, lang)


async def _after_description(target, state: FSMContext, lang: str = "ru") -> None:
    data = await state.get_data()
    if data.get("edit_mode"):
        await state.update_data(edit_mode=False)
        await _show_review(target, state, lang)
        return
    await state.set_state(ChallengeCreateForm.kind)
    kb = InlineKeyboardBuilder()
    from bot.i18n import KIND_LABELS
    for k, labels in KIND_LABELS.items():
        kb.button(text=labels.get(lang, labels["ru"]), callback_data=f"fsm:kind:{k}")
    kb.adjust(2)
    txt = t("adm_wiz_kind", lang)
    if isinstance(target, CallbackQuery):
        await target.message.edit_text(txt, reply_markup=kb.as_markup(), parse_mode="Markdown")
        await target.answer()
    else:
        await target.answer(txt, reply_markup=kb.as_markup(), parse_mode="Markdown")


# Step 4 – kind
@router.callback_query(ChallengeCreateForm.kind, F.data.startswith("fsm:kind:"))
async def create_kind(cb: CallbackQuery, state: FSMContext, user_lang: str = "ru"):
    lang = await _wlang(state, user_lang)
    kind = cb.data.split(":")[-1]
    await state.update_data(kind=kind)
    data = await state.get_data()
    if data.get("edit_mode"):
        await state.update_data(edit_mode=False)
        await _show_review(cb, state, lang)
        return
    await state.set_state(ChallengeCreateForm.question_ru)
    await cb.message.edit_text(
        t("adm_wiz_question", lang, kind=kind_label(kind, lang)),
        reply_markup=cancel_kb(lang), parse_mode="Markdown",
    )
    await cb.answer()


# Step 5 – question
@router.message(ChallengeCreateForm.question_ru)
async def create_question(msg: Message, state: FSMContext, user_lang: str = "ru"):
    lang = await _wlang(state, user_lang)
    q    = msg.text.strip()
    if not 5 <= len(q) <= 300:
        await msg.answer("❌ 5–300 символов.")
        return
    await state.update_data(question_ru=q)
    data = await state.get_data()
    if data.get("edit_mode"):
        await state.update_data(edit_mode=False)
        await _show_review(msg, state, lang)
        return
    # ── FIX: if kind is poll, ask for options before schedule ──
    if data.get("kind") == "poll":
        await state.set_state(ChallengeCreateForm.options_ru)
        await msg.answer(t("adm_wiz_options", lang),
                         reply_markup=cancel_kb(lang), parse_mode="Markdown")
    else:
        await state.set_state(ChallengeCreateForm.schedule_time)
        await msg.answer(t("adm_wiz_schedule", lang),
                         reply_markup=cancel_kb(lang), parse_mode="Markdown")


# Step 6 (poll only) – options
@router.message(ChallengeCreateForm.options_ru)
async def create_options(msg: Message, state: FSMContext, user_lang: str = "ru"):
    lang = await _wlang(state, user_lang)
    raw  = msg.text.strip()
    options = [o.strip() for o in raw.split("\n") if o.strip()]
    if len(options) < 2:
        await msg.answer(t("adm_wiz_options_invalid", lang), parse_mode="Markdown")
        return
    if len(options) > 10:
        await msg.answer(t("adm_wiz_options_too_many", lang), parse_mode="Markdown")
        return
    await state.update_data(options_ru=options)
    data = await state.get_data()
    if data.get("edit_mode"):
        await state.update_data(edit_mode=False)
        await _show_review(msg, state, lang)
        return
    await state.set_state(ChallengeCreateForm.schedule_time)
    await msg.answer(t("adm_wiz_schedule", lang),
                     reply_markup=cancel_kb(lang), parse_mode="Markdown")


# Step 6/7 – schedule_time
@router.message(ChallengeCreateForm.schedule_time)
async def create_schedule(msg: Message, state: FSMContext, user_lang: str = "ru"):
    lang = await _wlang(state, user_lang)
    raw  = msg.text.strip()
    try:
        h, m = map(int, raw.split(":"))
        assert 0 <= h <= 23 and 0 <= m <= 59
        formatted = f"{h:02d}:{m:02d}"
    except Exception:
        await msg.answer(t("adm_wiz_schedule_invalid", lang), parse_mode="Markdown")
        return
    await state.update_data(schedule_time=formatted)
    data = await state.get_data()
    if data.get("edit_mode"):
        await state.update_data(edit_mode=False)
        await _show_review(msg, state, lang)
        return
    await state.set_state(ChallengeCreateForm.duration_days)
    await msg.answer(t("adm_wiz_duration", lang),
                     reply_markup=cancel_kb(lang), parse_mode="Markdown")


# Step 7/8 – duration
@router.message(ChallengeCreateForm.duration_days)
async def create_duration(msg: Message, state: FSMContext, user_lang: str = "ru"):
    lang = await _wlang(state, user_lang)
    try:
        days = int(msg.text.strip())
        assert 1 <= days <= 3650
    except Exception:
        await msg.answer(t("adm_wiz_duration_invalid", lang))
        return
    await state.update_data(duration_days=days)
    data = await state.get_data()
    if data.get("edit_mode"):
        await state.update_data(edit_mode=False)
        await _show_review(msg, state, lang)
        return
    await state.set_state(ChallengeCreateForm.launch_at)
    await msg.answer(t("adm_wiz_launch", lang),
                     reply_markup=launch_time_kb(lang), parse_mode="Markdown")


# Step last – launch_at
@router.callback_query(ChallengeCreateForm.launch_at, F.data == "adm:ch:launch:now")
async def create_launch_now(cb: CallbackQuery, state: FSMContext, user_lang: str = "ru"):
    lang = await _wlang(state, user_lang)
    await state.update_data(launch_at=None, launch_at_display=None)
    await state.set_state(None)
    await _show_review(cb, state, lang)


@router.message(ChallengeCreateForm.launch_at)
async def create_launch_typed(msg: Message, state: FSMContext, user_lang: str = "ru"):
    lang = await _wlang(state, user_lang)
    raw  = msg.text.strip()
    try:
        dt = datetime.strptime(raw, "%Y-%m-%d %H:%M")
        moscow_tz = pytz.timezone("Europe/Moscow")
        localized_dt = moscow_tz.localize(dt)
        utc_dt = localized_dt.astimezone(pytz.UTC)
        dt = utc_dt.replace(tzinfo=timezone.utc)
    except ValueError:
        await msg.answer(t("adm_wiz_launch_invalid", lang), parse_mode="Markdown")
        return
    await state.update_data(launch_at=dt.isoformat(), launch_at_display=raw + " МСК")
    await state.set_state(None)
    await _show_review(msg, state, lang)


# ─── Review callbacks ──────────────────────────────────────────────────────

@router.callback_query(F.data == "adm:ch:review")
async def adm_review(cb: CallbackQuery, state: FSMContext, user_lang: str = "ru"):
    lang = await _wlang(state, user_lang)
    await _show_review(cb, state, lang)


@router.callback_query(F.data == "adm:ch:confirm")
async def adm_create_confirm(cb: CallbackQuery, state: FSMContext, user_lang: str = "ru"):
    lang = await _wlang(state, user_lang)
    data = await state.get_data()
    await state.clear()

    slug          = data["slug"]
    title_ru      = data["title_ru"]
    description   = data.get("description_ru", "")
    kind          = data["kind"]
    question_ru   = data["question_ru"]
    options_ru    = data.get("options_ru", [])   # ← FIX: persist poll options
    schedule_time = data["schedule_time"]
    duration_days = data["duration_days"]
    launch_at_iso = data.get("launch_at")

    metadata = {
        "translations": {
            "ru": {
                "title":       title_ru,
                "description": description,
                "question":    question_ru,
                "options":     options_ru,   # ← FIX: stored in metadata
            }
        },
        "schedule_time": schedule_time,
        "duration_days": duration_days,
        "launch_at":     launch_at_iso,
        "announced":     False,
    }

    await db.create_challenge(slug, kind, metadata)
    challenges = await db.fetch_all_challenges()
    await cb.message.edit_text(
        t("adm_ch_created", lang,
          title=title_ru, slug=slug, kind=kind,
          time=schedule_time, days=duration_days),
        reply_markup=admin_challenges_list_kb(challenges, lang),
        parse_mode="Markdown",
    )
    await cb.answer()


@router.callback_query(F.data == "adm:ch:edit_menu")
async def adm_edit_menu(cb: CallbackQuery, state: FSMContext, user_lang: str = "ru"):
    lang = user_lang
    data = await state.get_data()
    kind = data.get("kind", "")
    await cb.message.edit_text(
        t("adm_edit_menu_title", lang),
        reply_markup=edit_field_kb(lang, kind=kind), parse_mode="Markdown",
    )
    await cb.answer()


@router.callback_query(F.data.startswith("adm:ch:edit_field:"))
async def adm_edit_field(cb: CallbackQuery, state: FSMContext, user_lang: str = "ru"):
    field = cb.data.split(":")[-1]
    lang  = await _wlang(state, user_lang)
    await state.update_data(edit_mode=True)

    field_state_map = {
        "slug":           ChallengeCreateForm.slug,
        "title_ru":       ChallengeCreateForm.title_ru,
        "description_ru": ChallengeCreateForm.description_ru,
        "kind":           ChallengeCreateForm.kind,
        "question_ru":    ChallengeCreateForm.question_ru,
        "options_ru":     ChallengeCreateForm.options_ru,
        "schedule_time":  ChallengeCreateForm.schedule_time,
        "duration_days":  ChallengeCreateForm.duration_days,
    }
    field_prompts = {
        "slug":           t("adm_wiz_slug_invalid",    lang),
        "title_ru":       t("adm_wiz_title",           lang, slug="…"),
        "description_ru": t("adm_wiz_description",     lang, title="…"),
        "kind":           t("adm_wiz_kind",             lang),
        "question_ru":    t("adm_wiz_question",        lang, kind="…"),
        "options_ru":     t("adm_wiz_options",         lang),
        "schedule_time":  t("adm_wiz_schedule",        lang),
        "duration_days":  t("adm_wiz_duration",        lang),
    }
    target_state = field_state_map.get(field)
    if not target_state:
        await cb.answer(t("adm_edit_field_unknown", lang), show_alert=True)
        return
    await state.set_state(target_state)
    prompt = field_prompts.get(field, "")
    if field == "kind":
        kb = InlineKeyboardBuilder()
        from bot.i18n import KIND_LABELS
        for k, labels in KIND_LABELS.items():
            kb.button(text=labels.get(lang, labels["ru"]), callback_data=f"fsm:kind:{k}")
        kb.adjust(2)
        await cb.message.edit_text(f"✏️ {prompt}", reply_markup=kb.as_markup(), parse_mode="Markdown")
    elif field == "description_ru":
        kb = InlineKeyboardBuilder()
        kb.button(text=t("adm_wiz_skip",  lang), callback_data="adm:ch:skip_desc")
        kb.button(text=t("btn_nav_back",  lang), callback_data="adm:ch:review")
        kb.adjust(1)
        await cb.message.edit_text(f"✏️ {prompt}", reply_markup=kb.as_markup(), parse_mode="Markdown")
    else:
        await cb.message.edit_text(f"✏️ {prompt}", reply_markup=cancel_kb(lang), parse_mode="Markdown")
    await cb.answer()


# ─── Cancel ───────────────────────────────────────────────────────────────

@router.callback_query(F.data == "adm:ch:cancel_create")
async def cancel_create(cb: CallbackQuery, state: FSMContext, user_lang: str = "ru"):
    await state.clear()
    challenges = await db.fetch_all_challenges()
    await cb.message.edit_text(
        t("adm_challenges_title", user_lang),
        reply_markup=admin_challenges_list_kb(challenges, user_lang),
        parse_mode="Markdown",
    )
    await cb.answer(t("adm_wiz_cancelled", user_lang))


# ─── Translations wizard ───────────────────────────────────────────────────

@router.callback_query(F.data.startswith("adm:ch:translations:"))
async def adm_translations(cb: CallbackQuery, state: FSMContext, user_lang: str = "ru"):
    challenge_id = int(cb.data.split(":")[-1])
    c            = await db.get_challenge_by_id(challenge_id)
    if not c:
        await cb.answer(t("adm_ch_not_found", user_lang), show_alert=True)
        return
    meta     = c["metadata"]
    if isinstance(meta, str):
        meta = json.loads(meta)
    existing = [k for k in meta.get("translations", {}) if k != "ru"]
    await state.update_data(tr_challenge_id=challenge_id, wizard_lang=user_lang)
    await cb.message.edit_text(
        t("adm_tr_title", user_lang, slug=c["slug"]),
        reply_markup=admin_translation_lang_kb(challenge_id, existing, user_lang),
        parse_mode="Markdown",
    )
    await cb.answer()


@router.callback_query(F.data.startswith("adm:tr:lang:"))
async def adm_tr_select_lang(cb: CallbackQuery, state: FSMContext, user_lang: str = "ru"):
    parts        = cb.data.split(":")
    challenge_id = int(parts[3])
    lang_code    = parts[4]
    await state.set_state(ChallengeTranslateForm.title)
    await state.update_data(tr_challenge_id=challenge_id, tr_lang=lang_code,
                             wizard_lang=user_lang)
    lang_label = LANG_LABELS.get(lang_code, lang_code)
    await cb.message.edit_text(
        t("adm_tr_step_title", user_lang, lang_name=lang_label),
        parse_mode="Markdown",
    )
    await cb.answer()


@router.message(ChallengeTranslateForm.title)
async def adm_tr_title(msg: Message, state: FSMContext, user_lang: str = "ru"):
    lang  = await _wlang(state, user_lang)
    title = msg.text.strip()
    if not 2 <= len(title) <= 80:
        await msg.answer("❌ 2–80 символов.")
        return
    data = await state.get_data()
    await state.update_data(tr_title=title)
    await state.set_state(ChallengeTranslateForm.question)
    lang_label = LANG_LABELS.get(data["tr_lang"], data["tr_lang"])
    await msg.answer(t("adm_tr_step_question", lang, lang_name=lang_label),
                     parse_mode="Markdown")


@router.message(ChallengeTranslateForm.question)
async def adm_tr_question(msg: Message, state: FSMContext, user_lang: str = "ru"):
    lang     = await _wlang(state, user_lang)
    question = msg.text.strip()
    if not 5 <= len(question) <= 300:
        await msg.answer("❌ 5–300 символов.")
        return
    data         = await state.get_data()
    await state.clear()
    challenge_id = data["tr_challenge_id"]
    lang_code    = data["tr_lang"]
    title        = data["tr_title"]
    await db.update_challenge_translation(
        challenge_id=challenge_id, lang=lang_code,
        title=title, question=question,
    )
    lang_label = LANG_LABELS.get(lang_code, lang_code)
    await msg.answer(t("adm_tr_saved", lang, lang_name=lang_label),
                     parse_mode="Markdown")
    c    = await db.get_challenge_by_id(challenge_id)
    meta = c["metadata"]
    if isinstance(meta, str):
        meta = json.loads(meta)
    from bot.keyboards import admin_challenge_mgmt_kb as _mgmt
    await msg.answer(_challenge_card(c, meta, lang),
                     reply_markup=_mgmt(challenge_id, c["active"], lang),
                     parse_mode="Markdown")


# ─── Broadcast ────────────────────────────────────────────────────────────

@router.callback_query(F.data == "adm:broadcast")
async def adm_broadcast_start(cb: CallbackQuery, state: FSMContext, user_lang: str = "ru"):
    await state.set_state(BroadcastForm.text)
    await cb.message.edit_text(
        t("adm_broadcast_prompt", user_lang),
        reply_markup=cancel_kb(user_lang), parse_mode="Markdown",
    )
    await cb.answer()


@router.message(BroadcastForm.text)
async def adm_broadcast_text(msg: Message, state: FSMContext, user_lang: str = "ru"):
    text   = msg.text.strip()
    await state.clear()
    outbox = await db.create_outbox_message(text, target="all")
    await msg.answer(t("adm_broadcast_queued", user_lang, id=outbox["id"]),
                     reply_markup=admin_panel_kb(user_lang))