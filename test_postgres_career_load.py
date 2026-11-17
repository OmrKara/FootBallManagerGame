import sqlite3
import unittest
from contextlib import closing
from pathlib import Path
from tempfile import TemporaryDirectory

from backend.career import Career
from backend.postgres_career_setup import ensure_career
from backend.postgres_career_load import read_initial_career


class CareerLoadTests(unittest.TestCase):
    def setUp(self):
        self.path = Path(self.enterContext(TemporaryDirectory())) / "world.db"
        sql = (Path(__file__).parent / "docs/kariyer_baslangic.sql").read_text(encoding="utf-8")
        with closing(self.connect()) as db:
            db.execute("CREATE TABLE public.user_account (user_id INTEGER PRIMARY KEY)")
            db.executescript(sql.replace("REFERENCES public.", "REFERENCES "))
            db.executemany("INSERT INTO public.user_account VALUES (?)", [(1,), (2,)])
            db.commit()

    def connect(self):
        db = sqlite3.connect(":memory:")
        db.execute("PRAGMA foreign_keys=ON")
        db.execute("ATTACH DATABASE ? AS public", (str(self.path),))
        return db

    def create(self, uid):
        career = Career()
        for cid, team in career.season.teams.items():
            team["name"] = None if cid == 10 else f"Bot {cid}"
            for pid, player in team["players"].items():
                player.update(first_name="Deniz", last_name=f"{uid}-{pid}")
        career.season.teams[10]["players"][1000]["element"] = None
        career.rng.random()
        ensure_career(uid, connect=self.connect, make_career=lambda _: career)
        return career

    def load(self, uid):
        with closing(self.connect()) as db:
            db.execute("BEGIN")
            return read_initial_career(db.cursor(), uid)

    def test_unknown_and_separate_careers(self):
        self.assertIsNone(self.load(1))
        self.create(1)
        self.assertIsNone(self.load(2))
        self.create(2)
        a = self.load(1).season.teams[10]["players"][1000]
        b = self.load(2).season.teams[10]["players"][1000]
        self.assertNotEqual(a["last_name"], b["last_name"])

    def test_round_trip_and_first_week(self):
        original = self.create(1)
        loaded = self.load(1)
        self.assertEqual(loaded.season.teams, original.season.teams)
        self.assertEqual(loaded.season.fixtures, original.season.fixtures)
        order = lambda r: (r["element"], r["required_count"])
        self.assertEqual(sorted(loaded.season.bonus_rules, key=order),
                         sorted(original.season.bonus_rules, key=order))
        self.assertEqual(loaded.rng.getstate(), original.rng.getstate())
        expected = original.season.advance_week(1, rng=original.rng)
        self.assertTrue(expected["valid"])
        self.assertEqual(loaded.season.advance_week(1, rng=loaded.rng), expected)

    def test_advanced_week_is_not_loaded_as_an_empty_season(self):
        self.create(1)
        with closing(self.connect()) as db:
            db.execute("UPDATE public.season SET next_week=2 WHERE career_id=1")
            db.commit()
        with self.assertRaises(ValueError):
            self.load(1)
