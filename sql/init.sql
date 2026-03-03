-- ============================================================
-- Istiqama – init.sql  (полная версия с очередью v2)
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
-- ----------------------------------------------------------
CREATE TABLE IF NOT EXISTS challenge_participants (
    user_id           BIGINT      NOT NULL REFERENCES users(id)      ON DELETE CASCADE,
    challenge_id      BIGINT      NOT NULL REFERENCES challenges(id)  ON DELETE CASCADE,
    joined_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    active            BOOLEAN     NOT NULL DEFAULT TRUE,
    last_answer_day   DATE,
    last_dispatch_day DATE,
    next_dispatch_at  TIMESTAMPTZ,
    PRIMARY KEY (user_id, challenge_id)
);

-- ----------------------------------------------------------
-- events  (иммутабельный лог, партиционируется по event_ts)
-- ----------------------------------------------------------
CREATE TABLE IF NOT EXISTS events (
    id           BIGSERIAL,
    user_id      BIGINT      NOT NULL REFERENCES users(id)      ON DELETE CASCADE,
    challenge_id BIGINT      NOT NULL REFERENCES challenges(id)  ON DELETE CASCADE,
    event_ts     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    local_day    DATE        NOT NULL,
    payload      JSONB       NOT NULL DEFAULT '{}'
) PARTITION BY RANGE (event_ts);

DO $$
DECLARE m DATE;
BEGIN
    FOR i IN 0..14 LOOP
        m := DATE_TRUNC('month', NOW()) + (i || ' month')::INTERVAL;
        EXECUTE FORMAT(
            'CREATE TABLE IF NOT EXISTS events_%s PARTITION OF events
             FOR VALUES FROM (%L) TO (%L)',
            TO_CHAR(m, 'YYYY_MM'), m, m + '1 month'::INTERVAL
        );
    END LOOP;
END;
$$;

-- ----------------------------------------------------------
-- user_question_queue
--
-- Жизненный цикл записи:
--   sent_at=NULL,  answered_at=NULL  → в очереди, не отправлен
--   sent_at=NOW,   answered_at=NULL  → ОТПРАВЛЕН, ждём ответ  ← блокирует следующий
--   sent_at=NOW,   answered_at=NOW   → ОТВЕЧЕН → разблокирует следующий
--
-- Батч = (user_id, queued_for_day, schedule_time).
-- Каждый день записи пересоздаются. Вчерашние удаляются при старте тика.
-- ----------------------------------------------------------
CREATE TABLE IF NOT EXISTS user_question_queue (
    id             BIGSERIAL PRIMARY KEY,
    user_id        BIGINT   NOT NULL REFERENCES users(id)      ON DELETE CASCADE,
    challenge_id   BIGINT   NOT NULL REFERENCES challenges(id)  ON DELETE CASCADE,
    queued_for_day DATE     NOT NULL,
    schedule_time  TEXT     NOT NULL,
    position       SMALLINT NOT NULL DEFAULT 1,
    sent_at        TIMESTAMPTZ,    -- когда вопрос отправлен пользователю
    answered_at    TIMESTAMPTZ,    -- когда пользователь ответил
    UNIQUE (user_id, challenge_id, queued_for_day)
);

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

CREATE INDEX IF NOT EXISTS idx_participants_dispatch
    ON challenge_participants (next_dispatch_at)
    WHERE active = TRUE;

CREATE INDEX IF NOT EXISTS idx_events_id
    ON events (id);

CREATE INDEX IF NOT EXISTS idx_events_user_challenge_day
    ON events (user_id, challenge_id, local_day);

CREATE INDEX IF NOT EXISTS idx_participants_challenge_active
    ON challenge_participants (challenge_id, active);

-- Найти следующий неотправленный вопрос в батче
CREATE INDEX IF NOT EXISTS idx_queue_unsent
    ON user_question_queue (user_id, queued_for_day, schedule_time, position)
    WHERE sent_at IS NULL;

-- Проверить есть ли отправленный-неотвеченный в батче
CREATE INDEX IF NOT EXISTS idx_queue_unanswered
    ON user_question_queue (user_id, queued_for_day, schedule_time)
    WHERE sent_at IS NOT NULL AND answered_at IS NULL;

-- ----------------------------------------------------------
-- Safe migrations for existing databases
-- Безопасно запускать повторно на живой базе
-- ----------------------------------------------------------

-- lang в users
DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name='users' AND column_name='lang') THEN
        ALTER TABLE users ADD COLUMN lang TEXT NOT NULL DEFAULT 'ru';
    END IF;
END $$;

-- last_dispatch_day в challenge_participants
DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name='challenge_participants'
                   AND column_name='last_dispatch_day') THEN
        ALTER TABLE challenge_participants ADD COLUMN last_dispatch_day DATE;
    END IF;
END $$;

-- Создать user_question_queue если не существует
DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.tables
                   WHERE table_name = 'user_question_queue') THEN
        CREATE TABLE user_question_queue (
            id             BIGSERIAL PRIMARY KEY,
            user_id        BIGINT   NOT NULL REFERENCES users(id)      ON DELETE CASCADE,
            challenge_id   BIGINT   NOT NULL REFERENCES challenges(id)  ON DELETE CASCADE,
            queued_for_day DATE     NOT NULL,
            schedule_time  TEXT     NOT NULL,
            position       SMALLINT NOT NULL DEFAULT 1,
            sent_at        TIMESTAMPTZ,
            answered_at    TIMESTAMPTZ,
            UNIQUE (user_id, challenge_id, queued_for_day)
        );
        CREATE INDEX idx_queue_unsent ON user_question_queue
            (user_id, queued_for_day, schedule_time, position)
            WHERE sent_at IS NULL;
        CREATE INDEX idx_queue_unanswered ON user_question_queue
            (user_id, queued_for_day, schedule_time)
            WHERE sent_at IS NOT NULL AND answered_at IS NULL;
    END IF;
END $$;

-- Миграция если таблица есть со старой схемой (dispatched_at → sent_at + answered_at)
DO $$ BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.columns
               WHERE table_name='user_question_queue'
               AND column_name='dispatched_at') THEN
        ALTER TABLE user_question_queue RENAME COLUMN dispatched_at TO sent_at;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name='user_question_queue'
                   AND column_name='answered_at') THEN
        ALTER TABLE user_question_queue ADD COLUMN answered_at TIMESTAMPTZ;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name='user_question_queue'
                   AND column_name='sent_at') THEN
        ALTER TABLE user_question_queue ADD COLUMN sent_at TIMESTAMPTZ;
    END IF;
END $$;