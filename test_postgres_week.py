import unittest
from contextlib import closing
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

import test_postgres_career_load as block3
from backend.postgres_week import advance_sql_week, read_week_career, WeekConflict


class SqlWeekTests(unittest.TestCase):
    def setUp(self):
        self.fixture = block3.CareerLoadTests()
        self.addCleanup(self.fixture.doCleanups)
        self.fixture.setUp()
        self.connect = self.fixture.connect
        sql = (Path(__file__).parent / "docs/hafta_kaydi.sql").read_text(encoding="utf-8")
        with closing(self.connect()) as db:
            db.executescript(sql.replace("REFERENCES public.", "REFERENCES "))
        self.original = self.fixture.create(1)

    def load(self):
        with closing(self.connect()) as db:
            db.execute("BEGIN")
            return read_week_career(db.cursor(), 1)

    def advance(self, week):
        return advance_sql_week(1, 1, week, connect=self.connect)

    def test_reload_including_final_development(self):
        for week in range(1, 7):
            expected = self.original.season.advance_week(week, rng=self.original.rng)
            self.assertEqual(self.advance(week), expected)
            loaded = self.load()
            self.assertEqual(loaded.season.completed_matches, self.original.season.completed_matches)
            self.assertEqual(loaded.season.teams, self.original.season.teams)
            self.assertEqual(loaded.season.next_week, self.original.season.next_week)
            self.assertEqual(loaded.rng.getstate(), self.original.rng.getstate())

    def test_concurrent_retry(self):
        def request(_):
            try:
                return self.advance(1)["valid"]
            except WeekConflict:
                return False
        with ThreadPoolExecutor(2) as pool:
            self.assertEqual(sorted(pool.map(request, range(2))), [False, True])
        self.assertEqual(len(self.load().season.completed_matches), 2)

    def test_failure_on_second_match_rolls_back(self):
        import sqlite3
        with closing(self.connect()) as db:
            db.execute("""CREATE TRIGGER public.stop_second BEFORE INSERT ON match_player_stat
                          WHEN NEW.match_id=2 BEGIN SELECT RAISE(ABORT,'failure'); END""")
            db.commit()
        with self.assertRaises(sqlite3.IntegrityError):
            self.advance(1)
        loaded = self.load()
        self.assertEqual(loaded.season.next_week, 1)
        self.assertEqual(loaded.season.completed_matches, [])
        self.assertEqual(loaded.rng.getstate(), self.original.rng.getstate())
        with closing(self.connect()) as db:
            db.execute("DROP TRIGGER public.stop_second")
            db.commit()
        self.assertTrue(self.advance(1)["valid"])
