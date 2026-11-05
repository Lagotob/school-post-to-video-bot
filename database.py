"""Asynchronous SQLite persistence layer (``aiosqlite``).

Tables:
    users            — one row per Telegram chat that has interacted with the bot.
    organization_configs — custom logo paths keyed by chat id.
"""

from __future__ import annotations

import os
from typing import Optional

import aiosqlite

from config import LOGOS_DIR, TMP_DIR

# Database file location. Kept in the project root by default.
DB_PATH: str = os.getenv("DB_PATH", "bot_data.db")


async def init_db() -> None:
    """Create the database file and all required tables if missing.

    Safe to call repeatedly on every bot startup — it uses ``CREATE TABLE
    IF NOT EXISTS`` so it never drops existing data.
    """
    # Make sure the directories the bot relies on exist before any writes.
    for directory in (LOGOS_DIR, TMP_DIR):
        os.makedirs(directory, exist_ok=True)

    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                chat_id      INTEGER PRIMARY KEY,
                username     TEXT,
                first_name   TEXT,
                last_name    TEXT,
                is_admin     INTEGER NOT NULL DEFAULT 0,
                created_at   TEXT    NOT NULL DEFAULT (datetime('now'))
            )
            """
        )
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS organization_configs (
                chat_id       INTEGER PRIMARY KEY,
                logo_path     TEXT,
                logo_file_id  TEXT,
                updated_at    TEXT NOT NULL DEFAULT (datetime('now')),
                FOREIGN KEY (chat_id) REFERENCES users(chat_id) ON DELETE CASCADE
            )
            """
        )
        await db.commit()


async def upsert_user(
    chat_id: int,
    username: Optional[str] = None,
    first_name: Optional[str] = None,
    last_name: Optional[str] = None,
    is_admin: bool = False,
) -> None:
    """Insert or update a user row, preserving admin status when already set."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            INSERT INTO users (chat_id, username, first_name, last_name, is_admin)
            VALUES (?, ?, ?, ?, ?)
            ON CON(chat_id) DO UPDATE SET
                username    = excluded.username,
                first_name  = excluded.first_name,
                last_name   = excluded.last_name,
                is_admin    = CASE
                                WHEN users.is_admin = 1 THEN 1
                                ELSE excluded.is_admin
                              END
            """,
            (
                chat_id,
                username,
                first_name,
                last_name,
                1 if is_admin else 0,
            ),
        )
        await db.commit()


async def is_admin(chat_id: int) -> bool:
    """Return ``True`` when ``chat_id`` is a known administrator."""
    async with aiosqlite.connect(DB_PATH) as path_db:
        cursor = await path_db.execute(
            "SELECT is_admin FROM users WHERE chat_id = ?", (chat_id,)
        )
        row = await cursor.fetchone()
        await cursor.close()
    return bool(row and row[0] == 1)


async def get_logo_path(chat_id: int) -> Optional[str]:
    """Return the stored custom logo path for ``chat_id`` or ``None``."""
    async with aiosqlite.connect(DB_PATH) as path_db:
        cursor = await path_db.execute(
            "SELECT logo_path FROM organization_configs WHERE chat_id = ?",
            (chat_id,),
        )
        row = await cursor.fetchone()
        await cursor.close()
    if row is None:
        return None
    value = row[0]
    # Only return paths that actually exist on disk — a stale record is worse
    # than no record at all.
    if value and os.path.exists(value):
        return value
    return None


async def save_logo_path(chat_id: int, logo_path: str, logo_file_id: Optional[str] = None) -> None:
    """Persist a freshly uploaded logo for ``chat_id``."""
    async with aiosqlite.connect(DB_PATH) as path_db:
        await path_db.execute(
            """
            INSERT INTO organization_configs (chat_id, logo_path, logo_file_id)
            VALUES (?, ?, ?)
            ON CON(chat_id) DO UPDATE SET
                logo_path    = excluded.logo_path,
                logo_file_id = excluded.logo_file_id,
                updated_at   = datetime('now')
            """,
            (chat_id, logo_path, logo_file_id),
        )
        await path_db.commit()


async def delete_logo_path(chat_id: int) -> None:
    """Remove a stored custom logo record (and its file on disk)."""
    async with aiosqlite.connect(DB_PATH) as path_db:
        cursor = await path_db.execute(
            "SELECT logo_path FROM organization_configs WHERE chat_id = ?",
            (chat_id,),
        )
        row = await cursor.fetchone()
        await cursor.close()
        if row and row[0] and os.path.exists(row[0]):
            try:
                os.remove(row[0])
            except OSError:
                # Best-effort cleanup — a missing file should not break the flow.
                pass
        await path_db.execute(
            "DELETE FROM organization_configs WHERE chat_id = ?", (chat_id,)
        )
        await path_db.commit()