"""Handler for the ``/start`` command.

Uses target-audience copywriting for students in Uzbek.
"""

from __future__ import annotations

from aiogram import Router, types
from aiogram.filters import Command

router = Router()


@router.message(Command("start"))
async def handle_start(message: types.Message) -> None:
    """Handle the ``/start`` command."""
    await message.answer(
        """
        👋 <b>Salom! PostToVideo Bot xizmatingizda!</b>

Maktab yoki universitet kanallaridagi uzun va zerikarli matnlardan charchadingizmi? Talabalar 2 qatordan uzun postlarni o‘qishga erinishadimi? 🥱

<b>Men bu muammoni hal qilaman!</b> Menga istalgan matnni yuboring, men esa uni bir necha soniya ichida ovozli, avto-titrli va tashkilotingiz logotipi tushirilgan qisqa vertikal videoga (Shorts/Reels) aylantirib beraman! 🎬🔥

⚙️ <b>Mavjud buyruqlar:</b>
🔹 Shunchaki matnni yuboring — va men montajni boshlayman.
🔹 <code>/setlogo</code> — videolaringizga brend qo‘shish uchun PNG formatdagi logotipni yuklang (adminlar uchun).

Sizdan birinchi postni kutib qolaman! 👇
        """
    )