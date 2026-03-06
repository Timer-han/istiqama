"""bot/keyboards.py – language-aware keyboard builders.

Every function accepts `lang: str = "ru"` and uses i18n for button labels.
Inline callback_data strings remain language-independent.
"""
from __future__ import annotations

from typing import List

from aiogram.types import ReplyKeyboardMarkup, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder

from bot.i18n import t, SUPPORTED_LANGS, LANG_LABELS
from bot.utils import challenge_text


# ─── Reply keyboards ──────────────────────────────────────────────────────

def user_main_kb(lang: str = "ru") -> ReplyKeyboardMarkup:
    kb = ReplyKeyboardBuilder()
    kb.button(text=t("btn_stats",      lang))
    kb.button(text=t("btn_challenges", lang))
    kb.button(text=t("btn_settings",   lang))
    kb.adjust(3)
    return kb.as_markup(resize_keyboard=True)


def admin_main_kb(lang: str = "ru") -> ReplyKeyboardMarkup:
    kb = ReplyKeyboardBuilder()
    kb.button(text=t("btn_stats",       lang))
    kb.button(text=t("btn_challenges",  lang))
    kb.button(text=t("btn_settings",    lang))
    kb.button(text=t("btn_admin_panel", lang))
    kb.adjust(3)
    return kb.as_markup(resize_keyboard=True)


def settings_kb(lang: str = "ru") -> ReplyKeyboardMarkup:
    kb = ReplyKeyboardBuilder()
    kb.button(text=t("btn_location",    lang), request_location=True)
    kb.button(text=t("btn_change_lang", lang))
    kb.button(text=t("btn_back",        lang))
    kb.adjust(1)
    return kb.as_markup(resize_keyboard=True, one_time_keyboard=False)


def admin_panel_kb(lang: str = "ru") -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text=t("adm_btn_broadcast",  lang), callback_data="adm:broadcast")
    kb.button(text=t("adm_btn_challenges", lang), callback_data="adm:challenges")
    kb.button(text=t("adm_btn_stats",      lang), callback_data="adm:stats")
    kb.adjust(2)
    return kb.as_markup()


# ─── Language selection ────────────────────────────────────────────────────

def lang_select_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for code in SUPPORTED_LANGS:
        kb.button(text=LANG_LABELS[code], callback_data=f"set_lang:{code}")
    kb.adjust(1)
    return kb.as_markup()


# ─── Inline answer keyboards ──────────────────────────────────────────────

def yes_no_kb(challenge_id: int, lang: str = "ru") -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text=t("btn_yes", lang), callback_data=f"ans:{challenge_id}:yes")
    kb.button(text=t("btn_no",  lang), callback_data=f"ans:{challenge_id}:no")
    return kb.as_markup()


