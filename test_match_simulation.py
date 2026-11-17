import random
import unittest
from unittest.mock import Mock

from backend.match_simulation import simulate_match


class MatchSimulationTests(unittest.TestCase):
    def setUp(self):
        self.home = {"DEF": 60, "MID": 60, "ATT": 60}
        self.away = {"DEF": 60, "MID": 60, "ATT": 60}

    def test_score_matches_goal_events(self):
        result = simulate_match(self.home, self.away, rng=random.Random(7))
        events = result["events"]

        self.assertEqual(result["home_goals"], sum(e["team"] == "home" for e in events))
        self.assertEqual(result["away_goals"], sum(e["team"] == "away" for e in events))

        minutes = [e["minute"] for e in events]
        self.assertEqual(minutes, sorted(minutes))
        self.assertTrue(all(1 <= minute <= 90 for minute in minutes))

    def test_stronger_attack_can_convert_same_chance(self):
        # Her fırsat ev sahibine gidiyor. Gol için çekilen sayı hep 0.18.
        def fixed_draws():
            rng = Mock()
            rng.random.side_effect = [0.1, 0.18] * 18
            rng.randint.side_effect = lambda first, last: first
            return rng

        equal = simulate_match(self.home, self.away, rng=fixed_draws())

        self.home["ATT"] = 120
        stronger = simulate_match(self.home, self.away, rng=fixed_draws())

        # Eşit güçte gol ihtimali 0.15, hücum iki katına çıkınca 0.20.
        self.assertEqual(equal["home_goals"], 0)
        self.assertEqual(stronger["home_goals"], 18)
        self.assertEqual(stronger["events"][0], {
            "minute": 1, "team": "home", "event_type": "GOAL"
        })

    def test_away_team_can_score(self):
        rng = Mock()
        rng.random.side_effect = [0.9, 0.01] * 18
        rng.randint.side_effect = lambda first, last: last

        result = simulate_match(self.home, self.away, rng=rng)

        self.assertEqual(result["home_goals"], 0)
        self.assertEqual(result["away_goals"], 18)
        self.assertEqual(result["events"][-1], {
            "minute": 90, "team": "away", "event_type": "GOAL"
        })

    def test_invalid_power(self):
        self.home["DEF"] = -5

        with self.assertRaises(ValueError):
            simulate_match(self.home, self.away)


if __name__ == "__main__":
    unittest.main()