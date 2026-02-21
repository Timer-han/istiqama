"""services/db.py – business-level DB operations."""
from __future__ import annotations

import json
from datetime import date, datetime, timedelta
from typing import Optional, List

import pytz
from asyncpg import Record

from adapters.storage_postgres import fetch, fetchrow, execute, get_pool


# ─────────────────────────── HELPERS ──────────────────────────────────────


def local_day_for_tz(tz_str: str) -> date:
    """Current calendar date in the given timezone."""
    tz = pytz.timezone(tz_str)
    return datetime.now(tz).date()


def next_dispatch_ts(schedule_time_str: str, tz_str: str) -> datetime:
    """
    Return the next UTC datetime when schedule_time fires in user's timezone.
    If the scheduled minute hasn't passed today → use today.
    Otherwise → tomorrow at the same time.
    """
    try:
        h, m = map(int, schedule_time_str.split(":"))
    except Exception:
        h, m = 6, 0

    tz = pytz.timezone(tz_str)
    now_local = datetime.now(tz)
    candidate = now_local.replace(hour=h, minute=m, second=0, microsecond=0)
    if candidate <= now_local:
        candidate += timedelta(days=1)
    # Return as UTC-aware datetime (asyncpg handles TIMESTAMPTZ fine)
    return candidate.astimezone(pytz.UTC)


# ─────────────────────────── USERS ────────────────────────────────────────


async def get_or_create_user(
    telegram_id: int,
    username: Optional[str],
    display_name: Optional[str],
    tz: str = "UTC",
) -> Record:
    row = await fetchrow("SELECT * FROM users WHERE telegram_id=$1", telegram_id)
    if row:
        return row
    return await fetchrow(
        """
        INSERT INTO users (telegram_id, username, display_name, timezone)
        VALUES ($1, $2, $3, $4)
        RETURNING *
        """,
        telegram_id, username, display_name, tz,
    )


async def get_user_by_telegram_id(telegram_id: int) -> Optional[Record]:
    return await fetchrow("SELECT * FROM users WHERE telegram_id=$1", telegram_id)


async def update_user_timezone(user_id: int, tz: str) -> None:
    await execute("UPDATE users SET timezone=$1 WHERE id=$2", tz, user_id)


async def update_user_lang(user_id: int, lang: str) -> None:
    await execute("UPDATE users SET lang=$1 WHERE id=$2", lang, user_id)


async def update_user_location(
    user_id: int, lat: float, lon: float, tz: str,
    country: str = None, city: str = None,
) -> None:
    await execute(
        "UPDATE users SET lat=$1, lon=$2, timezone=$3, country=$4, city=$5 WHERE id=$6",
        lat, lon, tz, country, city, user_id,
    )


# ─────────────────────────── CHALLENGES ───────────────────────────────────


async def get_active_challenges() -> List[Record]:
    return await fetch("SELECT * FROM challenges WHERE active=TRUE ORDER BY id")


async def fetch_all_challenges() -> List[Record]:
    return await fetch("SELECT * FROM challenges ORDER BY id")


async def get_challenge_by_id(challenge_id: int) -> Optional[Record]:
    return await fetchrow("SELECT * FROM challenges WHERE id=$1", challenge_id)


async def get_challenge_by_slug(slug: str) -> Optional[Record]:
    return await fetchrow("SELECT * FROM challenges WHERE slug=$1", slug)


async def create_challenge(slug: str, kind: str, metadata: dict) -> Record:
    return await fetchrow(
        """
        INSERT INTO challenges (slug, kind, metadata)
        VALUES ($1, $2, $3)
        RETURNING *
        """,
        slug, kind, json.dumps(metadata),
    )


async def update_challenge(challenge_id: int, **kwargs) -> None:
    sets = ", ".join(f"{k}=${i+2}" for i, k in enumerate(kwargs))
    await execute(
        f"UPDATE challenges SET {sets} WHERE id=$1",
        challenge_id, *kwargs.values(),
    )