def scale_1_5_kb(challenge_id: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for i in range(1, 6):
        kb.button(text=str(i), callback_data=f"ans:{challenge_id}:{i}")
    kb.adjust(5)
    return kb.as_markup()


def poll_kb(challenge_id: int, options: List[str]) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for i, opt in enumerate(options):
        kb.button(text=opt, callback_data=f"ans:{challenge_id}:{i}")
    kb.adjust(1)
    return kb.as_markup()


def challenges_list_kb(
    challenges,
    user_participations: set,
    lang: str = "ru",
) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for c in challenges:
        is_in  = c["id"] in user_participations
        title, _ = challenge_text(c, lang)
        if is_in:
            label    = t("btn_leave_challenge", lang, title=title)
            action   = "leave"
        else:
            label    = t("btn_join_challenge_list", lang, title=title)
            action   = "join"
        kb.button(
            text=label,
            callback_data=f"challenge:{action}:{c['id']}",
        )
    kb.adjust(1)
    return kb.as_markup()


def challenge_announce_kb(challenge_id: int, lang: str = "ru") -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(
        text=t("btn_join_challenge", lang),
        callback_data=f"challenge:join:{challenge_id}",
    )
    return kb.as_markup()


# ─── Admin keyboards ──────────────────────────────────────────────────────

def admin_challenge_mgmt_kb(challenge_id: int, active: bool, lang: str = "ru") -> InlineKeyboardMarkup:
    toggle = t("adm_ch_btn_deactivate" if active else "adm_ch_btn_activate", lang)
    kb = InlineKeyboardBuilder()
    kb.button(text=toggle,                              callback_data=f"adm:ch:toggle:{challenge_id}")
    kb.button(text=t("adm_ch_btn_delete",       lang),  callback_data=f"adm:ch:delete:{challenge_id}")
    kb.button(text=t("adm_ch_btn_stats",        lang),  callback_data=f"adm:ch:stats:{challenge_id}")
    kb.button(text=t("adm_ch_btn_detail",       lang),  callback_data=f"adm:ch:detail:{challenge_id}")
    kb.button(text=t("adm_ch_btn_translations", lang),  callback_data=f"adm:ch:translations:{challenge_id}")
    kb.button(text=t("btn_nav_back",            lang),  callback_data="adm:challenges")
    kb.adjust(2)
    return kb.as_markup()


def admin_challenges_list_kb(challenges, lang: str = "ru") -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for c in challenges:
        status = "🟢" if c["active"] else "🔴"
        kb.button(
            text=f"{status} {c['slug']}",
            callback_data=f"adm:ch:view:{c['id']}",
        )
    kb.button(text=t("adm_ch_btn_create", lang), callback_data="adm:ch:create")
    kb.button(text=t("btn_nav_back",      lang), callback_data="adm:panel")
    kb.adjust(1)
    return kb.as_markup()


def admin_translation_lang_kb(challenge_id: int, existing_langs: list[str], lang: str = "ru") -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for code in ("en", "tt"):
        label = LANG_LABELS[code]
        mark  = " ✅" if code in existing_langs else ""
        kb.button(
            text=f"{label}{mark}",
            callback_data=f"adm:tr:lang:{challenge_id}:{code}",
        )
    kb.button(text=t("btn_nav_back", lang), callback_data=f"adm:ch:view:{challenge_id}")
    kb.adjust(1)
    return kb.as_markup()


def confirm_create_kb(lang: str = "ru") -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text=t("adm_wiz_confirm_btn", lang), callback_data="adm:ch:confirm")
    kb.button(text=t("adm_wiz_edit_btn",   lang),  callback_data="adm:ch:edit_menu")
    kb.button(text=t("adm_wiz_cancel_btn", lang),  callback_data="adm:ch:cancel_create")
    kb.adjust(2)
    return kb.as_markup()


def launch_time_kb(lang: str = "ru") -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text=t("btn_launch_now",   lang), callback_data="adm:ch:launch:now")
    kb.button(text=t("btn_cancel",       lang), callback_data="adm:ch:cancel_create")
    kb.adjust(1)
    return kb.as_markup()


def edit_field_kb(lang: str = "ru", kind: str = "") -> InlineKeyboardMarkup:
    """
    Edit-field menu for the create wizard.
    When kind == 'poll', an extra 'Options' row is shown.
    All labels are pulled from i18n.
    """
    fields: list[tuple[str, str]] = [
        (t("adm_field_slug",        lang), "adm:ch:edit_field:slug"),
        (t("adm_field_title",       lang), "adm:ch:edit_field:title_ru"),
        (t("adm_field_description", lang), "adm:ch:edit_field:description_ru"),
        (t("adm_field_kind",        lang), "adm:ch:edit_field:kind"),
        (t("adm_field_question",    lang), "adm:ch:edit_field:question_ru"),
    ]
    if kind == "poll":
        fields.append((t("adm_field_options", lang), "adm:ch:edit_field:options_ru"))
    fields += [
        (t("adm_field_schedule", lang), "adm:ch:edit_field:schedule_time"),
        (t("adm_field_duration", lang), "adm:ch:edit_field:duration_days"),
        (t("btn_nav_back",       lang), "adm:ch:review"),
    ]
    kb = InlineKeyboardBuilder()
    for label, cd in fields:
        kb.button(text=label, callback_data=cd)
    kb.adjust(2)
    return kb.as_markup()


def back_to_panel_kb(lang: str = "ru") -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text=t("btn_nav_back", lang), callback_data="adm:panel")
    return kb.as_markup()


def cancel_kb(lang: str = "ru") -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text=t("btn_cancel", lang), callback_data="adm:ch:cancel_create")
    return kb.as_markup()