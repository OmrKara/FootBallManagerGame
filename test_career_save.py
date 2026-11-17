import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from backend.career_save import dump_career, load_career
from backend.season_api import Career


class CareerSaveTests(unittest.TestCase):
    def advance(self, career):
        result = career.season.advance_week(career.season.next_week, rng=career.rng)
        self.assertTrue(result["valid"])
        return result

    def test_transfer_and_next_match_survive_file_round_trip(self):
        career = Career()
        teams = career.season.teams
        offer = career.offers.create(teams, 10, 2011, 400_000, 1)
        career.offers.resolve(teams, offer["offer_id"], 10, 1)
        teams[10]["selections"][0]["player_id"] = 2011
        self.advance(career)
        with TemporaryDirectory() as folder:
            path = Path(folder) / "career.json"
            path.write_text(dump_career(career), encoding="utf-8")
            loaded = load_career(path.read_text(encoding="utf-8"))

        self.assertEqual(loaded.season.next_week, 2)
        self.assertEqual(loaded.season.teams, teams)
        self.assertEqual(loaded.season.teams[10]["budget"], 1_600_000)
        self.assertEqual(loaded.season.completed_matches, career.season.completed_matches)
        self.assertEqual(loaded.offers.transfers, career.offers.transfers)
        self.assertEqual(self.advance(loaded), self.advance(career))

    def test_archive_development_and_pending_offer_survive(self):
        career = Career()
        pending = career.offers.create(career.season.teams, 10, 3011, 400_000, 1)
        while not career.season.finished:
            self.advance(career)
        loaded = load_career(dump_career(career))
        self.assertTrue(loaded.season.finished)
        self.assertEqual(loaded.season.teams, career.season.teams)
        loaded.start_next_season(1)
        restored = load_career(dump_career(loaded))
        self.assertEqual(restored.season_no, 2)
        self.assertEqual(restored.history[1]["matches"], career.season.completed_matches)
        self.assertEqual(restored.history[1]["standings"], career.season.standings())
        restored.offers.resolve(restored.season.teams, pending["offer_id"], 10, 1, season_no=2)
        next_offer = restored.offers.create(restored.season.teams, 10, 4011, 400_000, 1)
        self.assertEqual(next_offer["offer_id"], pending["offer_id"] + 1)
        self.assertEqual(loaded.offers.offers[pending["offer_id"]]["status"], "PENDING")
