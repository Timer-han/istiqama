"""adapters/storage_postgres.py – thin asyncpg wrapper."""
from __future__ import annotations

import asyncpg
from typing import Optional, List, Any

from constants import DB_POOL_MIN_SIZE, DB_POOL_MAX_SIZE

_pool: Optional[asyncpg.Pool] = None


async def init_pool(dsn: str, min_size: int = DB_POOL_MIN_SIZE, max_size: int = DB_POOL_MAX_SIZE) -> None:
    global _pool
    _pool = await asyncpg.create_pool(dsn, min_size=min_size, max_size=max_size)


async def close_pool() -> None:
    if _pool:
        await _pool.close()


def get_pool() -> asyncpg.Pool:
    if _pool is None:
        raise RuntimeError("DB pool not initialised")
    return _pool


# ---------- helpers -------------------------------------------------------

async def fetchrow(query: str, *args: Any) -> Optional[asyncpg.Record]:
    async with get_pool().acquire() as con:
        return await con.fetchrow(query, *args)


async def fetch(query: str, *args: Any) -> List[asyncpg.Record]:
    async with get_pool().acquire() as con:
        return await con.fetch(query, *args)


async def execute(query: str, *args: Any) -> str:
    async with get_pool().acquire() as con:
        return await con.execute(query, *args)


async def executemany(query: str, args: list) -> None:
    async with get_pool().acquire() as con:
        await con.executemany(query, args)