"""Orchestration root for the PostToVideo Bot.

Initializes the ``Bot`` and ``Dispatcher``, ties together database
initialization, registers the event routers, and starts polling or webhook mode.
"""

from __future__ import annotations

import asyncio
import logging
import re

from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application

from config import (
    BOT_TOKEN,
    PORT,
    WEBHOOK_BASE_URL,
    WEBHOOK_PATH,
    WEBHOOK_SECRET_TOKEN,
)
from database import init_db
from handlers import admin, start, video_generator


async def health_check(request: web.Request) -> web.Response:
    return web.Response(text="ok")


def create_web_app(bot: Bot, dp: Dispatcher) -> web.Application:
    """Create the HTTP application used for Telegram webhooks and health checks."""
    if not WEBHOOK_SECRET_TOKEN:
        raise RuntimeError(
            "WEBHOOK_SECRET_TOKEN is required when WEBHOOK_BASE_URL is configured."
        )
    if not WEBHOOK_BASE_URL.startswith("https://"):
        raise ValueError("WEBHOOK_BASE_URL must be an HTTPS URL.")
    if not WEBHOOK_PATH.startswith("/"):
        raise ValueError("WEBHOOK_PATH must start with '/'.")
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,256}", WEBHOOK_SECRET_TOKEN):
        raise ValueError(
            "WEBHOOK_SECRET_TOKEN must use 1-256 letters, numbers, underscores, or hyphens."
        )

    app = web.Application()
    app.router.add_get("/healthz", health_check)
    SimpleRequestHandler(
        dispatcher=dp,
        bot=bot,
        secret_token=WEBHOOK_SECRET_TOKEN,
    ).register(app, path=WEBHOOK_PATH)
    setup_application(app, dp, bot=bot)
    return app


async def run_webhook(bot: Bot, dp: Dispatcher) -> None:
    """Serve Telegram updates over HTTP when deployed as a Render Web Service."""
    app = create_web_app(bot, dp)
    runner = web.AppRunner(app)
    try:
        await runner.setup()
        site = web.TCPSite(runner, host="0.0.0.0", port=PORT)
        await site.start()
        await bot.set_webhook(
            f"{WEBHOOK_BASE_URL}{WEBHOOK_PATH}",
            secret_token=WEBHOOK_SECRET_TOKEN,
            allowed_updates=dp.resolve_used_update_types(),
        )
        logging.info("Telegram webhook listening on port %s", PORT)
        await asyncio.Event().wait()
    finally:
        await runner.cleanup()
        await bot.session.close()


async def main() -> None:
    """Initialize the bot and start polling or webhook mode."""
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN is required; set it in the deployment environment.")

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
    dp.include_router(video_generator.router)

    if WEBHOOK_BASE_URL:
        await run_webhook(bot, dp)
    else:
        await bot.delete_webhook(drop_pending_updates=False)
        await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())