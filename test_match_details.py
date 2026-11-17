import random
import unittest

from backend.match_details import build_match_details


class MatchDetailsTests(unittest.TestCase):
    def setUp(self):
        self.home = {
            i: {"shooting": 70, "passing": 60}
            for i in range(101, 112)
        }
        self.away = {
            i: {"shooting": 65, "passing": 75}
            for i in range(201, 212)
        }

    def test_three_goals_match_player_totals(self):
        match = {
            "home_goals": 3,
            "away_goals": 0,
            "events": [
                {"minute": m, "team": "home", "event_type": "GOAL"}
                for m in (29, 59, 88)
            ],
        }
        result = build_match_details(match, self.home, self.away, rng=random.Random(7))
        goals = [e for e in result["events"] if e["event_type"] == "GOAL"]
        assists = [e for e in result["events"] if e["event_type"] == "ASSIST"]

        self.assertEqual([g["minute"] for g in goals], [29, 59, 88])
        self.assertTrue(all(g["player_id"] in self.home for g in goals))
        self.assertEqual(sum(p["goals"] for p in result["player_stats"]), 3)
        self.assertEqual(sum(p["assists"] for p in result["player_stats"]), len(assists))

        scorers = {g["minute"]: g["player_id"] for g in goals}
        for assist in assists:
            self.assertIn(assist["player_id"], self.home)
            self.assertNotEqual(assist["player_id"], scorers[assist["minute"]])

    def test_goalless_match_keeps_all_player_stats(self):
        match = {"home_goals": 0, "away_goals": 0, "events": []}
        result = build_match_details(match, self.home, self.away)

        self.assertEqual(result["events"], [])
        self.assertEqual(len(result["player_stats"]), 22)
        for player in result["player_stats"]:
            self.assertEqual(player["minutes_played"], 90)
            self.assertEqual((player["goals"], player["assists"]), (0, 0))

    def test_rejects_score_without_matching_goals(self):
        match = {"home_goals": 1, "away_goals": 0, "events": []}

        with self.assertRaisesRegex(ValueError, "Skor"):
            build_match_details(match, self.home, self.away)

    def test_rejects_player_on_both_teams(self):
        self.away[101] = self.away.pop(201)
        match = {"home_goals": 0, "away_goals": 0, "events": []}

        with self.assertRaisesRegex(ValueError, "iki takımda"):
            build_match_details(match, self.home, self.away)


if __name__ == "__main__":
    unittest.main()