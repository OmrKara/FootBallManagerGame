import unittest

from backend.player_stats import summarize_player_stats


def player_stat(player_id, team, goals, assists):
    return {
        "player_id": player_id,
        "team": team,
        "minutes_played": 90,
        "goals": goals,
        "assists": assists,
    }


class PlayerStatsTests(unittest.TestCase):
    def setUp(self):
        self.matches = [
            {
                "home_club_id": 10,
                "away_club_id": 20,
                "player_stats": [
                    player_stat(101, "home", 2, 0),
                    player_stat(201, "away", 0, 1),
                ],
            },
            {
                "home_club_id": 20,
                "away_club_id": 40,
                "player_stats": [
                    player_stat(201, "home", 0, 2),
                    player_stat(101, "away", 1, 0),
                    player_stat(401, "away", 0, 1),
                ],
            },
        ]

    def test_season_totals(self):
        rows = summarize_player_stats(self.matches)

        self.assertEqual(rows[0], {
            "player_id": 101,
            "matches_played": 2,
            "minutes_played": 180,
            "goals": 3,
            "assists": 0,
        })

    def test_club_filter_uses_club_at_match_time(self):
        rows = summarize_player_stats(self.matches, club_id=40)
        by_id = {row["player_id"]: row for row in rows}

        self.assertEqual(set(by_id), {101, 401})
        self.assertEqual(by_id[101]["matches_played"], 1)
        self.assertEqual(by_id[101]["goals"], 1)

    def test_assist_order_and_minimum_matches(self):
        rows = summarize_player_stats(
            self.matches, sort_by="assists", min_matches=2
        )

        self.assertEqual([row["player_id"] for row in rows], [201, 101])
        self.assertEqual(rows[0]["assists"], 3)

    def test_season_without_matches(self):
        self.assertEqual(summarize_player_stats([]), [])