async def update_challenge_translation(
    challenge_id: int,
    lang: str,
    title: str,
    question: str,
    description: str = "",
    options: list | None = None,
) -> None:
    """Добавить или заменить перевод для указанного языка в metadata.translations."""
    row = await fetchrow("SELECT metadata FROM challenges WHERE id=$1", challenge_id)
    if not row:
        return
    meta = row["metadata"]
    if isinstance(meta, str):
        import json as _json
        meta = _json.loads(meta)
    meta.setdefault("translations", {})[lang] = {
        "title":       title,
        "description": description,
        "question":    question,
        "options":     options or [],
    }
    await execute(
        "UPDATE challenges SET metadata=$1 WHERE id=$2",
        json.dumps(meta), challenge_id,
    )


async def toggle_challenge_active(challenge_id: int, active: bool) -> None:
    await execute("UPDATE challenges SET active=$1 WHERE id=$2", active, challenge_id)


async def delete_challenge(challenge_id: int) -> None:
    await execute("DELETE FROM challenges WHERE id=$1", challenge_id)


async def deactivate_expired_challenges() -> int:
    """
    Деактивирует челленджи, у которых истёк срок (duration_days).
    Срок считается от created_at: ends_at = created_at + duration_days * '1 day'.

    Возвращает количество деактивированных челленджей.
    Вызывается из scheduler каждый тик.
    """
    result = await execute(
        """
        UPDATE challenges
        SET active = FALSE
        WHERE active = TRUE
          AND (metadata->>'duration_days') IS NOT NULL
          AND (metadata->>'duration_days')::int > 0
          AND created_at + ((metadata->>'duration_days')::int * INTERVAL '1 day') < NOW()
        """
    )
    count = int(result.split()[-1]) if result else 0
    return count


# ─────────────────────────── PARTICIPANTS ─────────────────────────────────


async def join_challenge(user_id: int, challenge_id: int, user_tz: str = "UTC") -> bool:
    """
    Вступить в челлендж.
    Вычисляет next_dispatch_at = следующий момент schedule_time в таймзоне пользователя.
    Возвращает True если участник добавлен/реактивирован.
    """
    challenge = await get_challenge_by_id(challenge_id)
    if not challenge:
        return False

    meta = challenge["metadata"]
    if isinstance(meta, str):
        meta = json.loads(meta)
    schedule_time = meta.get("schedule_time", "06:00")
    next_ts = next_dispatch_ts(schedule_time, user_tz)

    existing = await fetchrow(
        "SELECT active FROM challenge_participants WHERE user_id=$1 AND challenge_id=$2",
        user_id, challenge_id,
    )

    if existing is None:
        await execute(
            """
            INSERT INTO challenge_participants
                (user_id, challenge_id, next_dispatch_at)
            VALUES ($1, $2, $3)
            """,
            user_id, challenge_id, next_ts,
        )
        return True

    if not existing["active"]:
        # Реактивация: сбрасываем joined_at, next_dispatch_at, сохраняем last_answer_day
        await execute(
            """
            UPDATE challenge_participants
            SET active = TRUE,
                joined_at = NOW(),
                next_dispatch_at = $3
            WHERE user_id=$1 AND challenge_id=$2
            """,
            user_id, challenge_id, next_ts,
        )
        return True

    return False  # уже активен


async def leave_challenge(user_id: int, challenge_id: int) -> None:
    await execute(
        "UPDATE challenge_participants SET active=FALSE WHERE user_id=$1 AND challenge_id=$2",
        user_id, challenge_id,
    )


async def get_user_challenges(user_id: int) -> List[Record]:
    """Список всех активных челленджей с флагом участия текущего пользователя."""
    return await fetch(
        """
        SELECT c.*, cp.active AS participating
        FROM challenges c
        LEFT JOIN challenge_participants cp
               ON cp.challenge_id = c.id AND cp.user_id = $1
        WHERE c.active = TRUE
        ORDER BY c.id
        """,
        user_id,
    )


