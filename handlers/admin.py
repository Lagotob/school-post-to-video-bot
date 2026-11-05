"""Handler for the ``/setlogo`` command.

Prompts the user to upload a photo/document, verifies it is a valid format,
downloads it asynchronously, saves it into a ``logos/`` local directory,
and indexes the file location inside the SQLite database.
"""

from __future__ import annotations

import os
from typing import Optional

from aiogram import F, Router, types
from aiogram.filters import Command

from config import LOGOS_DIR
from database import save_logo_path

router = Router()


@router.message(Command("setlogo"))
async def handle_setlogo(message: types.Message) -> None:
    """Handle the ``/setlogo`` command.

    Prompts the user to upload a PNG image for their organization logo.
    """
    await message.answer(
        "Iltimos, tashkilotingiz logotipini PNG formatida yuboring:"
    )


@router.message(F.photo | F.document)
async def handle_logo_upload(message: types.Message) -> None:
    """Handle a logo upload.

    Verifies the file is a valid PNG, downloads it, saves it to the ``logos/``
    directory, and indexes the path in the database.
    """
    # Check if this is a reply to the ``/setlogo`` prompt.
    if not message.reply_to_message:
        return
    if not message.reply_to_message.text == "Iltimos, tashkilotingiz logotipini PNG formatida yuboring:":
        return

    # Verify the file is a PNG.
    file_id: Optional[str] = None
    file_path: Optional[str] = None
    if message.photo:
        file_id = message.photo[-1].file_id
        file_path = message.photo[-1].file_path
    elif message.document:
        if message.document.mime_type != "image/png":
            await message.answer(
                "Iltimos, faqat PNG formatdagi fayl yuboring."
            )
            return
        file_id = message.document.file_id
        file_path = message.document.file_path

    if not file_id or not file_path:
        await message.answer(
            "Faylni yuklashda xatolik yuz berdi. Iltimos, qayta urinib ko‘ring."
        )
        return

    # Download the file.
    file = await message.bot.download(file_id)
    if not file:
        await message.answer(
            "Faylni yuklashda xatolik yuz berdi. Iltimos, qayta urinib ko‘ring."
        )
        return

    # Save the file to the logos directory.
    os.makedirs(LOGOS_DIR, exist_ok=True)
    logo_path = os.path.join(LOGOS_DIR, f"{message.chat.id}.png")
    with open(logo_path, "wb") as f:
        f.write(file.read())

    # Save the path to the database.
    await save_logo_path(message.chat.id, logo_path, file_id)

    await message.answer("Logotip muvaffaqiyatli saqlandi! ✅")