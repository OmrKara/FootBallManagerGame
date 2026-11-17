from threading import Lock
from typing import Protocol

from backend.career import Career
from backend.career_save import dump_career, load_career


class CareerStore(Protocol):
    def load(self, user_id: int) -> Career | None: ...
    def save(self, user_id: int, career: Career) -> None: ...


class MemoryCareerStore:
    def __init__(self):
        self._records: dict[int, str] = {}
        self._lock = Lock()

    def load(self, user_id: int) -> Career | None:
        with self._lock:
            record = self._records.get(user_id)
        return None if record is None else load_career(record)

    def save(self, user_id: int, career: Career) -> None:
        record = dump_career(career)
        with self._lock:
            self._records[user_id] = record
