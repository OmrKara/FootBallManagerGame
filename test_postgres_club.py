import sqlite3
import unittest
from contextlib import closing

import test_postgres_career_load as block3
from backend.postgres_club import ClubConflict, name_sql_club, save_sql_lineup


class SqlClubTests(unittest.TestCase):
    def setUp(self):
        self.fixture = block3.CareerLoadTests()
        self.addCleanup(self.fixture.doCleanups)
        self.fixture.setUp()
        self.fixture.create(1)
        self.connect = self.fixture.connect
        self.before = self.team()
        self.picks = [s.copy() for s in self.before["selections"]]
        self.picks[0]["player_id"] = 1011

    def team(self):
        return self.fixture.load(1).season.teams[10]

    def save(self, picks):
        return save_sql_lineup(1, picks, 1, 1, "4-4-2", connect=self.connect)

    def test_name_once_and_per_career(self):
        def name(text):
            return name_sql_club(1, text, connect=self.connect)
        with self.assertRaises(ValueError):
            name("  ")
        with self.assertRaises(ClubConflict):
            name("bot 20")
        self.assertEqual(name("  Ankara  Yıldızları ")["name"], "Ankara Yıldızları")
        self.assertEqual(name("Ankara Yıldızları")["name"], self.team()["name"])
        with self.assertRaises(ClubConflict):
            name("Yeni ad")
        self.fixture.create(2)
        self.assertEqual(name_sql_club(2, "Ankara Yıldızları", connect=self.connect)["club_id"], 10)

    def test_valid_lineup_and_formation(self):
        result = self.save(self.picks)
        team = self.team()
        self.assertTrue(result["power"]["valid"])
        self.assertEqual(team["formation"], "4-4-2")
        self.assertEqual(team["selections"], self.picks)
        self.assertEqual(team["formation_slots"][8], "ST")

    def test_invalid_and_stale_keep_lineup(self):
        self.picks[0]["player_id"] = 2000
        with self.assertRaises(ValueError):
            self.save(self.picks)
        with self.assertRaises(ClubConflict):
            save_sql_lineup(1, self.picks, 2, 1, connect=self.connect)
        self.assertEqual(self.team(), self.before)

    def test_final_slot_failure_rolls_back(self):
        with closing(self.connect()) as db:
            db.execute("""CREATE TRIGGER public.stop_slot BEFORE INSERT ON lineup_selection
                          WHEN NEW.slot_id=11 BEGIN SELECT RAISE(ABORT,'failure'); END""")
        with self.assertRaises(sqlite3.IntegrityError):
            self.save(self.picks)
        self.assertEqual(self.team(), self.before)
        with closing(self.connect()) as db:
            db.execute("DROP TRIGGER public.stop_slot")
        self.assertEqual(self.save(self.picks)["selections"], self.picks)