async def get_active_participants(challenge_id: int) -> List[Record]:
    """Для статистики и рассылок — не для scheduler."""
    return await fetch(
        """
        SELECT u.*
        FROM users u
        JOIN challenge_participants cp ON cp.user_id = u.id
        WHERE cp.challenge_id = $1 AND cp.active = TRUE
        """,
        challenge_id,
    )


async def deactivate_expired_challenges() -> int:
    """
    Деактивировать челленджи, у которых истёк срок (duration_days).
    Считаем от created_at. Возвращает количество деактивированных.
    """
    result = await execute(
        """
        UPDATE challenges
        SET active = FALSE
        WHERE active = TRUE
          AND (metadata->>'duration_days')::int IS NOT NULL
          AND created_at + ((metadata->>'duration_days')::int || ' days')::INTERVAL < NOW()
        """
    )
    return int(result.split()[-1]) if result else 0


async def get_due_participants(limit: int = 500) -> List[Record]:
    """
    Scheduler hotpath: один запрос вместо двойного цикла challenge→user.

    Возвращает строки с полями:
      user.*,
      cp.challenge_id,
      cp.joined_at       AS cp_joined_at,
      cp.last_answer_day AS cp_last_answer_day,
      cp.next_dispatch_at,
      c.slug, c.kind, c.metadata

    Условие: cp.active=TRUE AND c.active=TRUE AND cp.next_dispatch_at <= NOW()

    Ограничение LIMIT защищает от случая, когда после долгого простоя
    накапливается много строк (например после рестарта сервера).
    Одна итерация scheduler обрабатывает не более `limit` участников.
    """
    return await fetch(
        """
        SELECT
            u.id              AS user_id,
            u.telegram_id,
            u.timezone,
            u.lang,
            u.display_name,
            cp.challenge_id,
            cp.joined_at      AS cp_joined_at,
            cp.last_answer_day,
            cp.last_dispatch_day,
            cp.next_dispatch_at,
            c.slug,
            c.kind,
            c.metadata
        FROM challenge_participants cp
        JOIN users      u ON u.id = cp.user_id
        JOIN challenges c ON c.id = cp.challenge_id
        WHERE cp.active       = TRUE
          AND c.active        = TRUE
          AND cp.next_dispatch_at <= NOW()
        ORDER BY cp.next_dispatch_at
        LIMIT $1
        """,
        limit,
    )


async def set_participant_inactive(user_id: int, challenge_id: int) -> None:
    """Авто-кик за неактивность."""
    await execute(
        "UPDATE challenge_participants SET active=FALSE WHERE user_id=$1 AND challenge_id=$2",
        user_id, challenge_id,
    )


async def update_after_dispatch(
    user_id: int,
    challenge_id: int,
    local_day: date,
    next_ts: datetime,
) -> None:
    """
    После успешной отправки вопроса:
      - last_dispatch_day = сегодня в таймзоне пользователя
      - next_dispatch_at  = завтра в schedule_time (UTC)
    """
    await execute(
        """
        UPDATE challenge_participants
        SET last_dispatch_day = $3,
            next_dispatch_at  = $4
        WHERE user_id=$1 AND challenge_id=$2
        """,
        user_id, challenge_id, local_day, next_ts,
    )


async def set_next_dispatch_at(
    user_id: int, challenge_id: int, ts: datetime
) -> None:
    """Обновить только next_dispatch_at (используется при реактивации)."""
    await execute(
        "UPDATE challenge_participants SET next_dispatch_at=$3 WHERE user_id=$1 AND challenge_id=$2",
        user_id, challenge_id, ts,
    )


async def refresh_dispatch_times_for_user(user_id: int, tz_str: str) -> None:
    """
    После смены таймзоны пересчитать next_dispatch_at для всех активных участий.
    Вызывается когда пользователь обновил геолокацию / таймзону.
    """
    participants = await fetch(
        """
        SELECT cp.challenge_id, c.metadata
        FROM challenge_participants cp
        JOIN challenges c ON c.id = cp.challenge_id
        WHERE cp.user_id = $1 AND cp.active = TRUE
        """,
        user_id,
    )
    for p in participants:
        meta = p["metadata"]
        if isinstance(meta, str):
            meta = json.loads(meta)
        schedule_time = meta.get("schedule_time", "06:00")
        next_ts = next_dispatch_ts(schedule_time, tz_str)
        await execute(
            "UPDATE challenge_participants SET next_dispatch_at=$3 WHERE user_id=$1 AND challenge_id=$2",
            user_id, p["challenge_id"], next_ts,
        )


