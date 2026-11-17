from threading import Lock
from typing import Protocol


class UsernameTaken(ValueError):
    pass


class UserStore(Protocol):
    def create(self, username: str, salt: bytes, password_hash: bytes) -> dict:
        ...

    def find_by_username(self, username: str) -> dict | None:
        ...


class MemoryUserStore:
    def __init__(self):
        self._users = {}
        self._next_id = 1
        self._lock = Lock()

    def create(self, username: str, salt: bytes, password_hash: bytes) -> dict:
        with self._lock:
            if username in self._users:
                raise UsernameTaken(username)

            user = {
                "user_id": self._next_id,
                "username": username,
                "salt": salt,
                "password_hash": password_hash,
            }
            self._users[username] = user
            self._next_id += 1
            return user.copy()

    def find_by_username(self, username: str) -> dict | None:
        with self._lock:
            user = self._users.get(username)
            return user.copy() if user is not None else None