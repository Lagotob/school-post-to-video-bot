"""Admin-only logo upload handlers."""

from __future__ import annotations

import os
from io import BytesIO
from typing import Optional

from aiogram import F, Router, types
from aiogram.filters import Command
from PIL import Image, UnidentifiedImageError

from config import ADMIN_IDS, LOGOS_DIR
from database import save_logo_path, upsert_user

router = Router()
_pending_logo_uploads: set[tuple[int, int]] = set()


@router.message(Command("setlogo"))
async def handle_setlogo(message: types.Message) -> None:
    """Handle the ``/setlogo`` command.

    Prompts the admin to upload an image for their organization logo.
    """
    if message.from_user is None or message.from_user.id not in ADMIN_IDS:
        await message.answer("Bu buyruq faqat bot administratorlari uchun.")
        return

    await upsert_user(
        chat_id=message.chat.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
        last_name=message.from_user.last_name,
        is_admin=True,
    )
    _pending_logo_uploads.add((message.chat.id, message.from_user.id))
    await message.answer("Iltimos, logotipni rasm yoki rasm fayli sifatida yuboring:")


@router.message(F.photo | F.document)
async def handle_logo_upload(message: types.Message) -> None:
    """Handle a logo upload.

    Downloads the image, normalizes it to PNG, saves it in ``logos/``, and
    records the path in the database.
    """
    if message.from_user is None:
        return
    upload_key = (message.chat.id, message.from_user.id)
    if upload_key not in _pending_logo_uploads:
        return

    file_id: Optional[str] = None
    if message.photo:
        file_id = message.photo[-1].file_id
    elif message.document:
        if not message.document.mime_type or not message.document.mime_type.startswith("image/"):
            await message.answer(
                "Iltimos, rasm faylini yuboring."
            )
            return
        file_id = message.document.file_id

    if not file_id:
        await message.answer(
            "Iltimos, rasm yoki rasm faylini yuboring."
        )
        return

    file = await message.bot.download(file_id, destination=BytesIO())
    if file is None:
        await message.answer("Rasmni yuklab bo‘lmadi. Iltimos, qayta urinib ko‘ring.")
        return

    try:
        with Image.open(file) as image:
            image.load()
            normalized_image = image.convert("RGBA")
    except (UnidentifiedImageError, OSError):
        await message.answer("Yuborilgan fayl yaroqli rasm emas. Qayta urinib ko‘ring.")
        return

    os.makedirs(LOGOS_DIR, exist_ok=True)
    logo_path = os.path.join(LOGOS_DIR, f"{message.chat.id}.png")
    temporary_path = f"{logo_path}.tmp"
    normalized_image.save(temporary_path, format="PNG")
    os.replace(temporary_path, logo_path)

    await save_logo_path(message.chat.id, logo_path, file_id)
    _pending_logo_uploads.discard(upload_key)

    await message.answer("Logotip muvaffaqiyatli saqlandi! ✅")