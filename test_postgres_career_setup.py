import sqlite3
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from pathlib import Path
from random import Random
from types import SimpleNamespace
from unittest.mock import Mock

from backend.demo_data import sample_season
from backend.postgres_career_setup import ensure_career


def world(club_id):
    fixtures, teams = sample_season()
    for cid, team in teams.items():
        team["name"] = None if cid == club_id else f"Bot {cid}"
        for pid, p in team["players"].items():
            p.update(first_name="Test", last_name=str(pid), element=None)
    rule = dict(element="Fire", required_count=4, defense_bonus_pct=0,
                midfield_bonus_pct=0, attack_bonus_pct=5)
    season = SimpleNamespace(fixtures=fixtures, teams=teams, bonus_rules=[rule],
                             next_week=1, last_week=6)
    return SimpleNamespace(season=season, season_no=1, rng=Random(7))


class CareerSetupTests(unittest.TestCase):
    def setUp(self):
        self.path = Path(self.enterContext(tempfile.TemporaryDirectory())) / "world.db"
        sql = (Path(__file__).parent / "docs/kariyer_baslangic.sql").read_text(encoding="utf-8")
        with closing(self.connect()) as db:
            db.execute("CREATE TABLE public.user_account (user_id INTEGER PRIMARY KEY)")
            db.executemany("INSERT INTO public.user_account VALUES (?)", [(1,), (2,)])
            # SQLite, REFERENCES içinde şema ön ekine izin vermez.
            db.executescript(sql.replace("REFERENCES public.", "REFERENCES "))
            db.commit()

    def connect(self):
        db = sqlite3.connect(":memory:", timeout=10)
        db.execute("PRAGMA foreign_keys=ON")
        db.execute("ATTACH DATABASE ? AS public", (str(self.path),))
        return db

    def test_complete_world_and_isolated_ids(self):
        for uid in (1, 2):
            ensure_career(uid, connect=self.connect, make_career=world)
        with closing(self.connect()) as db:
            for table, count in [("club", 4), ("player", 48), ("lineup_selection", 44),
                                 ("fixture", 12), ("season", 1), ("career_bonus_rule", 1)]:
                rows = db.execute(f"SELECT count(*) FROM public.{table} GROUP BY career_id").fetchall()
                self.assertEqual(rows, [(count,), (count,)])
            self.assertGreater(db.execute("SELECT count(*) FROM public.player_position WHERE career_id=1").fetchone()[0], 48)

    def test_concurrent_first_requests_generate_once(self):
        factory = Mock(side_effect=world)
        def create(_):
            return ensure_career(1, connect=self.connect, make_career=factory)
        with ThreadPoolExecutor(2) as pool:
            self.assertEqual(list(pool.map(create, range(2))), [1, 1])
        factory.assert_called_once_with(10)

    def test_invalid_last_fixture_rolls_back_and_retry_succeeds(self):
        broken = world(10)
        broken.season.fixtures[-1]["home_club_id"] = 999
        with self.assertRaises(sqlite3.IntegrityError):
            ensure_career(1, connect=self.connect, make_career=lambda _: broken)
        with closing(self.connect()) as db:
            for table in ("career", "club", "player", "fixture", "lineup_selection"):
                self.assertEqual(db.execute(f"SELECT count(*) FROM public.{table}").fetchone()[0], 0)
        self.assertEqual(ensure_career(1, connect=self.connect, make_career=world), 1)
