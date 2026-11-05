import os
import tempfile
import unittest
from unittest.mock import patch

import database


class DatabaseTests(unittest.IsolatedAsyncioTestCase):
    async def test_upserts_and_logo_persistence(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            db_path = os.path.join(directory, "nested", "bot.db")
            logo_path = os.path.join(directory, "logo.png")
            with (
                patch.object(database, "DB_PATH", db_path),
                patch.object(database, "LOGOS_DIR", os.path.join(directory, "logos")),
                patch.object(database, "TMP_DIR", os.path.join(directory, "tmp")),
            ):
                await database.init_db()
                await database.upsert_user(10, username="first", is_admin=True)
                await database.upsert_user(10, username="updated", is_admin=False)
                self.assertTrue(await database.is_admin(10))

                with open(logo_path, "wb") as logo:
                    logo.write(b"png data")
                await database.save_logo_path(10, logo_path, "telegram-file-id")
                self.assertEqual(await database.get_logo_path(10), logo_path)

                await database.delete_logo_path(10)
                self.assertIsNone(await database.get_logo_path(10))
                self.assertFalse(os.path.exists(logo_path))

    async def test_upsert_and_init_are_repeatable(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            db_path = os.path.join(directory, "bot.db")
            with (
                patch.object(database, "DB_PATH", db_path),
                patch.object(database, "LOGOS_DIR", os.path.join(directory, "logos")),
                patch.object(database, "TMP_DIR", os.path.join(directory, "tmp")),
            ):
                await database.init_db()
                await database.init_db()
                await database.upsert_user(20)
                await database.upsert_user(20, first_name="Updated")
                self.assertFalse(await database.is_admin(20))


if __name__ == "__main__":
    unittest.main()
