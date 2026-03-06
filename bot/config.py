"""config.py – Central configuration loaded from environment."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import List

from dotenv import load_dotenv

from constants import (
    DB_POOL_MIN_SIZE,
    DB_POOL_MAX_SIZE,
    OUTBOX_RATE_LIMIT,
    SCHEDULER_INACTIVITY_DAYS,
)

load_dotenv()


@dataclass
class Config:
    bot_token: str = field(default_factory=lambda: os.environ["BOT_TOKEN"])
    db_dsn: str = field(
        default_factory=lambda: os.getenv(
            "DATABASE_URL",
            "postgresql://istiqama:istiqama@db:5432/istiqama",
        )
    )
    admin_ids: List[int] = field(
        default_factory=lambda: [
            int(x.strip())
            for x in os.getenv("ADMIN_IDS", "").split(",")
            if x.strip()
        ]
    )
    scheduler_interval: int = field(
        default_factory=lambda: int(os.getenv("SCHEDULER_INTERVAL", "60"))
    )
    # Maximum Telegram messages per second for broadcasts.
    # Overrides the OUTBOX_RATE_LIMIT constant when set via env.
    outbox_rate_limit: int = field(
        default_factory=lambda: int(os.getenv("OUTBOX_RATE_LIMIT", str(OUTBOX_RATE_LIMIT)))
    )
    db_pool_min: int = field(
        default_factory=lambda: int(os.getenv("DB_POOL_MIN", str(DB_POOL_MIN_SIZE)))
    )
    db_pool_max: int = field(
        default_factory=lambda: int(os.getenv("DB_POOL_MAX", str(DB_POOL_MAX_SIZE)))
    )


config = Config()