import unittest
from random import Random
from unittest.mock import Mock

from backend.career_save import dump_career, load_career
from backend.club_generation import ATTRIBUTES, draw_element, new_user_career
from backend.transfer_market import list_market_players


class ClubGenerationTests(unittest.TestCase):
    def test_rosters_and_names(self):
        teams = new_user_career(10, Random(19)).season.teams
        names = [t["name"] for i, t in teams.items() if i != 10]
        self.assertEqual(len(set(names)), 3)
        self.assertIsNone(teams[10]["name"])
        players = [p for t in teams.values() for p in t["players"].values()]
        self.assertEqual(len({(p["first_name"], p["last_name"]) for p in players}), 48)
        for field in ATTRIBUTES:
            values = {p[field] for p in players}
            self.assertGreater(len(values), 1)
            self.assertTrue(all(50 <= v <= 90 for v in values))

    def test_element_boundary(self):
        rng = Mock()
        rng.random.side_effect = [0.69999, 0.70]
        rng.choice.return_value = "Air"
        self.assertEqual(draw_element(rng), "Air")
        self.assertIsNone(draw_element(rng))
        rng.choice.assert_called_once()

    def test_play_save_and_filter(self):
        career = new_user_career(10, Random(3))
        self.assertTrue(career.season.advance_week(1, rng=career.rng)["valid"])
        loaded = load_career(dump_career(career))
        self.assertEqual(loaded.season.teams, career.season.teams)
        players = list_market_players(loaded.season.teams, 10, element="none")
        self.assertTrue(players)
        self.assertTrue(all(p["element"] is None for p in players))
