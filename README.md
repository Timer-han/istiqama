# Истикама — трекер исламских привычек 🌙

MVP Telegram-бота для ежедневных исламских челленджей.

## Стек

- **Python 3.11+**
- **aiogram 3.x** (long-polling)
- **PostgreSQL 16** + **asyncpg**
- **Docker Compose**

---

## Быстрый старт

### 1. Клонируй / распакуй проект

```bash
cd istiqama
```

### 2. Создай `.env`

```bash
cp .env.example .env
# Открой .env и заполни BOT_TOKEN и ADMIN_IDS
```

### 3. Запусти

```bash
docker compose up --build
```

Бот стартует, PostgreSQL инициализируется автоматически через `sql/init.sql`.

---

## Переменные окружения

| Переменная          | Описание                                         | Дефолт                                           |
|---------------------|--------------------------------------------------|--------------------------------------------------|
| `BOT_TOKEN`         | Токен бота от @BotFather                        | **обязательно**                                  |
| `ADMIN_IDS`         | Telegram ID администраторов через запятую        | `""` (пусто)                                     |
| `DATABASE_URL`      | DSN PostgreSQL                                   | `postgresql://istiqama:istiqama@db:5432/istiqama` |
| `SCHEDULER_INTERVAL`| Интервал планировщика в секундах                | `60`                                             |

---

## Архитектура

```
bot/
  main.py            – точка входа, запуск polling и bg-задач
  config.py          – конфигурация из env
  handlers.py        – пользовательские хэндлеры
  admin_handlers.py  – хэндлеры панели администратора (FSM)
  keyboards.py       – все клавиатуры
  states.py          – FSM-состояния
  utils.py           – вспомогательные функции

services/
  db.py              – бизнес-логика работы с БД
  scheduler.py       – ежеминутная рассылка вопросов + авто-кик
  aggregator.py      – инкрементальная агрегация статистики
  outbox.py          – отправка рассылок с rate-limit

adapters/
  storage_postgres.py – asyncpg-пул и базовые хелперы

sql/
  init.sql           – DDL: таблицы, партиции, индексы
```

### Фоновые задачи (в одном процессе, asyncio)

| Задача          | Частота  | Что делает                                        |
|-----------------|----------|---------------------------------------------------|
| `scheduler_task`| 60 сек   | Отправляет вопросы по расписанию, кикает неактивных |
| `aggregator_task`| 30 сек  | Агрегирует events → daily_challenge_stats          |
| `outbox_task`   | 5 сек    | Рассылает admin-сообщения (~20 msg/s)              |

---

## Типы челленджей

| Тип         | Ответ                    | UI                       |
|-------------|--------------------------|--------------------------|
| `yes_no`    | Да / Нет                 | 2 inline-кнопки          |
| `scale_1_5` | Оценка 1–5               | 5 inline-кнопок          |
| `poll`      | Вариант из metadata      | N inline-кнопок          |
| `count`     | Произвольное число       | Текстовый ввод числа     |

---

## Пользовательское меню

```
📊 Моя статистика   🕌 Челленджи   ⚙️ Настройки
```

Администраторы видят дополнительную кнопку:
```
🛠 Панель админа
```

### Панель администратора

- **📣 Рассылка** — отправить сообщение всем пользователям
- **🧩 Челленджи** — создать / редактировать / удалить / вкл/выкл
- **📊 Статистика** — сводка по участникам и челленджам

---

## Автокик за неактивность

Если участник **не отвечал 3 дня подряд**, планировщик автоматически устанавливает `challenge_participants.active = FALSE`. Пользователь может снова вступить в челлендж вручную.

---

## Локализация

Тексты челленджа хранятся в `challenges.metadata.translations`:

```json
{
  "translations": {
    "ru": { "title": "...", "question": "...", "options": [] },
    "en": { "title": "...", "question": "...", "options": [] }
  },
  "schedule_time": "06:00",
  "duration_days": 40
}
```

Если перевод для языка не найден — используется `ru`.

---

## Переход на webhook (в будущем)

Вся логика инкапсулирована в `Dispatcher`. Для перехода на webhook достаточно заменить в `main.py`:

```python
# Вместо dp.start_polling(...)
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web
# ... настройка aiohttp + bot.set_webhook(...)
```

Никаких изменений в handlers, services или adapters не требуется.

---

## Разработка без Docker

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Запусти PostgreSQL локально, примени DDL:
psql -U postgres -c "CREATE DATABASE istiqama;"
psql -U postgres -d istiqama -f sql/init.sql

export BOT_TOKEN=...
export ADMIN_IDS=...
export DATABASE_URL=postgresql://postgres:postgres@localhost:5432/istiqama

python -m bot.main
```
