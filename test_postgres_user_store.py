import os
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from backend.postgres_user_store import PostgresUserStore, configured_user_store
from backend.user_store import MemoryUserStore, UsernameTaken


class PostgresUserStoreTests(unittest.TestCase):
    def setUp(self):
        directory = self.enterContext(tempfile.TemporaryDirectory())
        path = Path(directory) / "accounts.db"

        def connect():
            db = sqlite3.connect(":memory:")
            db.execute("ATTACH DATABASE ? AS public", (str(path),))
            return db

        self.connect = connect
        db = connect()
        try:
            db.execute("""CREATE TABLE public.user_account (
                user_id INTEGER PRIMARY KEY, username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL)""")
            db.commit()
        finally:
            db.close()
        self.store = PostgresUserStore(connect)

    def test_save_and_read_through_another_connection(self):
        name = "Ece'nin kulübü"
        created = self.store.create(name, b"salt", b"digest")
        self.assertEqual(PostgresUserStore(self.connect).find_by_username(name), created)
        self.assertIsNone(self.store.find_by_username("unknown"))

    def test_duplicate_rolls_back_and_preserves_original(self):
        original = self.store.create("deniz", b"abc", b"123")
        with self.assertRaises(UsernameTaken):
            self.store.create("deniz", b"other", b"456")
        self.assertEqual(self.store.find_by_username("deniz"), original)
        second = self.store.create("ece", b"b", b"c")
        self.assertNotEqual(second["user_id"], original["user_id"])

    def test_store_mode_is_explicit(self):
        with patch.dict(os.environ, {"BIL372_USER_STORE": "memory"}):
            self.assertIsInstance(configured_user_store(), MemoryUserStore)
        with patch.dict(os.environ, {"BIL372_USER_STORE": "typo"}):
            with self.assertRaises(ValueError):
                configured_user_store()
