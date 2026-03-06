"""services/aggregator.py – incremental stats aggregation."""
from __future__ import annotations

import asyncio
import json
import logging

from adapters.storage_postgres import fetch, fetchrow, execute, get_pool
from constants import AGGREGATOR_BATCH_SIZE, AGGREGATOR_SLEEP_SECONDS

logger = logging.getLogger(__name__)


async def aggregator_task() -> None:
    logger.info("Aggregator started")
    while True:
        try:
            await _run_aggregation()
        except Exception as exc:
            logger.exception("Aggregator error: %s", exc)
        await asyncio.sleep(AGGREGATOR_SLEEP_SECONDS)


async def _run_aggregation() -> None:
    state = await fetchrow(
        "SELECT value FROM meta_processing_state WHERE key='last_processed_event_id'"
    )
    last_id = int(state["value"]) if state else 0

    events = await fetch(
        """
        SELECT id, challenge_id, local_day, payload
        FROM events
        WHERE id > $1
        ORDER BY id
        LIMIT $2
        """,
        last_id, AGGREGATOR_BATCH_SIZE,
    )

    if not events:
        return

    # Group by (challenge_id, local_day)
    groups: dict[tuple, dict] = {}
    for e in events:
        key = (e["challenge_id"], e["local_day"])
        payload = e["payload"]
        if isinstance(payload, str):
            payload = json.loads(payload)
        val = payload.get("value", 0)
        try:
            numeric_val = int(val)
        except (TypeError, ValueError):
            numeric_val = 0

        if key not in groups:
            groups[key] = {"count": 0, "sum": 0, "max": 0}
        g = groups[key]
        g["count"] += 1
        g["sum"] += numeric_val
        g["max"] = max(g["max"], numeric_val)

    async with get_pool().acquire() as con:
        async with con.transaction():
            for (challenge_id, day), g in groups.items():
                await con.execute(
                    """
                    INSERT INTO daily_challenge_stats (challenge_id, day, total_responses, sum_counts, max_count)
                    VALUES ($1, $2, $3, $4, $5)
                    ON CONFLICT (challenge_id, day) DO UPDATE SET
                        total_responses = daily_challenge_stats.total_responses + EXCLUDED.total_responses,
                        sum_counts      = daily_challenge_stats.sum_counts      + EXCLUDED.sum_counts,
                        max_count       = GREATEST(daily_challenge_stats.max_count, EXCLUDED.max_count)
                    """,
                    challenge_id, day, g["count"], g["sum"], g["max"],
                )

            new_last_id = events[-1]["id"]
            await con.execute(
                "UPDATE meta_processing_state SET value=$1 WHERE key='last_processed_event_id'",
                str(new_last_id),
            )

    logger.debug("Aggregated %d events, last_id=%d", len(events), events[-1]["id"])