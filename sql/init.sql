-- ============================================================
-- Istiqama – init.sql
-- ============================================================

CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ----------------------------------------------------------
-- users
-- ----------------------------------------------------------
CREATE TABLE IF NOT EXISTS users (
    id            BIGSERIAL PRIMARY KEY,
    telegram_id   BIGINT UNIQUE NOT NULL,
    username      TEXT,
    display_name  TEXT,
    gender        TEXT,
    country       TEXT,
    city          TEXT,
    lat           DOUBLE PRECISION,
    lon           DOUBLE PRECISION,
    timezone      TEXT NOT NULL DEFAULT 'UTC',
    registered_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    lang          TEXT NOT NULL DEFAULT 'ru',
    profile       JSONB NOT NULL DEFAULT '{}'
);

-- ----------------------------------------------------------
-- challenges
-- ----------------------------------------------------------
CREATE TABLE IF NOT EXISTS challenges (
    id         BIGSERIAL PRIMARY KEY,
    slug       TEXT UNIQUE NOT NULL,
    kind       TEXT NOT NULL CHECK (kind IN ('yes_no','count','scale_1_5','poll')),
    metadata   JSONB NOT NULL DEFAULT '{}',
    active     BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ----------------------------------------------------------
-- challenge_participants
--
--   last_answer_day  – дата последнего ответа (local_day пользователя).
--                      NULL если ответов ещё не было.
--   next_dispatch_at – UTC-момент следующей отправки вопроса.
--                      Scheduler: WHERE cp.next_dispatch_at <= NOW().
--                      NULL = не вычислено (scheduler отправит сразу).
-- ----------------------------------------------------------
CREATE TABLE IF NOT EXISTS challenge_participants (
    user_id          BIGINT      NOT NULL REFERENCES users(id)     ON DELETE CASCADE,
    challenge_id     BIGINT      NOT NULL REFERENCES challenges(id) ON DELETE CASCADE,
    joined_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    active           BOOLEAN     NOT NULL DEFAULT TRUE,
    last_answer_day   DATE,         -- local_day последнего ответа пользователя
    last_dispatch_day DATE,         -- local_day последней отправки вопроса
    next_dispatch_at TIMESTAMPTZ,
    PRIMARY KEY (user_id, challenge_id)
);

-- ----------------------------------------------------------
-- events  (иммутабельный лог, партиционируется по event_ts)
-- ----------------------------------------------------------
CREATE TABLE IF NOT EXISTS events (
    id           BIGSERIAL,
    user_id      BIGINT      NOT NULL REFERENCES users(id)     ON DELETE CASCADE,
    challenge_id BIGINT      NOT NULL REFERENCES challenges(id) ON DELETE CASCADE,
    event_ts     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    local_day    DATE        NOT NULL,
    payload      JSONB       NOT NULL DEFAULT '{}'
) PARTITION BY RANGE (event_ts);

DO $$
DECLARE
    m DATE;
BEGIN
    FOR i IN 0..11 LOOP
        m := DATE_TRUNC('month', NOW()) + (i || ' month')::INTERVAL;
        EXECUTE FORMAT(
            'CREATE TABLE IF NOT EXISTS events_%s PARTITION OF events
             FOR VALUES FROM (%L) TO (%L)',
            TO_CHAR(m, 'YYYY_MM'),
            m,
            m + '1 month'::INTERVAL
        );
    END LOOP;
END;
$$;

-- ----------------------------------------------------------
-- daily_challenge_stats
-- ----------------------------------------------------------
CREATE TABLE IF NOT EXISTS daily_challenge_stats (
    challenge_id     BIGINT NOT NULL REFERENCES challenges(id) ON DELETE CASCADE,
    day              DATE   NOT NULL,
    total_responses  INT    NOT NULL DEFAULT 0,
    sum_counts       BIGINT NOT NULL DEFAULT 0,
    max_count        BIGINT NOT NULL DEFAULT 0,
    PRIMARY KEY (challenge_id, day)
);

-- ----------------------------------------------------------
-- outbox_messages
-- ----------------------------------------------------------
CREATE TABLE IF NOT EXISTS outbox_messages (
    id           BIGSERIAL PRIMARY KEY,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    scheduled_at TIMESTAMPTZ,
    sent_at      TIMESTAMPTZ,
    status       TEXT NOT NULL DEFAULT 'pending'
                      CHECK (status IN ('pending','sending','sent','failed')),
    target       TEXT NOT NULL DEFAULT 'all',
    text         TEXT NOT NULL,
    extra        JSONB NOT NULL DEFAULT '{}'
);

-- ----------------------------------------------------------
-- meta_processing_state
-- ----------------------------------------------------------
CREATE TABLE IF NOT EXISTS meta_processing_state (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

INSERT INTO meta_processing_state (key, value)
VALUES ('last_processed_event_id', '0')
ON CONFLICT DO NOTHING;

-- ----------------------------------------------------------
-- Indexes
-- ----------------------------------------------------------

-- Главный индекс scheduler hotpath:
--   WHERE cp.active = TRUE AND cp.next_dispatch_at <= NOW()
-- Partial index — покрывает только активных, B-tree по времени.
CREATE INDEX IF NOT EXISTS idx_participants_dispatch
    ON challenge_participants (next_dispatch_at)
    WHERE active = TRUE;

-- Aggregator читает events строго по id
CREATE INDEX IF NOT EXISTS idx_events_id
    ON events (id);

-- Статистика и дубль-чек ответов
CREATE INDEX IF NOT EXISTS idx_events_user_challenge_day
    ON events (user_id, challenge_id, local_day);

-- Для get_active_participants / admin stats
CREATE INDEX IF NOT EXISTS idx_participants_challenge_active
    ON challenge_participants (challenge_id, active);

-- ----------------------------------------------------------
-- Migration: add last_dispatch_day to challenge_participants
-- (safe to run on existing DB — IF NOT EXISTS column pattern)
-- ----------------------------------------------------------
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name='challenge_participants'
          AND column_name='last_dispatch_day'
    ) THEN
        ALTER TABLE challenge_participants
            ADD COLUMN last_dispatch_day DATE;
    END IF;
END;
$$;

-- ----------------------------------------------------------
-- Migration: add lang column to users (safe for existing DB)
-- ----------------------------------------------------------
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name='users' AND column_name='lang'
    ) THEN
        ALTER TABLE users ADD COLUMN lang TEXT NOT NULL DEFAULT 'ru';
    END IF;
END;
$$;

-- ----------------------------------------------------------
-- Migration: challenges – launch_at and announced are stored
-- inside metadata JSONB (no DDL change needed).
-- This comment documents the convention:
--   metadata.launch_at  – ISO UTC string | null (null = immediately)
--   metadata.announced  – boolean (false until scheduler sends announcement)
-- ----------------------------------------------------------
