import unittest

from backend.formation_stats import summarize_formation_stats


def game(home, away, home_goals, away_goals, home_formation, away_formation):
    return {
        "home_club_id": home,
        "away_club_id": away,
        "home_goals": home_goals,
        "away_goals": away_goals,
        "formations": {"home": home_formation, "away": away_formation},
    }


class FormationStatsTests(unittest.TestCase):
    def test_home_and_away_results_use_clubs_own_formation(self):
        matches = [
            game(10, 20, 2, 0, "4-4-2", "4-3-3"),
            game(30, 10, 1, 1, "4-3-3", "4-4-2"),
            game(40, 10, 3, 1, "4-4-2", "4-3-3"),
            game(20, 30, 5, 0, "4-4-2", "4-4-2"),
        ]

        rows = summarize_formation_stats(matches, 10)

        self.assertEqual(rows, [
            {
                "formation": "4-4-2", "played": 2,
                "won": 1, "drawn": 1, "lost": 0,
                "goals_for": 3, "goals_against": 1, "win_pct": 50.0,
            },
            {
                "formation": "4-3-3", "played": 1,
                "won": 0, "drawn": 0, "lost": 1,
                "goals_for": 1, "goals_against": 3, "win_pct": 0.0,
            },
        ])

    def test_no_matches_for_club(self):
        matches = [game(20, 30, 2, 1, "4-3-3", "4-4-2")]
        self.assertEqual(summarize_formation_stats(matches, 10), [])