import random
import unittest


from backend.standings import calculate_standings
from backend.week_engine import play_week
from backend.demo_data import sample_season




class WeekEngineTests(unittest.TestCase):
    def test_first_week_feeds_standings(self):
        fixtures, teams = sample_season()
        result = play_week(1, fixtures, teams, [], rng=random.Random(7))

        self.assertTrue(result["valid"])
        matches = result["matches"]
        self.assertEqual([m["match_id"] for m in matches], [1, 2])
        self.assertEqual(
            [(m["home_club_id"], m["away_club_id"]) for m in matches],
            [(10, 40), (20, 30)],
        )

        for game in matches:
            self.assertEqual(game["week_no"], 1)
            self.assertEqual(len(game["player_stats"]), 22)

        table = calculate_standings(teams.keys(), matches)
        self.assertTrue(all(row["played"] == 1 for row in table))
        self.assertEqual(
            sum(row["goals_for"] for row in table),
            sum(m["home_goals"] + m["away_goals"] for m in matches),
        )

    def test_invalid_second_match_returns_no_partial_week(self):
        fixtures, teams = sample_season()
        teams[30]["selections"].pop()

        result = play_week(1, fixtures, teams, [], rng=random.Random(7))

        self.assertFalse(result["valid"])
        self.assertNotIn("matches", result)
        self.assertEqual(result["errors"][0]["away_club_id"], 30)
        self.assertIn("away", result["errors"][0]["details"])
        self.assertTrue(all("home_goals" not in game for game in fixtures))

    def test_week_outside_fixture(self):
        fixtures, teams = sample_season()
        result = play_week(7, fixtures, teams, [])

        self.assertFalse(result["valid"])
        self.assertNotIn("matches", result)

    def test_club_cannot_play_twice_in_same_week(self):
        fixtures, teams = sample_season()
        fixtures[1]["home_club_id"] = fixtures[0]["home_club_id"]

        result = play_week(1, fixtures, teams, [])

        self.assertFalse(result["valid"])
        self.assertIn("aynı haftada", result["errors"][0])


if __name__ == "__main__":
    unittest.main()