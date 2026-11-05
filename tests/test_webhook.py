import unittest
from unittest.mock import patch

from aiogram import Bot, Dispatcher
from aiohttp.test_utils import TestClient, TestServer

from bot import create_web_app


class WebhookTests(unittest.IsolatedAsyncioTestCase):
    async def test_health_endpoint_is_available(self) -> None:
        bot = Bot(token="123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11")
        try:
            with (
                patch("bot.WEBHOOK_BASE_URL", "https://example.onrender.com"),
                patch("bot.WEBHOOK_SECRET_TOKEN", "test_secret"),
            ):
                app = create_web_app(bot, Dispatcher())
                async with TestClient(TestServer(app)) as client:
                    response = await client.get("/healthz")
                    self.assertEqual(response.status, 200)
                    self.assertEqual(await response.text(), "ok")
        finally:
            await bot.session.close()


if __name__ == "__main__":
    unittest.main()
