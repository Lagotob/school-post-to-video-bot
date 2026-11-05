"""Orchestration root for the PostToVideo Bot.

Initializes the ``Bot`` and ``Dispatcher``, ties together database
initialization lifecycle hooks on startup, registers all created event routers,
and establishes long-polling mode.
"""

from __future__ import annotations

import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from config import BOT_TOKEN
from database import init_db
from handlers import admin, start, text_processor, video_generator


async def main() -> None:
    """Initialize the bot and start long-polling mode."""
    # Initialize the database.
    await init_db()

    # Set up the bot and dispatcher.
    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher()

    # Register all event routers.
    dp.include_router(start.router)
    dp.include_router(admin.router)
    dp.include_router(text_processor.router)
    dp.include_router(video_generator.router)

    # Start the bot.
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())