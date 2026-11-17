import unittest

from backend.career import Career
from backend.career_save import load_career, dump_career
from backend.match_rating import add_match_ratings
from backend.player_stats import summarize_player_stats


class MatchRatingTests(unittest.TestCase):
    def test_scoring_uses_position_and_opponents_goals(self):
        match = {
            "home_goals": 0, "away_goals": 1,
            "lineups": {"home": [{"player_id": 1, "position": "CB"}],
                        "away": [{"player_id": 2, "position": "GK"},
                                 {"player_id": 3, "position": "ST"}]},
            "player_stats": [
                dict(player_id=1, team="home", minutes_played=90, goals=0, assists=0),
                dict(player_id=2, team="away", minutes_played=90, goals=0, assists=1),
                dict(player_id=3, team="away", minutes_played=90, goals=1, assists=0),
            ],
        }
        add_match_ratings(match)
        self.assertEqual([s["rating"] for s in match["player_stats"]], [6.5, 7.5, 7.0])
        scorer = match["player_stats"][2]
        del scorer["rating"]
        scorer["goals"] = 5
        add_match_ratings(match)
        self.assertEqual(scorer["rating"], 10)

    def test_last_five_use_players_own_appearances(self):
        games = [dict(home_club_id=10, away_club_id=20, player_stats=[
            dict(player_id=1, team="home", minutes_played=90, goals=0, assists=0, rating=r)
        ]) for r in [10, 6, 6, 6, 6, 6]]
        games.append(dict(home_club_id=20, away_club_id=30, player_stats=[]))
        row, = summarize_player_stats(games, sort_by="rating")
        self.assertEqual(row["avg_rating"], 6.67)
        self.assertEqual(row["last_5_rating"], 6)

    def test_legacy_save_recovers_ratings_from_match(self):
        career = Career()
        career.season.advance_week(1, rng=career.rng)
        stats = career.season.completed_matches[0]["player_stats"]
        expected = [row.pop("rating") for row in stats]
        loaded = load_career(dump_career(career))
        restored = loaded.season.completed_matches[0]["player_stats"]
        self.assertEqual([row["rating"] for row in restored], expected)
