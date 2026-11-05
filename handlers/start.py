"""Handler for the ``/start`` command.

Uses target-audience copywriting for students in Uzbek.
"""

from __future__ import annotations

from aiogram import Router, types
from aiogram.filters import Command

router = Router()


@router.message(Command("start"))
async def handle_start(message: types.Message) -> None:
    """Handle the ``/start`` command.

    Uses this exact text verbatim:
        """👋 **Salom! PostToVideo Bot xizmatingizda!**\n\nMaktab yoki universitet kanallaridagi uzun va zerikarli matnlardan charchadingizmi? Talabalar 2 qatordan uzun postlarni o‘qishga erinishadimi? 🥱\n\n**Men bu muammoni hal qilaman!** Menga istalgan matnni yuboring, men esa uni bir necha soniya ichida ovozli, avto-titrli va tashkilotingiz logotipi tushirilgan qisqa vertikal videoga (Shorts/Reels) aylantirib beraman! 🎬🔥\n\n⚙️ **Mavjud buyruqlar:**\n🔹 Shunchaki matnni yuboring — va men montajni boshlayman.\n🔹 ``/setlogo`` — videolaringizga brend qo‘shish uchun PNG formatdagi logotipni yuklang (adminlar va faollar uchun).\n\nSizdan birinchi postni kutib qolaman! 👇"""
    """
    await message.answer(
        """
        👋 **Salom! PostToVideo Bot xizmatingizda!**

Maktab yoki universitet kanallaridagi uzun va zerikarli matnlardan charchadingizmi? Talabalar 2 qatordan uzun postlarni o‘qishga erinishadimi? 🥱

**Men bu muammoni hal qilaman!** Menga istalgan matnni yuboring, men esa uni bir necha soniya ichida ovozli, avto-titrli va tashkilotingiz logotipi tushirilgan qisqa vertikal videoga (Shorts/Reels) aylantirib beraman! 🎬🔥

⚙️ **Mavjud buyruqlar:**
🔹 Shunchaki matnni yuboring — va men montajni boshlayman.
🔹 `/setlogo` — videolaringizga brend qo‘shish uchun PNG formatdagi logotipni yuklang (adminlar va faollar uchun).

Sizdan birinchi postni kutib qolaman! 👇
        """
    )