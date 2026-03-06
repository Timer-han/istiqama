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
    "poll":      {"ru": "Варианты",   "en": "Options",   "tt": "Вариантлар"},
}

# ─── String table ──────────────────────────────────────────────────────────
_S: dict[str, dict[str, str]] = {

    # ── Reply-keyboard button labels ───────────────────────────────────────
    "btn_stats": {
        "ru": "📊 Моя статистика",
        "en": "📊 My Statistics",
        "tt": "📊 Статистикам",
    },
    "btn_challenges": {
        "ru": "🕌 Челленджи",
        "en": "🕌 Challenges",
        "tt": "🕌 Сынаулар",
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
        "tt": "📍 Урынны жибәрү",
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

    # ── Inline Yes / No answer buttons ────────────────────────────────────
    "btn_yes": {
        "ru": "✅ Да",
        "en": "✅ Yes",
        "tt": "✅ Әйе",
    },
    "btn_no": {
        "ru": "❌ Нет",
        "en": "❌ No",
        "tt": "❌ Юк",
    },

    # ── General ────────────────────────────────────────────────────────────
    "welcome": {
        "ru": """Ас-саляму алейкум, {name}!

Это бот Istiqama, трекер халяльных привычек, разработанный для развития уммы.

В боте можно присоединиться к различным коллективным и индивидуальным челленджам. Каждый день будут приходить вопросы и в конце периода можно будет увидеть свой прогресс!

Нажми на меню снизу, чтобы увидеть все возможности!""",
        "en": """As-salamu alaykum, {name}

This is the Istiqama bot, a halal habit tracker developed for the growth of the ummah.

In the bot, you can join various collective and individual challenges. Every day you will receive questions, and at the end of the period you will be able to see your progress!

Click the menu below to see all the features!""",
        "tt": """Әс-сәламү галәйкүм, {name}

Бу — Istiqama боты, өммәтне үстерү өчен эшләнгән хәләл гадәтләр трекеры.

Ботта син төрле коллектив һәм шәхси сынауларга кушыла аласың. Һәр көн сораулар киләчәк, ә чор ахырында үз прогрессыңны күрә алачаксыз!

Барлык мөмкинлекләрне күрү өчен астагы менюга басыгыз!""",
    },
    "main_menu_prompt": {
        "ru": "Главное меню:",
        "en": "Main menu:",
        "tt": "Төп меню:",
    },
    "start_first": {
        "ru": "Сначала отправьте /start",
        "en": "Please send /start first",
        "tt": "Башта /start дип языгыз",
    },

    # ── Statistics ─────────────────────────────────────────────────────────
    "stats_header": {
        "ru": "📊 *Ваша статистика за 7 дней:*\n",
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
    "stats_detail_header": {
        "ru": "📊 *Моя статистика*\n",
        "en": "📊 *My Statistics*\n",
        "tt": "📊 *Минем статистика*\n",
    },
    "stats_no_active": {
        "ru": "У тебя нет активных участий в челленджах.",
        "en": "You are not participating in any challenges.",
        "tt": "Сезнең актив чәлленҗләрегез юк.",
    },
    "stats_no_answers_yet": {
        "ru": "_Ответов пока нет_",
        "en": "_No answers yet_",
        "tt": "_Җаваплар юк әле_",
    },

    # ── yes_no ────────────────────────────────────────────────────────────
    "stats_yesno_block": {
        "ru": (
            "✅ *{title}* _(да/нет)_\n"
            "За неделю: {yes_7}/{days_7} дней ✅\n"
            "За всё время: {yes_all}/{total_days} дней ✅ ({pct_all}%)\n"
            "Серия сейчас: {cur_streak} 🔥 | Рекорд: {max_streak} 🏆"
        ),
        "en": (
            "✅ *{title}* _(yes/no)_\n"
            "This week: {yes_7}/{days_7} days ✅\n"
            "All time: {yes_all}/{total_days} days ✅ ({pct_all}%)\n"
            "Current streak: {cur_streak} 🔥 | Record: {max_streak} 🏆"
        ),
        "tt": (
            "✅ *{title}* _(әйе/юк)_\n"
            "Атна: {yes_7}/{days_7} көн ✅\n"
            "Барлыгы: {yes_all}/{total_days} көн ✅ ({pct_all}%)\n"
            "Хәзерге серия: {cur_streak} 🔥 | Рекорд: {max_streak} 🏆"
        ),
    },

    # ── count ─────────────────────────────────────────────────────────────
    "stats_count_block": {
        "ru": (
            "🔢 *{title}* _(число)_\n"
            "За 7 дней: среднее {avg_7}, сумма {sum_7}\n"
            "За всё время: среднее {avg_all}, сумма {sum_all}, макс {max_val}\n"
            "Дней с ответом: {total_days}"
        ),
        "en": (
            "🔢 *{title}* _(number)_\n"
            "Last 7 days: avg {avg_7}, sum {sum_7}\n"
            "All time: avg {avg_all}, sum {sum_all}, max {max_val}\n"
            "Days answered: {total_days}"
        ),
        "tt": (
            "🔢 *{title}* _(сан)_\n"
            "7 көн: уртача {avg_7}, сумма {sum_7}\n"
            "Барлыгы: уртача {avg_all}, сумма {sum_all}, макс {max_val}\n"
            "Җавап биргән көннәр: {total_days}"
        ),
    },

    # ── scale_1_5 ─────────────────────────────────────────────────────────
    "stats_scale_block": {
        "ru": (
            "⭐ *{title}* _(шкала 1–5)_\n"
            "За 7 дней: среднее {avg_7}\n"
            "За всё время: среднее {avg_all}, макс {max_val}\n"
            "Оценки: {dist_str}\n"
            "Дней с ответом: {total_days}"
        ),
        "en": (
            "⭐ *{title}* _(scale 1–5)_\n"
            "Last 7 days: avg {avg_7}\n"
            "All time: avg {avg_all}, max {max_val}\n"
            "Scores: {dist_str}\n"
            "Days answered: {total_days}"
        ),
        "tt": (
            "⭐ *{title}* _(шкала 1–5)_\n"
            "7 көн: уртача {avg_7}\n"
            "Барлыгы: уртача {avg_all}, макс {max_val}\n"
            "Бәяләр: {dist_str}\n"
            "Дней с ответом: {total_days}"
        ),
    },

    # ── poll ──────────────────────────────────────────────────────────────
    "stats_poll_block": {
        "ru": (
            "📋 *{title}* _(варианты)_\n"
            "Всего ответов: {total}\n"
            "{dist_str}"
        ),
        "en": (
            "📋 *{title}* _(poll)_\n"
            "Total answers: {total}\n"
            "{dist_str}"
        ),
        "tt": (
            "📋 *{title}* _(вариантлар)_\n"
            "Барлыгы: {total}\n"
            "{dist_str}"
        ),
    },

    "stats_separator": {
        "ru": "\n",
        "en": "\n",
        "tt": "\n",
    },

    # ── Poll distribution row (admin detail + user stats) ─────────────────
    "poll_dist_row": {
        "ru": "  • {label}: {cnt}× ({pct}%)",
        "en": "  • {label}: {cnt}× ({pct}%)",
        "tt": "  • {label}: {cnt}× ({pct}%)",
    },

    # ── Admin challenge detail ─────────────────────────────────────────────
    "adm_detail_header": {
        "ru": "📊 *{title}* — подробная статистика\n",
        "en": "📊 *{title}* — detailed stats\n",
        "tt": "📊 *{title}* — тулы статистика\n",
    },
    "adm_detail_participants": {
        "ru": (
            "👥 Участники: *{active}* активных / {total} всего\n"
            "📬 Сегодня ответили: *{today}* ({rate}%)\n"
            "📅 За неделю: *{week}* уникальных\n"
        ),
        "en": (
            "👥 Participants: *{active}* active / {total} total\n"
            "📬 Answered today: *{today}* ({rate}%)\n"
            "📅 This week: *{week}* unique\n"
        ),
        "tt": (
            "👥 Катнашучылар: *{active}* актив / {total} барлыгы\n"
            "📬 Бүген: *{today}* ({rate}%)\n"
            "📅 Атна: *{week}* уникаль\n"
        ),
    },
    "adm_detail_yesno": {
        "ru": "✅ «Да» сегодня: *{today_pct}%* | за неделю: *{week_pct}%*\n",
        "en": "✅ «Yes» today: *{today_pct}%* | this week: *{week_pct}%*\n",
        "tt": "✅ «Әйе» бүген: *{today_pct}%* | атна: *{week_pct}%*\n",
    },
    "adm_detail_count": {
        "ru": (
            "📈 Среднее сегодня: *{avg_today}* | за неделю: *{avg_week}*\n"
            "🏆 Максимум за всё время: *{max_ever}*\n"
        ),
        "en": (
            "📈 Avg today: *{avg_today}* | this week: *{avg_week}*\n"
            "🏆 All-time max: *{max_ever}*\n"
        ),
        "tt": (
            "📈 Уртача бүген: *{avg_today}* | атна: *{avg_week}*\n"
            "🏆 Максимум: *{max_ever}*\n"
        ),
    },
    "adm_detail_poll_week_header": {
        "ru": "📋 За неделю:",
        "en": "📋 This week:",
        "tt": "📋 Атна:",
    },
    "adm_detail_daily_header": {
        "ru": "\n📆 *Последние 7 дней:*\n",
        "en": "\n📆 *Last 7 days:*\n",
        "tt": "\n📆 *Соңгы 7 көн:*\n",
    },
    "adm_detail_daily_row_yesno": {
        "ru": "`{day}` — {count} ответов, {yes_pct}% «да»",
        "en": "`{day}` — {count} answers, {yes_pct}% «yes»",
        "tt": "`{day}` — {count} җавап, {yes_pct}% «әйе»",
    },
    "adm_detail_daily_row_count": {
        "ru": "`{day}` — {count} ответов, среднее {avg_val}",
        "en": "`{day}` — {count} answers, avg {avg_val}",
        "tt": "`{day}` — {count} җавап, уртача {avg_val}",
    },
    "adm_detail_daily_row_plain": {
        "ru": "`{day}` — {count} ответов",
        "en": "`{day}` — {count} answers",
        "tt": "`{day}` — {count} җавап",
    },
    "adm_detail_top_header": {
        "ru": "\n🏅 *Топ участников:*\n",
        "en": "\n🏅 *Top participants:*\n",
        "tt": "\n🏅 *Иң яхшы катнашучылар:*\n",
    },
    "adm_detail_top_row": {
        "ru": "{pos}. {name} — {answers} дней, среднее {avg}",
        "en": "{pos}. {name} — {answers} days, avg {avg}",
        "tt": "{pos}. {name} — {answers} көн, уртача {avg}",
    },
    "adm_ch_btn_detail": {
        "ru": "📊 Детальная статистика",
        "en": "📊 Detailed Stats",
        "tt": "📊 Тулы статистика",
    },
    "adm_na": {
        "ru": "н/д",
        "en": "n/a",
        "tt": "юк",
    },

    # ── Admin stats: per-challenge link button ─────────────────────────────
    "adm_btn_ch_stats_link": {
        "ru": "🔍 {title}",
        "en": "🔍 {title}",
        "tt": "🔍 {title}",
    },

    # ── Admin challenge card (shown in challenge management view) ─────────────
    "adm_ch_card": {
        "ru": (
            "🧩 *{title}*\n_{description}_\n\n"
            "Slug: `{slug}`\n"
            "Тип: `{kind}`\n"
            "Время: `{schedule}`\n"
            "Длительность: {duration} дней\n"
            "Статус: {status}{launch}\n\n"
            "Вопрос: _{question}_"
        ),
        "en": (
            "🧩 *{title}*\n_{description}_\n\n"
            "Slug: `{slug}`\n"
            "Type: `{kind}`\n"
            "Time: `{schedule}`\n"
            "Duration: {duration} days\n"
            "Status: {status}{launch}\n\n"
            "Question: _{question}_"
        ),
        "tt": (
            "🧩 *{title}*\n_{description}_\n\n"
            "Slug: `{slug}`\n"
            "Төр: `{kind}`\n"
            "Вакыт: `{schedule}`\n"
            "Озынлыгы: {duration} көн\n"
            "Статус: {status}{launch}\n\n"
            "Сорау: _{question}_"
        ),
    },

    # ── Admin challenge card: launch date line ─────────────────────────────
    "adm_ch_launch_str": {
        "ru": "\nЗапуск: `{launch_at}`",
        "en": "\nLaunch: `{launch_at}`",
        "tt": "\nБашлану: `{launch_at}`",
    },

    # ── Challenges ─────────────────────────────────────────────────────────
    "challenges_header": {
        "ru": "🕌 *Активные челленджи:*\n",
        "en": "🕌 *Active challenges:*\n",
        "tt": "🕌 *Актив сынаулар:*\n",
    },
    "no_challenges": {
        "ru": "Нет активных челленджей.",
        "en": "No active challenges.",
        "tt": "Актив сынаулар юк.",
    },
    "joined_challenge": {
        "ru": "✅ Вы вступили в челлендж!",
        "en": "✅ You joined the challenge!",
        "tt": "✅ Сез сынауга кушылдыгыз!",
    },
    "already_participating": {
        "ru": "Вы уже участвуете.",
        "en": "You are already participating.",
        "tt": "Сез сынауда катнашасыз.",
    },
    "left_challenge": {
        "ru": "Вы вышли из челленджа.",
        "en": "You left the challenge.",
        "tt": "Сез сынаудар чыктыгыз.",
    },

    # ── Settings ───────────────────────────────────────────────────────────
    "settings_header": {
        "ru": "⚙️ *Настройки*\n\nЧасовой пояс: `{tz}`\nЯзык: {lang_label}\n\nОтправьте геолокацию для автоопределения таймзоны.\nИли введи вручную: `/timezone Europe/Moscow`",
        "en": "⚙️ *Settings*\n\nTimezone: `{tz}`\nLanguage: {lang_label}\n\nSend your location to detect timezone automatically.\nOr type manually: `/timezone Europe/Moscow`",
        "tt": "⚙️ *Көйләүләр*\n\nВакыт зонасы: `{tz}`\nТел: {lang_label}\n\nВакыт зонасын автоматик билгеләү өчен урыныгызны жибәрегез.\nЯки языгыз: `/timezone Europe/Moscow`",
    },
    "tz_invalid": {
        "ru": "❌ Неверная таймзона. Пример: `Europe/Moscow`",
        "en": "❌ Invalid timezone. Example: `Europe/Moscow`",
        "tt": "❌ Хаталы вакыт зонасы. Мисал: `Europe/Moscow`",
    },
    "tz_updated": {
        "ru": "✅ Часовой пояс обновлён: `{tz}`",
        "en": "✅ Timezone updated: `{tz}`",
        "tt": "✅ Вакыт зонасы яңартылды: `{tz}`",
    },
    "location_received": {
        "ru": "📍 Геолокация получена.\nЧасовой пояс определён: `{tz}`\n\nВопросы теперь будут приходить в нужное время.",
        "en": "📍 Location received.\nTimezone detected: `{tz}`\n\nYou will now receive questions at the right time.",
        "tt": "📍 Геолокация кабул булды.\nВакыт зонасы: `{tz}`\n\nСораулар дөрес вакытта килер.",
    },

    # ── Language selection ──────────────────────────────────────────────────
    "lang_select": {
        "ru": "🌐 Выберите язык интерфейса:",
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
        "tt": "✅ *{title}* сынауга «{value}» кабул ителде.",
    },
    "answer_toast": {
        "ru": "✅ Записано!",
        "en": "✅ Recorded!",
        "tt": "✅ Язылды!",
    },
    "already_answered": {
        "ru": "Вы уже ответили на этот вопрос сегодня.",
        "en": "You have already answered this question today.",
        "tt": "Сез бүген инде бу соруга җавап бирдегез.",
    },
    "challenge_not_found": {
        "ru": "Челлендж не найден.",
        "en": "Challenge not found.",
        "tt": "Сынау табылмады.",
    },

    # ── Count input ─────────────────────────────────────────────────────────
    "count_prompt": {
        "ru": "\n\n✏️ Введите число в ответ на это сообщение.",
        "en": "\n\n✏️ Reply to this message with a number.",
        "tt": "\n\n✏️ Бу хәбәргә сан белән җавап языгыз.",
    },
    "count_recorded": {
        "ru": "✅ Записано {count} для *{title}*.",
        "en": "✅ Recorded {count} for *{title}*.",
        "tt": "✅ *{title}* өчен {count} язылды.",
    },
    "count_already_answered": {
        "ru": "Вы уже ответили сегодня.",
        "en": "You have already answered today.",
        "tt": "Сез бүген инде җавап бирдегез.",
    },
    "count_multiple_pending": {
        "ru": "У вас несколько неотвеченных вопросов с числовым ответом. Ответьте через кнопку в нужном сообщении.\n\nОжидают:\n{list}",
        "en": "You have multiple count questions pending. Please reply via the button in the specific message.\n\nPending:\n{list}",
        "tt": "Сездә берничә җавапсыз сорау бар. Дөрес хәбәрдәге төймә аша җавап биреп карагыз.\n\nКөтеп тора:\n{list}",
    },

    # ── Challenge announcement ─────────────────────────────────────────────
    "challenge_announce": {
        "ru": (
            "🕌 *Новый челлендж: {title}*\n"
            "{description}\n\n"
            "Ежедневно в {time} на протяжении {days} дней вы будете получать вопросы по ходу челленджа\n\n"
            "Присоединяйтесь!"
        ),
        "en": (
            "🕌 *New Challenge: {title}*\n"
            "{description}\n\n"
            "Every day at {time} for {days} days, you will receive questions throughout the challenge.\n\n"
            "Join us!"
        ),
        "tt": (
            "🕌 *Яңа сынау: {title}*\n"
            "{description}\n\n"
            "Һәр көн {time} сәгатьтә, {days} көн дәвамында, сынау дәвамында сез сораулар алачаксыз.\n\n"
            "Кушылыгыз!"
        ),
    },
    "btn_join_challenge": {
        "ru": "✅ Участвовать",
        "en": "✅ Join Challenge",
        "tt": "✅ Катнашу",
    },
    "btn_join_challenge_list": {
        "ru": "➕ {title}",
        "en": "➕ {title}",
        "tt": "➕ {title}",
    },
    "btn_leave_challenge": {
        "ru": "⛔️ Выйти из «{title}»",
        "en": "⛔️ Leave «{title}»",
        "tt": "⛔️ «{title}» дән чыгу",
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
        "tt": "🧩 Сынаулар",
    },
    "adm_btn_stats": {
        "ru": "📊 Статистика",
        "en": "📊 Statistics",
        "tt": "📊 Статистика",
    },
    "adm_stats_header": {
        "ru": "👥 Всего пользователей: *{total}*\n🔥 Ответили сегодня: *{today}*\n\n📊 *Статистика по челленджам (сегодня):*",
        "en": "👥 Total users: *{total}*\n🔥 Active today: *{today}*\n\n📊 *Challenge statistics (today):*",
        "tt": "👥 Барлык кулланучылар: *{total}*\n🔥 Бүген актив: *{today}*\n\n📊 *Сынау статистикасы (бүген):*",
    },
    "adm_stats_row": {
        "ru": "\n• *{title}*\n  Ответили: {resp} | Среднее: {avg} | Макс: {max}",
        "en": "\n• *{title}*\n  Answered: {resp} | Avg: {avg} | Max: {max}",
        "tt": "\n• *{title}*\n  Җавап биргән: {resp} | Уртача: {avg} | Макс: {max}",
    },
    "adm_challenges_title": {
        "ru": "🧩 *Управление челленджами:*",
        "en": "🧩 *Challenge Management:*",
        "tt": "🧩 *Сынаулар белән идарә итү:*",
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
        "tt": "🔴 Деактивация",
    },
    "adm_ch_btn_activate": {
        "ru": "🟢 Активировать",
        "en": "🟢 Activate",
        "tt": "🟢 Активация",
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
        "tt": "➕ Сынау башларга",
    },
    "adm_ch_toggled_active": {
        "ru": "Челлендж активирован 🟢",
        "en": "Challenge activated 🟢",
        "tt": "Сынау башланды 🟢",
    },
    "adm_ch_toggled_inactive": {
        "ru": "Челлендж деактивирован 🔴",
        "en": "Challenge deactivated 🔴",
        "tt": "Сынау деактивлаштырылды 🔴",
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
        "ru": (
            "🆕 *Создание челленджа*\n\n"
            "Шаг 1 — введи *slug* (технический идентификатор).\n\n"
            "Slug — внутреннее имя для базы данных. Пользователи его *не видят*.\n\n"
            "Только a-z, 0-9, дефис. Пример: `daily-prayer`"
        ),
        "en": (
            "🆕 *Create Challenge*\n\n"
            "Step 1 — enter *slug* (technical identifier).\n\n"
            "Slug is the internal name. Users *never see it*.\n\n"
            "Only a-z, 0-9, hyphen. Example: `daily-prayer`"
        ),
        "tt": (
            "🆕 *Чәлленҗ булдыру*\n\n"
            "Адым 1 — *slug* языгыз (техник идентификатор).\n\n"
            "Slug — эчке исем, кулланучылар *күрми*.\n\n"
            "Тик a-z, 0-9, дефис. Мисал: `daily-prayer`"
        ),
    },
    "adm_wiz_slug_invalid": {
        "ru": "❌ Slug — только a-z, 0-9 и дефис.\nПример: `daily-prayer`",
        "en": "❌ Slug — only a-z, 0-9 and hyphen.\nExample: `daily-prayer`",
        "tt": "❌ Slug — тик a-z, 0-9 һәм дефис.\nМисал: `daily-prayer`",
    },
    "adm_wiz_slug_taken": {
        "ru": "❌ Этот slug уже занят. Придумайте другой:",
        "en": "❌ This slug is already taken. Try another:",
        "tt": "❌ Бу slug инде бар. Башкасын языгыз:",
    },
    "adm_wiz_title": {
        "ru": "Slug: `{slug}`\n\nШаг 2 — введите *название* на русском:",
        "en": "Slug: `{slug}`\n\nStep 2 — enter *title* in Russian:",
        "tt": "Slug: `{slug}`\n\nАдым 2 — рус телендә *исем* языгыз:",
    },
    "adm_wiz_description": {
        "ru": "Название: *{title}*\n\nШаг 3 — введите *описание* (необязательно):",
        "en": "Title: *{title}*\n\nStep 3 — enter *description* (optional):",
        "tt": "Исем: *{title}*\n\nАдым 3 — *тасвирлама* языгыз (узып китеп була):",
    },
    "adm_wiz_skip": {
        "ru": "⏭ Пропустить",
        "en": "⏭ Skip",
        "tt": "⏭ Китеп калдыру",
    },
    "adm_wiz_kind": {
        "ru": "Шаг 4 — выберите *тип вопроса*:",
        "en": "Step 4 — choose *question type*:",
        "tt": "Адым 4 — *сорау төрен* сайлагыз:",
    },
    "adm_wiz_question": {
        "ru": "Тип: *{kind}*\n\nШаг 5 — введите *текст вопроса* на русском:",
        "en": "Type: *{kind}*\n\nStep 5 — enter *question text* in Russian:",
        "tt": "Төр: *{kind}*\n\nАдым 5 — рус телендә *сорау тексты* языгыз:",
    },
    "adm_wiz_options": {
        "ru": (
            "Шаг 6 — введите *варианты ответа* (каждый с новой строки, минимум 2, максимум 10).\n\n"
            "Пример:\n`Всегда`\n`Иногда`\n`Редко`\n`Никогда`"
        ),
        "en": (
            "Step 6 — enter *answer options* (one per line, min 2, max 10).\n\n"
            "Example:\n`Always`\n`Sometimes`\n`Rarely`\n`Never`"
        ),
        "tt": (
            "Адым 6 — *вариантлар* языгыз (яңа юлдан, иң кимендә 2, максимум 10).\n\n"
            "Мисал:\n`Һәрвакыт`\n`Кайчак`\n`Сирәк`\n`Беркайчан`"
        ),
    },
    "adm_wiz_options_invalid": {
        "ru": "❌ Нужно минимум 2 варианта. Введите каждый с новой строки:",
        "en": "❌ At least 2 options required. Enter each on a new line:",
        "tt": "❌ Иң кимендә 2 вариант кирәк. Яңа юлдан языгыз:",
    },
    "adm_wiz_options_too_many": {
        "ru": "❌ Максимум 10 вариантов.",
        "en": "❌ Maximum 10 options.",
        "tt": "❌ Максимум 10 вариант.",
    },
    "adm_wiz_options_preview": {
        "ru": "Варианты ответа:",
        "en": "Answer options:",
        "tt": "Вариантлар:",
    },
    "adm_wiz_schedule": {
        "ru": "Время ежедневной отправки (ЧЧ:ММ, например `06:00`):",
        "en": "Daily send time (HH:MM, e.g. `06:00`):",
        "tt": "Көнлек жибәрү вакыты (СС:ДД, мәс. `06:00`):",
    },
    "adm_wiz_schedule_invalid": {
        "ru": "❌ Неверный формат. Введите ЧЧ:ММ, например `06:00`:",
        "en": "❌ Wrong format. Enter HH:MM, e.g. `06:00`:",
        "tt": "❌ Хаталы формат. СС:ДД языгыз, мәс. `06:00`:",
    },
    "adm_wiz_duration": {
        "ru": "Длительность в днях (например `40`):",
        "en": "Duration in days (e.g. `40`):",
        "tt": "Озынлыгы көннәрдә (мәс. `40`):",
    },
    "adm_wiz_duration_invalid": {
        "ru": "❌ Введи целое число от 1 до 3650.",
        "en": "❌ Enter a whole number from 1 to 3650.",
        "tt": "❌ 1 дән 3650 кадәр сан языгыз.",
    },
    "adm_wiz_launch": {
        "ru": "Когда запустить челлендж?\n\nНажмите *Прямо сейчас* или введите дату по Москве:\n`ГГГГ-ММ-ДД ЧЧ:ММ`",
        "en": "When to launch the challenge?\n\nTap *Right Now* or enter Moscow date:\n`YYYY-MM-DD HH:MM`",
        "tt": "Сынауны кайчан башларга?\n\n*Хәзер үк* дип басыгыз яки Мәскәү вакытын языгыз:\n`ГГГГ-АА-КК СС:ДД`",
    },
    "adm_wiz_launch_invalid": {
        "ru": "❌ Неверный формат. Пример: `2025-03-20 09:00`",
        "en": "❌ Wrong format. Example: `2025-03-20 09:00`",
        "tt": "❌ Хаталы формат. Мисал: `2025-03-20 09:00`",
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
            "📋 *Яңа сынау карашы:*\n\n"
            "Slug: `{slug}`\nИсем: {title}\nТасвирлама: {desc}\n"
            "Төр: {kind}\nСорау: _{question}_\n"
            "Вакыт: `{time}`\nОзынлыгы: {days} көн\n"
            "Башлану: {launch}\n\n"
            "Сынауны ясаргамы?"
        ),
    },
    "adm_wiz_review_now": {
        "ru": "сразу после создания",
        "en": "immediately after creation",
        "tt": "ясаганнан соң",
    },
    "adm_wiz_confirm_btn": {
        "ru": "✅ Создать",
        "en": "✅ Create",
        "tt": "✅ Башларга",
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
        "tt": "✅ Сынау *{title}* (`{slug}`) булдырылды!\nТөр: `{kind}` | Вакыт: `{time}` | Көннәр: {days}",
    },
    "adm_wiz_cancelled": {
        "ru": "Отменено",
        "en": "Cancelled",
        "tt": "Кире кайтарылды",
    },

    # ── Validation errors ────────────────────────────────────────────────────
    "err_title_len": {
        "ru": "❌ Длина названия: 2–80 символов.",
        "en": "❌ Title length: 2–80 characters.",
        "tt": "❌ Исем озынлыгы: 2–80 символ.",
    },
    "err_desc_len": {
        "ru": "❌ Описание: максимум 600 символов.",
        "en": "❌ Description: max 600 characters.",
        "tt": "❌ Тасвирлама: максимум 600 символ.",
    },
    "err_question_len": {
        "ru": "❌ Длина вопроса: 5–300 символов.",
        "en": "❌ Question length: 5–300 characters.",
        "tt": "❌ Сорау озынлыгы: 5–300 символ.",
    },

    # ── Edit-field menu labels ───────────────────────────────────────────────
    "adm_edit_menu_title": {
        "ru": "✏️ *Что редактируем?*",
        "en": "✏️ *What to edit?*",
        "tt": "✏️ *Нәрсәне үзгәртәбез?*",
    },
    "adm_edit_field_unknown": {
        "ru": "Неизвестное поле",
        "en": "Unknown field",
        "tt": "Билгесез урын",
    },
    "adm_field_slug": {
        "ru": "Slug",
        "en": "Slug",
        "tt": "Slug",
    },
    "adm_field_title": {
        "ru": "Название",
        "en": "Title",
        "tt": "Исем",
    },
    "adm_field_description": {
        "ru": "Описание",
        "en": "Description",
        "tt": "Тасвирлама",
    },
    "adm_field_kind": {
        "ru": "Тип",
        "en": "Type",
        "tt": "Төр",
    },
    "adm_field_question": {
        "ru": "Вопрос",
        "en": "Question",
        "tt": "Сорау",
    },
    "adm_field_options": {
        "ru": "Варианты ответа",
        "en": "Answer Options",
        "tt": "Вариантлар",
    },
    "adm_field_schedule": {
        "ru": "Время",
        "en": "Time",
        "tt": "Вакыт",
    },
    "adm_field_duration": {
        "ru": "Длительность",
        "en": "Duration",
        "tt": "Озынлыгы",
    },

    # ── Broadcast ───────────────────────────────────────────────────────────
    "adm_broadcast_prompt": {
        "ru": "📣 *Рассылка*\n\nВведи текст сообщения (поддерживается Markdown):",
        "en": "📣 *Broadcast*\n\nEnter message text (Markdown supported):",
        "tt": "📣 *Рассылка*\n\nХәбәр текстын языгыз (Markdown):",
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
        "tt": "🌐 *{lang_name}* теленә тәрҗемә\n\nАдым 2/2 — *сорау текстын* языгыз:",
    },
    "adm_tr_saved": {
        "ru": "✅ Перевод на *{lang_name}* сохранён.",
        "en": "✅ Translation to *{lang_name}* saved.",
        "tt": "✅ *{lang_name}* теленә тәрҗемә сакланды.",
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