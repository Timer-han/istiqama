"""services/db.py – business-level DB operations."""
from __future__ import annotations

import json
from datetime import date, datetime, timedelta
from typing import Optional, List, Any

import pytz
from asyncpg import Record
from asyncpg.exceptions import UniqueViolationError

from adapters.storage_postgres import fetch, fetchrow, execute, get_pool
from constants import (
    SCHEDULE_TIME_FALLBACK,
    DB_DUE_PARTICIPANTS_LIMIT,
    DB_PENDING_OUTBOX_LIMIT,
    DB_STATS_WEEK_DAYS,
    DB_TOP_USERS_LIMIT,
    DB_PARTITION_MONTHS_AHEAD,
)


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
        h, m = map(int, SCHEDULE_TIME_FALLBACK.split(":"))

    tz = pytz.timezone(tz_str)
    now_local = datetime.now(tz)
    candidate = now_local.replace(hour=h, minute=m, second=0, microsecond=0)
    if candidate <= now_local:
        candidate += timedelta(days=1)
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


# ─────────────────────────── PARTICIPANTS ─────────────────────────────────


async def join_challenge(user_id: int, challenge_id: int, user_tz: str = "UTC") -> bool:
    challenge = await get_challenge_by_id(challenge_id)
    if not challenge:
        return False

    meta = challenge["metadata"]
    if isinstance(meta, str):
        meta = json.loads(meta)
    schedule_time = meta.get("schedule_time", SCHEDULE_TIME_FALLBACK)
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

    return False


async def leave_challenge(user_id: int, challenge_id: int) -> None:
    await execute(
        "UPDATE challenge_participants SET active=FALSE WHERE user_id=$1 AND challenge_id=$2",
        user_id, challenge_id,
    )


async def get_user_challenges(user_id: int) -> List[Record]:
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


async def get_active_participants_for_challenge(challenge_id: int) -> List[Record]:
    return await fetch(
        """
        SELECT u.*
        FROM users u
        JOIN challenge_participants cp ON cp.user_id = u.id
        WHERE cp.challenge_id = $1 AND cp.active = TRUE
        """,
        challenge_id,
    )


async def get_active_participations_for_user(user_id: int) -> List[Record]:
    """All challenges the user is currently active in, with metadata."""
    return await fetch(
        """
        SELECT cp.challenge_id, c.slug, c.kind, c.metadata
        FROM challenge_participants cp
        JOIN challenges c ON c.id = cp.challenge_id
        WHERE cp.user_id = $1 AND cp.active = TRUE
        ORDER BY c.id
        """,
        user_id,
    )


async def deactivate_expired_challenges() -> int:
    result = await execute(
        r"""
        UPDATE challenges
        SET active = FALSE
        WHERE active = TRUE
          AND (metadata->>'duration_days') IS NOT NULL
          AND (metadata->>'duration_days') ~ '^\d+$'
          AND created_at + ((metadata->>'duration_days')::int * INTERVAL '1 day') < NOW()
        """
    )
    return int(result.split()[-1]) if result else 0


async def get_due_participants(limit: int = DB_DUE_PARTICIPANTS_LIMIT) -> List[Record]:
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
    await execute(
        "UPDATE challenge_participants SET next_dispatch_at=$3 WHERE user_id=$1 AND challenge_id=$2",
        user_id, challenge_id, ts,
    )


async def refresh_dispatch_times_for_user(user_id: int, tz_str: str) -> None:
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
        schedule_time = meta.get("schedule_time", SCHEDULE_TIME_FALLBACK)
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
            except UniqueViolationError:
                return None

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


# ─────────────────────────── STATS ────────────────────────────────────────


async def get_challenge_stats(challenge_id: int, day: date) -> Optional[Record]:
    return await fetchrow(
        "SELECT * FROM daily_challenge_stats WHERE challenge_id=$1 AND day=$2",
        challenge_id, day,
    )


async def get_admin_stats() -> dict:
    total = await fetchrow("SELECT COUNT(*) AS n FROM users")
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


