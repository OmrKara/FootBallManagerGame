import sqlite3
import unittest
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing

from fastapi import HTTPException
import test_postgres_week as block4
from backend.postgres_week import advance_sql_week
from backend.postgres_season import start_sql_season, read_season_archive


class SqlSeasonTests(unittest.TestCase):
    def setUp(self):
        self.world = block4.SqlWeekTests()
        self.addCleanup(self.world.doCleanups)
        self.world.setUp()
        self.connect = self.world.connect

    def finish(self):
        for week in range(1, 7):
            self.world.advance(week)

    def start(self):
        return start_sql_season(1, 1, connect=self.connect)

    def archive(self, uid=1, number=1):
        with closing(self.connect()) as db:
            return read_season_archive(db.cursor(), uid, number)

    def test_archive_after_next_week_and_career_isolation(self):
        self.finish()
        final = self.world.load()
        new = self.start()
        self.assertEqual((new["season_no"], new["next_week"]), (2, 1))
        self.assertTrue(all(row["points"] == 0 for row in new["standings"]))
        self.assertEqual(self.world.load().season.teams, final.season.teams)
        advance_sql_week(1, 2, 1, connect=self.connect)
        archive = self.archive()
        self.assertEqual(archive["matches"], final.season.completed_matches)
        self.assertEqual(archive["standings"], final.season.standings())
        self.assertEqual(len(self.world.load().season.completed_matches), 2)
        with self.assertRaises(KeyError):
            self.archive(uid=2)
        with self.assertRaises(KeyError):
            self.archive(number=2)

    def test_early_and_concurrent_requests(self):
        with self.assertRaises(HTTPException) as early:
            self.start()
        self.assertEqual(early.exception.status_code, 409)
        self.finish()
        def request(_):
            try:
                return self.start()["season_no"]
            except HTTPException as error:
                return error.status_code
        with ThreadPoolExecutor(2) as pool:
            self.assertEqual(sorted(pool.map(request, range(2))), [2, 409])

    def test_failed_fixture_insert_can_retry(self):
        self.finish()
        with closing(self.connect()) as db:
            db.execute("""CREATE TRIGGER public.stop_fixture BEFORE INSERT ON fixture
                          WHEN NEW.season_no=2 AND NEW.match_id=12
                          BEGIN SELECT RAISE(ABORT,'failure'); END""")
        with self.assertRaises(sqlite3.IntegrityError):
            self.start()
        self.assertEqual(self.world.load().season_no, 1)
        with closing(self.connect()) as db:
            for table in ("fixture", "season"):
                count = db.execute(f"SELECT count(*) FROM public.{table} WHERE season_no=2").fetchone()[0]
                self.assertEqual(count, 0)
            db.execute("DROP TRIGGER public.stop_fixture")
        self.assertEqual(self.start()["season_no"], 2)
        self.assertEqual(len(self.archive()["matches"]), 12)
