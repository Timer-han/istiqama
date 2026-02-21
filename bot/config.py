"""config.py – Central configuration loaded from environment."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import List

from dotenv import load_dotenv

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
    scheduler_interval: int = int(os.getenv("SCHEDULER_INTERVAL", "60"))
    outbox_batch: int = int(os.getenv("OUTBOX_BATCH", "20"))


config = Config()