async def get_pending_outbox(limit: int = DB_PENDING_OUTBOX_LIMIT) -> List[Record]:
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
    rows = await fetch("SELECT telegram_id FROM users ORDER BY id")
    return [r["telegram_id"] for r in rows]


# ─── QUEUE ─────────────────────────────────────────────────────────────────


async def clear_stale_queue(user_id: int, today: date) -> None:
    await execute(
        "DELETE FROM user_question_queue WHERE user_id = $1 AND queued_for_day < $2",
        user_id, today,
    )


async def enqueue_question(
    user_id: int,
    challenge_id: int,
    day: date,
    schedule_time: str,
    position: int,
    next_dispatch_ts: datetime,
) -> None:
    async with get_pool().acquire() as con:
        async with con.transaction():
            await con.execute(
                """
                INSERT INTO user_question_queue
                    (user_id, challenge_id, queued_for_day, schedule_time, position)
                VALUES ($1, $2, $3, $4, $5)
                ON CONFLICT (user_id, challenge_id, queued_for_day) DO NOTHING
                """,
                user_id, challenge_id, day, schedule_time, position,
            )
            await con.execute(
                """
                UPDATE challenge_participants
                SET next_dispatch_at = $3
                WHERE user_id = $1 AND challenge_id = $2
                """,
                user_id, challenge_id, next_dispatch_ts,
            )


async def has_unanswered_in_batch(
    user_id: int, day: date, schedule_time: str
) -> bool:
    row = await fetchrow(
        """
        SELECT 1
        FROM user_question_queue
        WHERE user_id        = $1
          AND queued_for_day = $2
          AND schedule_time  = $3
          AND sent_at        IS NOT NULL
          AND answered_at    IS NULL
        LIMIT 1
        """,
        user_id, day, schedule_time,
    )
    return row is not None


async def has_any_unanswered_today(user_id: int, day: date) -> bool:
    row = await fetchrow(
        """
        SELECT 1
        FROM user_question_queue
        WHERE user_id        = $1
          AND queued_for_day = $2
          AND sent_at        IS NOT NULL
          AND answered_at    IS NULL
        LIMIT 1
        """,
        user_id, day,
    )
    return row is not None


async def get_next_unsent(
    user_id: int, day: date, schedule_time: str
) -> Optional[object]:
    return await fetchrow(
        """
        SELECT q.id           AS queue_id,
               q.challenge_id,
               q.schedule_time,
               q.queued_for_day,
               c.slug,
               c.kind,
               c.metadata
        FROM user_question_queue q
        JOIN challenges c ON c.id = q.challenge_id
        WHERE q.user_id        = $1
          AND q.queued_for_day = $2
          AND q.schedule_time  = $3
          AND q.sent_at        IS NULL
        ORDER BY q.position ASC
        LIMIT 1
        """,
        user_id, day, schedule_time,
    )


async def get_next_after_answer(
    user_id: int, answered_challenge_id: int, today: date, tz_str: str = "UTC"
) -> Optional[object]:
    entry = await fetchrow(
        """
        SELECT 1
        FROM user_question_queue
        WHERE user_id        = $1
          AND challenge_id   = $2
          AND queued_for_day = $3
        """,
        user_id, answered_challenge_id, today,
    )
    if not entry:
        return None

    import pytz as _pytz
    try:
        _tz = _pytz.timezone(tz_str)
    except Exception:
        _tz = _pytz.UTC
    current_hhmm = datetime.now(_tz).strftime("%H:%M")

    return await fetchrow(
        """
        SELECT q.id           AS queue_id,
               q.challenge_id,
               q.schedule_time,
               q.queued_for_day,
               c.slug,
               c.kind,
               c.metadata
        FROM user_question_queue q
        JOIN challenges c ON c.id = q.challenge_id
        WHERE q.user_id        = $1
          AND q.queued_for_day = $2
          AND q.sent_at        IS NULL
          AND q.schedule_time  <= $3
        ORDER BY q.schedule_time ASC, q.position ASC
        LIMIT 1
        """,
        user_id, today, current_hhmm,
    )


