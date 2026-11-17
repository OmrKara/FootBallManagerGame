import unittest
from random import Random
from unittest.mock import Mock

from backend.demo_data import sample_season
from backend.player_development import develop_players, season_change
from backend.season_engine import SeasonEngine


class PlayerDevelopmentTests(unittest.TestCase):
    def test_young_player_needs_playing_time(self):
        self.assertEqual(season_change(23, True, 0, None), 1)
        self.assertEqual(season_change(23, False, 3, None), 0)

    def test_middle_age_random_change(self):
        rng = Mock()
        rng.random.side_effect = [0.10, 0.50, 0.90]
        self.assertEqual(season_change(24, True, 0, rng), -1)
        self.assertEqual(season_change(29, True, 0, rng), 0)
        self.assertEqual(season_change(34, True, 0, rng), 1)

    def test_veteran_declines_but_good_season_offsets_it(self):
        self.assertEqual(season_change(35, True, 2, None), -1)
        self.assertEqual(season_change(36, True, 3, None), 0)

    def test_goals_and_assists_combine_for_striker(self):
        _, teams = sample_season()
        striker = teams[10]["players"][1009]
        old_shooting = striker["shooting"]
        old_passing = striker["passing"]
        match = {
            "home_club_id": 10,
            "away_club_id": 20,
            "player_stats": [{"player_id": 1009, "minutes_played": 90}],
            "events": [
                {"player_id": 1009, "event_type": "GOAL"},
                {"player_id": 1009, "event_type": "GOAL"},
                {"player_id": 1009, "event_type": "ASSIST"},
            ],
        }

        develop_players(teams, [match], rng=Random(7))

        self.assertEqual(striker["shooting"], old_shooting + 2)
        self.assertEqual(striker["passing"], old_passing)
        self.assertEqual(striker["age"], 24)

    def test_players_age_only_once_after_last_week(self):
        fixtures, teams = sample_season()
        season = SeasonEngine(fixtures, teams, [])
        rng = Random(7)
        keeper = teams[10]["players"][1000]
        old_age = keeper["age"]

        for week in range(1, season.last_week):
            result = season.advance_week(week, rng=rng)
            self.assertTrue(result["valid"])
            self.assertEqual(keeper["age"], old_age)

        result = season.advance_week(season.last_week, rng=rng)
        self.assertTrue(result["valid"])
        self.assertEqual(keeper["age"], old_age + 1)

        repeated = season.advance_week(season.last_week, rng=rng)
        self.assertFalse(repeated["valid"])
        self.assertEqual(keeper["age"], old_age + 1)