# ─────────────────────────── EVENTS ───────────────────────────────────────


async def record_event(
    user_id: int,
    challenge_id: int,
    tz_str: str,
    payload: dict,
) -> Optional[Record]:
    """
    Атомарно:
      1. INSERT event (иммутабельный лог)
      2. UPDATE challenge_participants.last_answer_day = local_day

    Возвращает вставленную строку events, или None если уже отвечал сегодня
    (уникальный индекс по user_id+challenge_id+local_day нарушен).
    """
    today = local_day_for_tz(tz_str)
    async with get_pool().acquire() as con:
        async with con.transaction():
            try:
                row = await con.fetchrow(
                    """
                    INSERT INTO events (user_id, challenge_id, local_day, payload)
                    VALUES ($1, $2, $3, $4)
                    RETURNING *
                    """,
                    user_id, challenge_id, today, json.dumps(payload),
                )
            except Exception:
                # Дубль: unique violation на (user_id, challenge_id, local_day)
                return None

            # Обновляем last_answer_day только если новый ответ позже текущего
            await con.execute(
                """
                UPDATE challenge_participants
                SET last_answer_day = $3
                WHERE user_id = $1
                  AND challenge_id = $2
                  AND (last_answer_day IS NULL OR last_answer_day < $3)
                """,
                user_id, challenge_id, today,
            )
            return row


async def get_pending_count_challenges(user_id: int, tz_str: str) -> List[Record]:
    """
    Все count-челленджи, вопрос по которым уже отправлен сегодня (last_dispatch_day = today),
    но ответа ещё нет (last_answer_day < today или NULL).

    Возвращает список, чтобы хендлер мог определить — один ли челлендж ждёт ответа,
    или несколько (и попросить выбрать).
    """
    today = local_day_for_tz(tz_str)
    return await fetch(
        """
        SELECT cp.challenge_id, c.slug, c.metadata
        FROM challenge_participants cp
        JOIN challenges c ON c.id = cp.challenge_id
        WHERE cp.user_id = $1
          AND c.kind = 'count'
          AND cp.active = TRUE
          AND cp.last_dispatch_day = $2
          AND (cp.last_answer_day IS NULL OR cp.last_answer_day < $2)
        ORDER BY cp.challenge_id
        """,
        user_id, today,
    )


async def get_user_stats_today(user_id: int) -> List[Record]:
    user = await fetchrow("SELECT timezone FROM users WHERE id=$1", user_id)
    if not user:
        return []
    today = local_day_for_tz(user["timezone"])
    return await fetch(
        """
        SELECT c.slug, c.metadata, e.payload, e.local_day
        FROM events e
        JOIN challenges c ON c.id = e.challenge_id
        WHERE e.user_id = $1 AND e.local_day = $2
        ORDER BY e.event_ts DESC
        """,
        user_id, today,
    )


async def get_user_stats_days(user_id: int, days: int = 7) -> List[Record]:
    # Cast days to int explicitly; INTERVAL '1 day' * $2 is safe with asyncpg
    return await fetch(
        """
        SELECT e.challenge_id, e.local_day, e.payload,
               c.slug, c.metadata
        FROM events e
        JOIN challenges c ON c.id = e.challenge_id
        WHERE e.user_id = $1
          AND e.event_ts >= NOW() - INTERVAL '1 day' * $2
        ORDER BY e.local_day DESC, e.challenge_id
        """,
        user_id, days,
    )


# ─────────────────────────── STATS ────────────────────────────────────────


async def get_challenge_stats(challenge_id: int, day: date) -> Optional[Record]:
    return await fetchrow(
        "SELECT * FROM daily_challenge_stats WHERE challenge_id=$1 AND day=$2",
        challenge_id, day,
    )