async def mark_queue_sent(queue_id: int) -> None:
    await execute(
        "UPDATE user_question_queue SET sent_at = NOW() WHERE id = $1",
        queue_id,
    )


async def mark_queue_answered(
    user_id: int, challenge_id: int, today: date
) -> None:
    await execute(
        """
        UPDATE user_question_queue
        SET answered_at = NOW()
        WHERE user_id        = $1
          AND challenge_id   = $2
          AND queued_for_day = $3
          AND sent_at        IS NOT NULL
          AND answered_at    IS NULL
        """,
        user_id, challenge_id, today,
    )


async def mark_last_dispatch_day(
    user_id: int, challenge_id: int, local_day: date
) -> None:
    await execute(
        """
        UPDATE challenge_participants
        SET last_dispatch_day = $3
        WHERE user_id = $1 AND challenge_id = $2
        """,
        user_id, challenge_id, local_day,
    )


# ─── PARTITION MANAGEMENT ──────────────────────────────────────────────────


async def ensure_event_partitions(months_ahead: int = DB_PARTITION_MONTHS_AHEAD) -> None:
    today = date.today()
    async with get_pool().acquire() as con:
        for i in range(1, months_ahead + 1):
            year  = today.year + (today.month - 1 + i) // 12
            month = (today.month - 1 + i) % 12 + 1
            m_start = date(year, month, 1)
            m_end   = (
                date(year + 1, 1, 1) if month == 12
                else date(year, month + 1, 1)
            )
            await con.execute(
                f"""
                CREATE TABLE IF NOT EXISTS events_{m_start.strftime('%Y_%m')}
                PARTITION OF events
                FOR VALUES FROM ('{m_start}') TO ('{m_end}')
                """
            )


# ─────────────────────────── USER DETAILED STATS ──────────────────────────


async def get_user_challenge_stats(user_id: int, challenge_id: int) -> dict[str, Any]:
    rows = await fetch(
        """
        SELECT local_day, payload
        FROM events
        WHERE user_id = $1 AND challenge_id = $2
        ORDER BY local_day ASC
        """,
        user_id, challenge_id,
    )

    cp = await fetchrow(
        "SELECT joined_at FROM challenge_participants WHERE user_id=$1 AND challenge_id=$2",
        user_id, challenge_id,
    )
    joined_date = cp["joined_at"].astimezone(pytz.UTC).date() if cp else date.today()
    joined_days = (date.today() - joined_date).days + 1

    total_days = len(rows)
    today      = date.today()
    week_ago   = today - timedelta(days=DB_STATS_WEEK_DAYS - 1)

    last_7_rows = [r for r in rows if r["local_day"] >= week_ago]

    result: dict[str, Any] = {
        "total_days":  total_days,
        "joined_days": joined_days,
        "last_7_rows": last_7_rows,
    }

    challenge = await fetchrow("SELECT kind FROM challenges WHERE id=$1", challenge_id)
    if not challenge:
        return result
    kind = challenge["kind"]

    if kind == "yes_no":
        yes_count = sum(
            1 for r in rows
            if _payload_value(r["payload"]) == "yes"
        )
        no_count = total_days - yes_count
        yes_7  = sum(1 for r in last_7_rows if _payload_value(r["payload"]) == "yes")
        days_7 = len(last_7_rows)
        current_streak, max_streak = _calc_streaks(rows, "yes")
        result.update({
            "yes_count":      yes_count,
            "no_count":       no_count,
            "yes_7":          yes_7,
            "days_7":         days_7,
            "current_streak": current_streak,
            "max_streak":     max_streak,
        })

    elif kind in ("count", "scale_1_5"):
        values_all  = [_payload_int(r["payload"]) for r in rows]
        values_7    = [_payload_int(r["payload"]) for r in last_7_rows]
        avg_all = round(sum(values_all) / len(values_all), 1) if values_all else None
        avg_7   = round(sum(values_7)   / len(values_7),   1) if values_7   else None
        max_val = max(values_all) if values_all else None
        sum_all = sum(values_all)
        last_7_values = [(r["local_day"], _payload_int(r["payload"])) for r in last_7_rows]
        result.update({
            "avg_7":         avg_7,
            "avg_all":       avg_all,
            "max_val":       max_val,
            "sum_all":       sum_all,
            "last_7_values": last_7_values,
        })
        if kind == "scale_1_5":
            dist: dict[int, int] = {i: 0 for i in range(1, 6)}
            for v in values_all:
                if v in dist:
                    dist[v] += 1
            result["distribution"] = dist

    elif kind == "poll":
        dist_poll: dict[str, int] = {}
        for r in rows:
            v = str(_payload_value(r["payload"]))
            dist_poll[v] = dist_poll.get(v, 0) + 1
        result["distribution"]  = dist_poll
        result["total_answers"] = total_days

    return result


