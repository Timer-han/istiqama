"""constants.py – Single source of truth for all magic numbers and defaults.

Import from here everywhere instead of scattering literals across modules.
"""
from __future__ import annotations

# ── Timezones ──────────────────────────────────────────────────────────────
DEFAULT_TIMEZONE          = "Europe/Moscow"
SCHEDULE_TIME_FALLBACK    = "06:00"          # used when metadata is malformed

# ── DB connection pool ─────────────────────────────────────────────────────
DB_POOL_MIN_SIZE          = 2
DB_POOL_MAX_SIZE          = 10

# ── Query limits ───────────────────────────────────────────────────────────
DB_DUE_PARTICIPANTS_LIMIT = 500   # max rows per scheduler tick
DB_PENDING_OUTBOX_LIMIT   = 50    # rows fetched & locked per outbox tick
DB_STATS_WEEK_DAYS        = 7     # "last N days" window for user stats
DB_TOP_USERS_LIMIT        = 5     # rows in admin challenge top-users list
DB_PARTITION_MONTHS_AHEAD = 3     # how many future months to pre-create

# ── Aggregator ─────────────────────────────────────────────────────────────
AGGREGATOR_BATCH_SIZE     = 200   # events processed per aggregation run
AGGREGATOR_SLEEP_SECONDS  = 30    # pause between aggregation runs

# ── Outbox ─────────────────────────────────────────────────────────────────
OUTBOX_RATE_LIMIT         = 20    # max Telegram messages per second
OUTBOX_PROCESS_LIMIT      = 20    # outbox rows sent per tick (= RATE_LIMIT)
OUTBOX_SLEEP_SECONDS      = 5     # pause between outbox processing ticks

# ── Scheduler ─────────────────────────────────────────────────────────────
SCHEDULER_INACTIVITY_DAYS = 3     # days without answer → auto-kick
SCHEDULER_ANNOUNCE_RATE   = 0.05  # seconds between per-user announce messages

# ── Validation: challenge wizard ───────────────────────────────────────────
TITLE_MIN_LEN             = 2
TITLE_MAX_LEN             = 80
DESCRIPTION_MAX_LEN       = 600
QUESTION_MIN_LEN          = 5
QUESTION_MAX_LEN          = 300
POLL_OPTIONS_MIN          = 2
POLL_OPTIONS_MAX          = 10
DURATION_MIN_DAYS         = 1
DURATION_MAX_DAYS         = 3_650