async def get_admin_stats() -> dict:
    total = await fetchrow("SELECT COUNT(*) AS n FROM users")
    # Активных сегодня = у кого last_answer_day = today по их таймзоне.
    # Быстрое приближение: ответили за последние 24h (используем daily_challenge_stats).
    active_today = await fetchrow(
        """
        SELECT COALESCE(SUM(total_responses), 0) AS n
        FROM daily_challenge_stats
        WHERE day = CURRENT_DATE
        """
    )
    challenges = await fetch(
        """
        SELECT c.id, c.slug, c.metadata,
               COALESCE(s.total_responses, 0) AS responses,
               COALESCE(s.sum_counts,      0) AS sum_counts,
               COALESCE(s.max_count,       0) AS max_count
        FROM challenges c
        LEFT JOIN daily_challenge_stats s
               ON s.challenge_id = c.id AND s.day = CURRENT_DATE
        WHERE c.active = TRUE
        ORDER BY c.id
        """
    )
    return {
        "total_users": total["n"],
        "active_today": active_today["n"],
        "challenges": challenges,
    }


# ─────────────────────────── OUTBOX ───────────────────────────────────────


async def create_outbox_message(text: str, target: str = "all") -> Record:
    return await fetchrow(
        "INSERT INTO outbox_messages (text, target) VALUES ($1,$2) RETURNING *",
        text, target,
    )


async def get_pending_outbox(limit: int = 50) -> List[Record]:
    return await fetch(
        """
        SELECT * FROM outbox_messages
        WHERE status = 'pending'
          AND (scheduled_at IS NULL OR scheduled_at <= NOW())
        ORDER BY id
        LIMIT $1
        FOR UPDATE SKIP LOCKED
        """,
        limit,
    )


async def mark_outbox_sending(msg_id: int) -> None:
    await execute("UPDATE outbox_messages SET status='sending' WHERE id=$1", msg_id)


async def mark_outbox_sent(msg_id: int) -> None:
    await execute(
        "UPDATE outbox_messages SET status='sent', sent_at=NOW() WHERE id=$1", msg_id
    )


async def mark_outbox_failed(msg_id: int) -> None:
    await execute("UPDATE outbox_messages SET status='failed' WHERE id=$1", msg_id)


# ─────────────────────────── ANNOUNCEMENTS ────────────────────────────────


async def get_unannounced_challenges() -> List[Record]:
    """
    Челленджи, у которых:
      - active = TRUE
      - metadata.announced = false (или ключ отсутствует)
      - launch_at <= NOW() (или launch_at отсутствует/null → сразу)
    """
    return await fetch(
        """
        SELECT *
        FROM challenges
        WHERE active = TRUE
          AND (
              (metadata->>'announced') IS DISTINCT FROM 'true'
          )
          AND (
              metadata->>'launch_at' IS NULL
              OR (metadata->>'launch_at')::TIMESTAMPTZ <= NOW()
          )
        ORDER BY created_at
        """
    )


async def mark_challenge_announced(challenge_id: int) -> None:
    """Set metadata.announced = true so we don't send again."""
    row = await fetchrow("SELECT metadata FROM challenges WHERE id=$1", challenge_id)
    if not row:
        return
    meta = row["metadata"]
    if isinstance(meta, str):
        meta = json.loads(meta)
    meta["announced"] = True
    await execute(
        "UPDATE challenges SET metadata=$1 WHERE id=$2",
        json.dumps(meta), challenge_id,
    )


async def get_all_active_telegram_ids() -> List[int]:
    """All users who have at least one active challenge participation."""
    rows = await fetch(
        """
        SELECT DISTINCT u.telegram_id
        FROM users u
        JOIN challenge_participants cp ON cp.user_id = u.id
        WHERE cp.active = TRUE
        """
    )
    return [r["telegram_id"] for r in rows]


async def get_all_telegram_ids() -> List[int]:
    """All registered users."""
    rows = await fetch("SELECT telegram_id FROM users ORDER BY id")
    return [r["telegram_id"] for r in rows]