def _payload_value(payload) -> str:
    import json as _json
    if isinstance(payload, str):
        payload = _json.loads(payload)
    return str(payload.get("value", ""))


def _payload_int(payload) -> int:
    import json as _json
    if isinstance(payload, str):
        payload = _json.loads(payload)
    try:
        return int(payload.get("value", 0))
    except (TypeError, ValueError):
        return 0


def _calc_streaks(rows, target_value: str) -> tuple[int, int]:
    if not rows:
        return 0, 0

    today = date.today()
    yes_days = {r["local_day"] for r in rows if _payload_value(r["payload"]) == target_value}
    all_days  = sorted({r["local_day"] for r in rows})

    max_s = cur_s = 0
    prev: date | None = None
    for d in all_days:
        if d in yes_days:
            if prev is not None and (d - prev).days == 1:
                cur_s += 1
            else:
                cur_s = 1
            max_s = max(max_s, cur_s)
        else:
            cur_s = 0
        prev = d

    cur_s = 0
    d = today
    while d in yes_days:
        cur_s += 1
        d -= timedelta(days=1)
    if cur_s == 0:
        d = today - timedelta(days=1)
        while d in yes_days:
            cur_s += 1
            d -= timedelta(days=1)

    return cur_s, max_s


# ─────────────────────────── ADMIN DETAILED STATS ─────────────────────────


