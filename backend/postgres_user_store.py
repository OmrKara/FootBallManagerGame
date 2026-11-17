"""Kullanıcı deposu. Her işlem kendi ODBC bağlantısını kullanır."""
import os
from contextlib import closing

from backend.user_store import MemoryUserStore, UsernameTaken


class PostgresUserStore:
    def __init__(self, connect=None):
        if connect is None:
            from backend.db import get_connection
            connect = get_connection
        self.connect = connect

    def create(self, username, salt, password_hash):
        encoded = f"{salt.hex()}:{password_hash.hex()}"
        with closing(self.connect()) as connection:
            try:
                with closing(connection.cursor()) as cursor:
                    cursor.execute(
                        """
                        INSERT INTO public.user_account (username, password_hash)
                        VALUES (?, ?)
                        ON CONFLICT (username) DO NOTHING
                        RETURNING user_id
                        """,
                        (username, encoded),
                    )
                    row = cursor.fetchone()
                    if row is None:
                        raise UsernameTaken(username)
                    user_id = row[0]
                connection.commit()
            except Exception:
                connection.rollback()
                raise

        return dict(user_id=user_id, username=username, salt=salt,
                    password_hash=password_hash)

    def find_by_username(self, username):
        with closing(self.connect()) as connection:
            with closing(connection.cursor()) as cursor:
                cursor.execute(
                    """
                    SELECT user_id, username, password_hash
                    FROM public.user_account
                    WHERE username = ?
                    """,
                    (username,),
                )
                row = cursor.fetchone()
        if row is None:
            return None
        salt, digest = row[2].split(":", 1)
        return dict(user_id=row[0], username=row[1], salt=bytes.fromhex(salt),
                    password_hash=bytes.fromhex(digest))


def configured_user_store():
    mode = os.environ.get("BIL372_USER_STORE", "memory").strip().lower()
    if mode == "memory":
        return MemoryUserStore()
    if mode == "postgres":
        return PostgresUserStore()
    raise ValueError("BIL372_USER_STORE yalnızca memory veya postgres olabilir.")
