"""bot/main.py – application entry point."""
from __future__ import annotations

import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from adapters.storage_postgres import init_pool, close_pool
from bot.config import config
from bot.handlers import router as user_router
from bot.admin_handlers import router as admin_router
from bot.middleware import UserMiddleware
from services.aggregator import aggregator_task
from services.outbox import outbox_task
from services.scheduler import scheduler_task

logging.basicConfig(
    level=logging.INFO,
    stream=sys.stdout,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


async def main() -> None:
    logger.info("Connecting to database …")
    await init_pool(config.db_dsn, min_size=config.db_pool_min, max_size=config.db_pool_max)
    logger.info("Database connected.")

    storage = MemoryStorage()
    bot = Bot(
        token=config.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN),
    )
    dp = Dispatcher(storage=storage)

    dp.update.middleware(UserMiddleware())

    # Admin router first (has IsAdmin filter)
    dp.include_router(admin_router)
    dp.include_router(user_router)

    loop = asyncio.get_event_loop()
    loop.create_task(scheduler_task(bot, storage=storage, interval=config.scheduler_interval))
    loop.create_task(aggregator_task())
    loop.create_task(outbox_task(bot, rate_limit=config.outbox_rate_limit))

    logger.info("Starting long-polling …")
    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        await close_pool()
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())