async def get_admin_challenge_detail(challenge_id: int) -> dict[str, Any]:
    challenge = await fetchrow("SELECT * FROM challenges WHERE id=$1", challenge_id)
    if not challenge:
        return {}

    import json as _json
    meta = challenge["metadata"]
    if isinstance(meta, str):
        meta = _json.loads(meta)
    kind    = challenge["kind"]
    today   = date.today()
    week_ago = today - timedelta(days=DB_STATS_WEEK_DAYS - 1)

    parts = await fetchrow(
        """
        SELECT
            COUNT(*) FILTER (WHERE TRUE)       AS total_participants,
            COUNT(*) FILTER (WHERE active=TRUE) AS active_participants
        FROM challenge_participants
        WHERE challenge_id = $1
        """,
        challenge_id,
    )

    answers = await fetchrow(
        """
        SELECT
            COUNT(DISTINCT user_id) FILTER (WHERE local_day = $2) AS answered_today,
            COUNT(DISTINCT user_id) FILTER (WHERE local_day >= $3) AS answered_week
        FROM events
        WHERE challenge_id = $1
        """,
        challenge_id, today, week_ago,
    )

    active = parts["active_participants"] or 0
    answered_today = answers["answered_today"] or 0
    rate = round(answered_today / active * 100) if active else 0

    result: dict[str, Any] = {
        "slug":                challenge["slug"],
        "kind":                kind,
        "total_participants":  parts["total_participants"],
        "active_participants": active,
        "answered_today":      answered_today,
        "answered_week":       answers["answered_week"],
        "response_rate_today": rate,
    }

    daily_rows = await fetch(
        r"""
        SELECT
            local_day,
            COUNT(*)                                                                 AS cnt,
            AVG(
                CASE WHEN payload->>'value' ~ '^-?\d+(\.\d+)?$'
                     THEN (payload->>'value')::numeric
                END
            )                                                                        AS avg_val,
            COUNT(*) FILTER (WHERE payload->>'value' = 'yes') * 100.0
                / NULLIF(COUNT(*), 0)                                                AS yes_pct
        FROM events
        WHERE challenge_id = $1 AND local_day >= $2
        GROUP BY local_day
        ORDER BY local_day DESC
        """,
        challenge_id, week_ago,
    )
    result["daily_7"] = [
        {
            "day":     r["local_day"],
            "count":   r["cnt"],
            "avg_val": round(float(r["avg_val"]), 1) if r["avg_val"] is not None else None,
            "yes_pct": round(float(r["yes_pct"])) if r["yes_pct"] is not None else None,
        }
        for r in daily_rows
    ]

    if kind == "yes_no":
        yn_today = await fetchrow(
            """
            SELECT
                COUNT(*) FILTER (WHERE payload->>'value' = 'yes') AS yes_today,
                COUNT(*)                                           AS total_today
            FROM events
            WHERE challenge_id=$1 AND local_day=$2
            """,
            challenge_id, today,
        )
        yn_week = await fetchrow(
            """
            SELECT
                COUNT(*) FILTER (WHERE payload->>'value' = 'yes') AS yes_week,
                COUNT(*)                                           AS total_week
            FROM events
            WHERE challenge_id=$1 AND local_day >= $2
            """,
            challenge_id, week_ago,
        )
        result.update({
            "yes_pct_today": (
                round(yn_today["yes_today"] / yn_today["total_today"] * 100)
                if yn_today["total_today"] else None
            ),
            "yes_pct_week": (
                round(yn_week["yes_week"] / yn_week["total_week"] * 100)
                if yn_week["total_week"] else None
            ),
        })

    elif kind in ("count", "scale_1_5"):
        agg = await fetchrow(
            """
            SELECT
                AVG((payload->>'value')::numeric) FILTER (WHERE local_day=$2) AS avg_today,
                AVG((payload->>'value')::numeric) FILTER (WHERE local_day>=$3) AS avg_week,
                MAX((payload->>'value')::numeric)                               AS max_ever
            FROM events
            WHERE challenge_id=$1
            """,
            challenge_id, today, week_ago,
        )
        result.update({
            "avg_today": round(float(agg["avg_today"]), 1) if agg["avg_today"] is not None else None,
            "avg_week":  round(float(agg["avg_week"]),  1) if agg["avg_week"]  is not None else None,
            "max_ever":  int(agg["max_ever"])               if agg["max_ever"]  is not None else None,
        })

        top_rows = await fetch(
            """
            SELECT
                u.display_name,
                COUNT(*)                              AS total_answers,
                AVG((e.payload->>'value')::numeric)   AS avg_val
            FROM events e
            JOIN users u ON u.id = e.user_id
            WHERE e.challenge_id = $1
            GROUP BY u.id, u.display_name
            ORDER BY total_answers DESC, avg_val DESC
            LIMIT $2
            """,
            challenge_id, DB_TOP_USERS_LIMIT,
        )
        result["top_users"] = [
            {
                "name":          r["display_name"] or "—",
                "total_answers": r["total_answers"],
                "avg_val":       round(float(r["avg_val"]), 1) if r["avg_val"] else 0,
            }
            for r in top_rows
        ]

    elif kind == "poll":
        poll_rows = await fetch(
            """
            SELECT payload->>'value' AS opt, COUNT(*) AS cnt
            FROM events
            WHERE challenge_id=$1 AND local_day >= $2
            GROUP BY payload->>'value'
            ORDER BY cnt DESC
            """,
            challenge_id, week_ago,
        )
        result["distribution_week"] = {r["opt"]: r["cnt"] for r in poll_rows}

    return result