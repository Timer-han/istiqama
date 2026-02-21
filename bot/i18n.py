"""bot/i18n.py – All UI strings in ru / en / tt (Tatar).

Usage:
    from bot.i18n import t, user_lang
    lang = user_lang(db_user)          # "ru" | "en" | "tt"
    text = t("welcome", lang, name="…")

Fallback chain:  lang → "ru" → key_string_itself
"""
from __future__ import annotations

SUPPORTED_LANGS = ("ru", "en", "tt")
DEFAULT_LANG    = "ru"

LANG_LABELS: dict[str, str] = {
    "ru": "🇷🇺 Русский",
    "en": "🇬🇧 English",
    "tt": "🏴 Татарча",
}

KIND_LABELS: dict[str, dict[str, str]] = {
    "yes_no":    {"ru": "Да / Нет",   "en": "Yes / No",  "tt": "Әйе / Юк"},
    "count":     {"ru": "Число",      "en": "Number",    "tt": "Сан"},
    "scale_1_5": {"ru": "Шкала 1–5",  "en": "Scale 1–5", "tt": "Шкала 1–5"},
    "poll":      {"ru": "Варианты",   "en": "Options",   "tt": "Варианты"},
}

# ─── String table ──────────────────────────────────────────────────────────
_S: dict[str, dict[str, str]] = {

    # ── Reply-keyboard button labels ───────────────────────────────────────
    # IMPORTANT: these exact strings are used by ButtonText filter for routing.
    "btn_stats": {
        "ru": "📊 Моя статистика",
        "en": "📊 My Statistics",
        "tt": "📊 Минем статистика",
    },
    "btn_challenges": {
        "ru": "🕌 Челленджи",
        "en": "🕌 Challenges",
        "tt": "🕌 Чәлленҗлар",
    },
    "btn_settings": {
        "ru": "⚙️ Настройки",
        "en": "⚙️ Settings",
        "tt": "⚙️ Көйләүләр",
    },
    "btn_admin_panel": {
        "ru": "🛠 Панель админа",
        "en": "🛠 Admin Panel",
        "tt": "🛠 Админ панеле",
    },
    "btn_location": {
        "ru": "📍 Отправить геолокацию",
        "en": "📍 Send Location",
        "tt": "📍 Геолокация жибәрү",
    },
    "btn_change_lang": {
        "ru": "🌐 Сменить язык",
        "en": "🌐 Change Language",
        "tt": "🌐 Телне алыштыру",
    },
    "btn_back": {
        "ru": "◀ Назад",
        "en": "◀ Back",
        "tt": "◀ Артка",
    },

    # ── General ────────────────────────────────────────────────────────────
    "welcome": {
        "ru": "Ассаляму алейкум, {name}! 🌙\n\nДобро пожаловать в Истикама — трекер исламских привычек.\nВыбери раздел:",
        "en": "Assalamu alaykum, {name}! 🌙\n\nWelcome to Istiqama — your Islamic habits tracker.\nChoose a section:",
        "tt": "Әссәламү галәйкем, {name}! 🌙\n\nИстикама — исламик гадәтләр трекерена хуш килдегез.\nБүлек сайлагыз:",
    },
    "main_menu_prompt": {
        "ru": "Главное меню:",
        "en": "Main menu:",
        "tt": "Төп меню:",
    },
    "start_first": {
        "ru": "Сначала отправь /start",
        "en": "Please send /start first",
        "tt": "Башта /start языгыз",
    },

    # ── Statistics ─────────────────────────────────────────────────────────
    "stats_header": {
        "ru": "📊 *Твоя статистика за 7 дней:*\n",
        "en": "📊 *Your stats for the last 7 days:*\n",
        "tt": "📊 *Соңгы 7 көн статистикасы:*\n",
    },
    "stats_row": {
        "ru": "• {day} | {title}: *{val}*",
        "en": "• {day} | {title}: *{val}*",
        "tt": "• {day} | {title}: *{val}*",
    },
    "stats_empty": {
        "ru": "За последние 7 дней ответов нет.",
        "en": "No responses in the last 7 days.",
        "tt": "Соңгы 7 көндә җаваплар юк.",
    },

    # ── Challenges ─────────────────────────────────────────────────────────
    "challenges_header": {
        "ru": "🕌 *Активные челленджи:*\n",
        "en": "🕌 *Active challenges:*\n",
        "tt": "🕌 *Актив чәлленҗлар:*\n",
    },
    "no_challenges": {
        "ru": "Нет активных челленджей.",
        "en": "No active challenges.",
        "tt": "Актив чәлленҗлар юк.",
    },
    "joined_challenge": {
        "ru": "✅ Ты вступил в челлендж!",
        "en": "✅ You joined the challenge!",
        "tt": "✅ Сез чәлленҗгә кердегез!",
    },
    "already_participating": {
        "ru": "Ты уже участвуешь.",
        "en": "You are already participating.",
        "tt": "Сез инде катнашасыз.",
    },
    "left_challenge": {
        "ru": "Ты вышел из челленджа.",
        "en": "You left the challenge.",
        "tt": "Сез чәлленҗдән чыктыгыз.",
    },

    # ── Settings ───────────────────────────────────────────────────────────
    "settings_header": {
        "ru": "⚙️ *Настройки*\n\nЧасовой пояс: `{tz}`\nЯзык: {lang_label}\n\nОтправь геолокацию для автоопределения таймзоны.\nИли введи вручную: `/timezone Europe/Moscow`",
        "en": "⚙️ *Settings*\n\nTimezone: `{tz}`\nLanguage: {lang_label}\n\nSend your location to detect timezone automatically.\nOr type manually: `/timezone Europe/Moscow`",
        "tt": "⚙️ *Көйләүләр*\n\nВакыт зонасы: `{tz}`\nТел: {lang_label}\n\nВакыт зонасын автоматик билгеләү өчен геолокацияне жибәрегез.\nЯки языгыз: `/timezone Europe/Moscow`",
    },
    "tz_invalid": {
        "ru": "❌ Неверный таймзон. Пример: `Europe/Moscow`",
        "en": "❌ Invalid timezone. Example: `Europe/Moscow`",
        "tt": "❌ Дөрес булмаган вакыт зонасы. Мисал: `Europe/Moscow`",
    },
    "tz_updated": {
        "ru": "✅ Часовой пояс обновлён: `{tz}`",
        "en": "✅ Timezone updated: `{tz}`",
        "tt": "✅ Вакыт зонасы яңартылды: `{tz}`",
    },
    "location_received": {
        "ru": "📍 Геолокация получена.\nЧасовой пояс определён: `{tz}`\n\nВопросы теперь будут приходить в нужное время.",
        "en": "📍 Location received.\nTimezone detected: `{tz}`\n\nYou will now receive questions at the right time.",
        "tt": "📍 Геолокация алынды.\nВакыт зонасы: `{tz}`\n\nСорауларны дөрес вакытта аласыз.",
    },

    # ── Language selection ──────────────────────────────────────────────────
    "lang_select": {
        "ru": "🌐 Выбери язык интерфейса:",
        "en": "🌐 Choose interface language:",
        "tt": "🌐 Интерфейс телен сайлагыз:",
    },
    "lang_set": {
        "ru": "✅ Язык изменён: {lang_label}",
        "en": "✅ Language changed: {lang_label}",
        "tt": "✅ Тел алмаштырылды: {lang_label}",
    },

    # ── Answer responses ───────────────────────────────────────────────────
    "answer_recorded": {
        "ru": "✅ Ответ «{value}» на челлендж *{title}* принят.",
        "en": "✅ Answer «{value}» for challenge *{title}* recorded.",
        "tt": "✅ *{title}* чәлленҗенә «{value}» кабул ителде.",
    },
    "answer_toast": {
        "ru": "✅ Записано!",
        "en": "✅ Recorded!",
        "tt": "✅ Язылды!",
    },
    "already_answered": {
        "ru": "Ты уже отвечал сегодня на этот вопрос.",
        "en": "You have already answered this question today.",
        "tt": "Сез бүген инде бу соруга җавап бирдегез.",
    },
    "challenge_not_found": {
        "ru": "Челлендж не найден.",
        "en": "Challenge not found.",
        "tt": "Чәлленҗ табылмады.",
    },

    # ── Count input ─────────────────────────────────────────────────────────
    "count_prompt": {
        "ru": "\n\n✏️ Введи число в ответ на это сообщение.",
        "en": "\n\n✏️ Reply to this message with a number.",
        "tt": "\n\n✏️ Бу хәбәргә сан белән җавап языгыз.",
    },
    "count_recorded": {
        "ru": "✅ Записано {count} для *{title}*.",
        "en": "✅ Recorded {count} for *{title}*.",
        "tt": "✅ *{title}* өчен {count} язылды.",
    },
    "count_already_answered": {
        "ru": "Ты уже отвечал сегодня.",
        "en": "You have already answered today.",
        "tt": "Сез бүген инде җавап бирдегез.",
    },
    "count_multiple_pending": {
        "ru": "У тебя несколько ожидающих вопросов с числовым ответом. Ответь через кнопку в нужном сообщении.\n\nОжидают:\n{list}",
        "en": "You have multiple count questions pending. Please reply via the button in the specific message.\n\nPending:\n{list}",
        "tt": "Сездә берничә санлы сорау бар. Дөрес хәбәрдәге төймә аша җавап биреп карагыз.\n\nКөтеп тора:\n{list}",
    },

    # ── Challenge announcement ─────────────────────────────────────────────
    "challenge_announce": {
        "ru": "🕌 *Новый челлендж: {title}*\n\n{description}\n\n📋 Тип: {kind}\n⏰ Ежедневно в: {time}\n📆 Длительность: {days} дней\n\nПрисоединяйся к испытанию!",
        "en": "🕌 *New Challenge: {title}*\n\n{description}\n\n📋 Type: {kind}\n⏰ Daily at: {time}\n📆 Duration: {days} days\n\nJoin the challenge!",
        "tt": "🕌 *Яңа чәлленҗ: {title}*\n\n{description}\n\n📋 Төр: {kind}\n⏰ Көн саен: {time}\n📆 Озынлыгы: {days} көн\n\nЧәлленҗгә катнаш!",
    },
    "btn_join_challenge": {
        "ru": "✅ Участвовать",
        "en": "✅ Join Challenge",
        "tt": "✅ Катнашу",
    },

    # ── Admin panel ────────────────────────────────────────────────────────
    "adm_panel_title": {
        "ru": "🛠 *Панель администратора*",
        "en": "🛠 *Admin Panel*",
        "tt": "🛠 *Администратор панеле*",
    },
    "adm_btn_broadcast": {
        "ru": "📣 Рассылка",
        "en": "📣 Broadcast",
        "tt": "📣 Рассылка",
    },
    "adm_btn_challenges": {
        "ru": "🧩 Челленджи",
        "en": "🧩 Challenges",
        "tt": "🧩 Чәлленҗлар",
    },
    "adm_btn_stats": {
        "ru": "📊 Статистика",
        "en": "📊 Statistics",
        "tt": "📊 Статистика",
    },
    "adm_stats_header": {
        "ru": "👥 Всего пользователей: *{total}*\n🔥 Ответили сегодня: *{today}*\n\n📊 *Статистика по челленджам (сегодня):*",
        "en": "👥 Total users: *{total}*\n🔥 Active today: *{today}*\n\n📊 *Challenge statistics (today):*",
        "tt": "👥 Барлык кулланучылар: *{total}*\n🔥 Бүген актив: *{today}*\n\n📊 *Чәлленҗ статистикасы (бүген):*",
    },
    "adm_stats_row": {
        "ru": "\n• *{title}*\n  Ответили: {resp} | Среднее: {avg} | Макс: {max}",
        "en": "\n• *{title}*\n  Answered: {resp} | Avg: {avg} | Max: {max}",
        "tt": "\n• *{title}*\n  Җавап биргән: {resp} | Уртача: {avg} | Макс: {max}",
    },
    "adm_challenges_title": {
        "ru": "🧩 *Управление челленджами:*",
        "en": "🧩 *Challenge Management:*",
        "tt": "🧩 *Чәлленҗларны идарә итү:*",
    },
    "adm_ch_status_active": {
        "ru": "🟢 Активен",
        "en": "🟢 Active",
        "tt": "🟢 Актив",
    },
    "adm_ch_status_inactive": {
        "ru": "🔴 Неактивен",
        "en": "🔴 Inactive",
        "tt": "🔴 Актив түгел",
    },
    "adm_ch_btn_deactivate": {
        "ru": "🔴 Деактивировать",
        "en": "🔴 Deactivate",
        "tt": "🔴 Деактивацияләргә",
    },
    "adm_ch_btn_activate": {
        "ru": "🟢 Активировать",
        "en": "🟢 Activate",
        "tt": "🟢 Активацияләргә",
    },
    "adm_ch_btn_delete": {
        "ru": "🗑 Удалить",
        "en": "🗑 Delete",
        "tt": "🗑 Бетерергә",
    },
    "adm_ch_btn_stats": {
        "ru": "📊 Статистика",
        "en": "📊 Statistics",
        "tt": "📊 Статистика",
    },
    "adm_ch_btn_translations": {
        "ru": "🌐 Переводы",
        "en": "🌐 Translations",
        "tt": "🌐 Тәрҗемәләр",
    },
    "adm_ch_btn_create": {
        "ru": "➕ Создать челлендж",
        "en": "➕ Create Challenge",
        "tt": "➕ Чәлленҗ булдырырга",
    },
    "adm_ch_toggled_active": {
        "ru": "Челлендж активирован 🟢",
        "en": "Challenge activated 🟢",
        "tt": "Чәлленҗ активлаштырылды 🟢",
    },
    "adm_ch_toggled_inactive": {
        "ru": "Челлендж деактивирован 🔴",
        "en": "Challenge deactivated 🔴",
        "tt": "Чәлленҗ деактивлаштырылды 🔴",
    },
    "adm_ch_deleted": {
        "ru": "Удалён.",
        "en": "Deleted.",
        "tt": "Бетерелде.",
    },
    "adm_ch_not_found": {
        "ru": "Не найден",
        "en": "Not found",
        "tt": "Табылмады",
    },
    "adm_ch_stats_today": {
        "ru": "📊 *{title}* — сегодня\n\nОтветили: {resp}\nСреднее: {avg}\nМаксимум: {max}",
        "en": "📊 *{title}* — today\n\nAnswered: {resp}\nAverage: {avg}\nMax: {max}",
        "tt": "📊 *{title}* — бүген\n\nЖавап биргән: {resp}\nУртача: {avg}\nМаксимум: {max}",
    },
    "adm_ch_stats_empty": {
        "ru": "📊 *{title}* — сегодня ответов нет.",
        "en": "📊 *{title}* — no responses today.",
        "tt": "📊 *{title}* — бүген җаваплар юк.",
    },
    # ── Wizard steps ────────────────────────────────────────────────────────
    "adm_wiz_start": {
        "ru": "🆕 *Создание челленджа*\n\nШаг 1/8 — введи slug.\nТолько a-z, 0-9, дефис. Пример: `daily-prayer`",
        "en": "🆕 *Create Challenge*\n\nStep 1/8 — enter slug.\nOnly a-z, 0-9, hyphen. Example: `daily-prayer`",
        "tt": "🆕 *Чәлленҗ булдыру*\n\nАдым 1/8 — slug языгыз.\nТик a-z, 0-9, дефис. Мисал: `daily-prayer`",
    },
    "adm_wiz_slug_invalid": {
        "ru": "❌ Slug — только a-z, 0-9 и дефис.\nПример: `daily-prayer`",
        "en": "❌ Slug — only a-z, 0-9 and hyphen.\nExample: `daily-prayer`",
        "tt": "❌ Slug — тик a-z, 0-9 һәм дефис.\nМисал: `daily-prayer`",
    },
    "adm_wiz_slug_taken": {
        "ru": "❌ Этот slug уже занят. Придумай другой:",
        "en": "❌ This slug is already taken. Try another:",
        "tt": "❌ Бу slug инде бар. Башкасын языгыз:",
    },
    "adm_wiz_title": {
        "ru": "Slug: `{slug}`\n\nШаг 2/8 — введи *название* на русском:",
        "en": "Slug: `{slug}`\n\nStep 2/8 — enter *title* in Russian:",
        "tt": "Slug: `{slug}`\n\nАдым 2/8 — рус телендә *исем* языгыз:",
    },
    "adm_wiz_description": {
        "ru": "Название: *{title}*\n\nШаг 3/8 — введи *описание* (необязательно):",
        "en": "Title: *{title}*\n\nStep 3/8 — enter *description* (optional):",
        "tt": "Исем: *{title}*\n\nАдым 3/8 — *тасвирлама* языгыз (кирәк түгел):",
    },
    "adm_wiz_skip": {
        "ru": "⏭ Пропустить",
        "en": "⏭ Skip",
        "tt": "⏭ Узып китү",
    },
    "adm_wiz_kind": {
        "ru": "Шаг 4/8 — выбери *тип вопроса*:",
        "en": "Step 4/8 — choose *question type*:",
        "tt": "Адым 4/8 — *сорау төрен* сайлагыз:",
    },
    "adm_wiz_question": {
        "ru": "Тип: *{kind}*\n\nШаг 5/8 — введи *текст вопроса* на русском:",
        "en": "Type: *{kind}*\n\nStep 5/8 — enter *question text* in Russian:",
        "tt": "Төр: *{kind}*\n\nАдым 5/8 — рус телендә *сорау тексты* языгыз:",
    },
    "adm_wiz_schedule": {
        "ru": "Шаг 6/8 — время ежедневной отправки (ЧЧ:ММ, например `06:00`):",
        "en": "Step 6/8 — daily send time (HH:MM, e.g. `06:00`):",
        "tt": "Адым 6/8 — көнлек жибәрү вакыты (СС:ДД, мәс. `06:00`):",
    },
    "adm_wiz_schedule_invalid": {
        "ru": "❌ Неверный формат. Введи ЧЧ:ММ, например `06:00`:",
        "en": "❌ Wrong format. Enter HH:MM, e.g. `06:00`:",
        "tt": "❌ Дөрес булмаган формат. СС:ДД языгыз, мәс. `06:00`:",
    },
    "adm_wiz_duration": {
        "ru": "Шаг 7/8 — длительность в днях (например `40`):",
        "en": "Step 7/8 — duration in days (e.g. `40`):",
        "tt": "Адым 7/8 — озынлыгы көннәрдә (мәс. `40`):",
    },
    "adm_wiz_duration_invalid": {
        "ru": "❌ Введи целое число от 1 до 3650.",
        "en": "❌ Enter a whole number from 1 to 3650.",
        "tt": "❌ 1 дән 3650 гача бөтен сан языгыз.",
    },
    "adm_wiz_launch": {
        "ru": "Шаг 8/8 — когда запустить челлендж?\n\nНажми *Прямо сейчас* или введи дату по Москве:\n`ГГГГ-ММ-ДД ЧЧ:ММ`",
        "en": "Step 8/8 — when to launch the challenge?\n\nTap *Right Now* or enter Moskow date:\n`YYYY-MM-DD HH:MM`",
        "tt": "Адым 8/8 — чәлленҗне кайчан башларга?\n\n*Хәзер үк* басыгыз яки Казандагы вакытын языгыз:\n`ГГГГ-АА-КК СС:ДД`",
    },
    "adm_wiz_launch_invalid": {
        "ru": "❌ Неверный формат. Пример: `2025-03-20 09:00`",
        "en": "❌ Wrong format. Example: `2025-03-20 09:00`",
        "tt": "❌ Дөрес булмаган формат. Мисал: `2025-03-20 09:00`",
    },
    "btn_launch_now": {
        "ru": "⚡ Прямо сейчас",
        "en": "⚡ Right Now",
        "tt": "⚡ Хәзер үк",
    },
    "adm_wiz_review": {
        "ru": (
            "📋 *Предпросмотр нового челленджа:*\n\n"
            "Slug: `{slug}`\nНазвание: {title}\nОписание: {desc}\n"
            "Тип: {kind}\nВопрос: _{question}_\n"
            "Время: `{time}`\nДлительность: {days} дней\n"
            "Запуск: {launch}\n\n"
            "Создать челлендж?"
        ),
        "en": (
            "📋 *New Challenge Preview:*\n\n"
            "Slug: `{slug}`\nTitle: {title}\nDescription: {desc}\n"
            "Type: {kind}\nQuestion: _{question}_\n"
            "Time: `{time}`\nDuration: {days} days\n"
            "Launch: {launch}\n\n"
            "Create challenge?"
        ),
        "tt": (
            "📋 *Яңа чәлленҗ карашы:*\n\n"
            "Slug: `{slug}`\nИсем: {title}\nТасвирлама: {desc}\n"
            "Төр: {kind}\nСорау: _{question}_\n"
            "Вакыт: `{time}`\nОзынлыгы: {days} көн\n"
            "Башлану: {launch}\n\n"
            "Чәлленҗ булдырырга?"
        ),
    },
    "adm_wiz_review_now": {
        "ru": "сразу после создания",
        "en": "immediately after creation",
        "tt": "булдырылгач дәррәү",
    },
    "adm_wiz_confirm_btn": {
        "ru": "✅ Создать",
        "en": "✅ Create",
        "tt": "✅ Булдырырга",
    },
    "adm_wiz_edit_btn": {
        "ru": "✏️ Редактировать",
        "en": "✏️ Edit",
        "tt": "✏️ Үзгәртергә",
    },
    "adm_wiz_cancel_btn": {
        "ru": "❌ Отменить",
        "en": "❌ Cancel",
        "tt": "❌ Баш тарту",
    },
    "adm_ch_created": {
        "ru": "✅ Челлендж *{title}* (`{slug}`) создан!\nТип: `{kind}` | Время: `{time}` | Дней: {days}",
        "en": "✅ Challenge *{title}* (`{slug}`) created!\nType: `{kind}` | Time: `{time}` | Days: {days}",
        "tt": "✅ Чәлленҗ *{title}* (`{slug}`) булдырылды!\nТөр: `{kind}` | Вакыт: `{time}` | Көннәр: {days}",
    },
    "adm_wiz_cancelled": {
        "ru": "Отменено",
        "en": "Cancelled",
        "tt": "Кире кайтарылды",
    },
    # ── Broadcast ───────────────────────────────────────────────────────────
    "adm_broadcast_prompt": {
        "ru": "📣 *Рассылка*\n\nВведи текст сообщения (поддерживается Markdown):",
        "en": "📣 *Broadcast*\n\nEnter message text (Markdown supported):",
        "tt": "📣 *Рассылка*\n\nХәбәр тексты языгыз (Markdown ярдәме бар):",
    },
    "adm_broadcast_queued": {
        "ru": "✅ Рассылка #{id} поставлена в очередь.",
        "en": "✅ Broadcast #{id} queued.",
        "tt": "✅ Рассылка #{id} чиратка куелды.",
    },
    # ── Translations wizard ──────────────────────────────────────────────────
    "adm_tr_title": {
        "ru": "🌐 *Переводы* — `{slug}`\n\nВыбери язык:",
        "en": "🌐 *Translations* — `{slug}`\n\nChoose language:",
        "tt": "🌐 *Тәрҗемәләр* — `{slug}`\n\nТел сайлагыз:",
    },
    "adm_tr_step_title": {
        "ru": "🌐 Перевод на *{lang_name}*\n\nШаг 1/2 — введи *название*:",
        "en": "🌐 Translation to *{lang_name}*\n\nStep 1/2 — enter *title*:",
        "tt": "🌐 *{lang_name}* теленә тәрҗемә\n\nАдым 1/2 — *исем* языгыз:",
    },
    "adm_tr_step_question": {
        "ru": "🌐 Перевод на *{lang_name}*\n\nШаг 2/2 — введи *текст вопроса*:",
        "en": "🌐 Translation to *{lang_name}*\n\nStep 2/2 — enter *question text*:",
        "tt": "🌐 *{lang_name}* теленә тәрҗемә\n\nАдым 2/2 — *сорау тексты* языгыз:",
    },
    "adm_tr_saved": {
        "ru": "✅ Перевод на *{lang_name}* сохранён.",
        "en": "✅ Translation to *{lang_name}* saved.",
        "tt": "✅ *{lang_name}* теленә тәрҗемә сакланды.",
    },
    # ── Edit wizard ──────────────────────────────────────────────────────────
    "adm_edit_menu_title": {
        "ru": "✏️ *Что редактируем?*",
        "en": "✏️ *What to edit?*",
        "tt": "✏️ *Нәрсәне үзгәртәбез?*",
    },
    "adm_edit_field_unknown": {
        "ru": "Неизвестное поле",
        "en": "Unknown field",
        "tt": "Билгесез кыр",
    },
    # ── Back / Cancel ────────────────────────────────────────────────────────
    "btn_cancel": {
        "ru": "❌ Отмена",
        "en": "❌ Cancel",
        "tt": "❌ Баш тарту",
    },
    "btn_nav_back": {
        "ru": "◀ Назад",
        "en": "◀ Back",
        "tt": "◀ Артка",
    },
}


# ─── Public API ────────────────────────────────────────────────────────────

def t(key: str, lang: str = DEFAULT_LANG, **kwargs: object) -> str:
    """Translate key to lang with optional {placeholder} substitution."""
    lang   = lang if lang in SUPPORTED_LANGS else DEFAULT_LANG
    bucket = _S.get(key, {})
    text   = bucket.get(lang) or bucket.get(DEFAULT_LANG) or key
    if kwargs:
        try:
            text = text.format(**kwargs)
        except (KeyError, ValueError):
            pass
    return text


def user_lang(user) -> str:
    """Extract language code from a user Record/dict; default to ru."""
    if user is None:
        return DEFAULT_LANG
    lang = (user.get("lang", DEFAULT_LANG) if hasattr(user, "get") else DEFAULT_LANG)
    return lang if lang in SUPPORTED_LANGS else DEFAULT_LANG


def kind_label(kind: str, lang: str = DEFAULT_LANG) -> str:
    """Human-readable label for a challenge kind in given language."""
    return KIND_LABELS.get(kind, {}).get(lang) or KIND_LABELS.get(kind, {}).get(DEFAULT_LANG) or kind
