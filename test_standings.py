import unittest

from backend.standings import calculate_standings


def match(match_id, home_id, away_id, home_goals, away_goals):
    return {
        "match_id": match_id,
        "home_club_id": home_id,
        "away_club_id": away_id,
        "home_goals": home_goals,
        "away_goals": away_goals,
    }


class StandingsTests(unittest.TestCase):
    def test_home_win_and_idle_club(self):
        rows = calculate_standings([1, 2, 3], [match(10, 1, 2, 5, 3)])
        by_id = {row["club_id"]: row for row in rows}

        self.assertEqual([row["club_id"] for row in rows], [1, 3, 2])
        self.assertEqual(by_id[1]["points"], 3)
        self.assertEqual(by_id[1]["goal_difference"], 2)
        self.assertEqual(by_id[2]["lost"], 1)
        self.assertEqual(by_id[2]["goals_for"], 3)
        self.assertEqual(by_id[3]["played"], 0)

    def test_draw_and_away_win_accumulate(self):
        matches = [
            match(10, 1, 2, 0, 0),
            match(11, 1, 2, 1, 2),
        ]
        rows = calculate_standings([1, 2], matches)
        leader = rows[0]

        self.assertEqual(leader["club_id"], 2)
        self.assertEqual(leader["played"], 2)
        self.assertEqual(leader["drawn"], 1)
        self.assertEqual(leader["won"], 1)
        self.assertEqual(leader["points"], 4)
        self.assertEqual(rows[1]["points"], 1)

    def test_duplicate_match_rejected(self):
        game = match(10, 1, 2, 5, 3)

        with self.assertRaisesRegex(ValueError, "iki kez"):
            calculate_standings([1, 2], [game, game])

    def test_unplayed_match_rejected(self):
        with self.assertRaisesRegex(ValueError, "gol sayıları"):
            calculate_standings([1, 2], [match(10, 1, 2, None, None)])

    def test_equal_points_use_goal_difference_then_goals_for(self):
        matches = [
            match(10, 1, 4, 1, 0),
            match(11, 2, 5, 3, 2),
            match(12, 3, 6, 2, 0),
        ]
        rows = calculate_standings([1, 2, 3, 4, 5, 6], matches)

        self.assertEqual([row["club_id"] for row in rows[:3]], [3, 2, 1])


if __name__ == "__main__":
    unittest.main()