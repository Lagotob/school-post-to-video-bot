from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

router = Router()

@router.message(CommandStart())
async def cmd_start(message: Message):
    welcome_text = (
        "Salom! PostToVideo Bot xizmatingizda!\n\n"
        "Maktab yoki universitet kanallaridagi uzun va zerikarli matnlardan charchadingizmi? "
        "Talabalar 2 qatordan uzun postlarni o'qishga erinishadimi?\n\n"
        "Men bu muammoni hal qilaman! Menga istalgan matnni yuboring, men esa uni bir necha "
        "soniya ichida ovozli, avto-titrli va tashkilotingiz logotipi tushirilgan qisqa vertikal "
        "videoga (Shorts/Reels) aylantirib beraman!\n\n"
        "Mavjud buyruqlar:\n"
        " - Shunchaki matnni yuboring va men montajni boshlayman.\n"
        " - /setlogo - videolaringizga brend qo'shish uchun PNG formatdagi logotipni yuklang.\n\n"
        "Sizdan birinchi postni kutib qolaman!"
    )
    await message.answer(welcome_text)
