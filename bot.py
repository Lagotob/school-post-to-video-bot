"""Orchestration root for the PostToVideo Bot.

Initializes the ``Bot`` and ``Dispatcher``, ties together database
initialization lifecycle hooks on startup, registers all created event routers,
and establishes long-polling mode with a background web health-check for Render.
"""

from __future__ import annotations

import asyncio
import logging
import os

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiohttp import web

from config import BOT_TOKEN
from database import init_db
from handlers import admin, start, text_processor, video_generator


async def handle_hc(request: web.Request) -> web.Response:
    """Handle health check requests from Render."""
    return web.Response(text="Bot is running smoothly!", status=200)


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

    # Set up a mini web server to pass Render's port scan on the free tier.
    app = web.Application()
    app.router.add_get("/", handle_hc)
    
    # Render automatically sets the PORT environment variable (defaults to 10000).
    port = int(os.environ.get("PORT", 10000))
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    
    # Start the web server in the background.
    await site.start()
    logging.info(f"Render health-check web server started on port {port}")

    # Start the bot in long-polling mode.
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
