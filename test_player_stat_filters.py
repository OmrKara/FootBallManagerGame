import unittest

from backend.player_stats import summarize_player_stats


def match(position, goals, club=10):
    return {
        "home_club_id": club, "away_club_id": 20,
        "lineups": {"home": [{"player_id": 7, "position": position}], "away": []},
        "player_stats": [{"player_id": 7, "team": "home", "minutes_played": 90,
                          "goals": goals, "assists": 1}],
    }


class PlayerStatFilterTests(unittest.TestCase):
    def test_position_counts_only_matches_in_that_slot(self):
        games = [match("ST", 2), match("RW", 1)]
        rows = summarize_player_stats(games, position=" st ")
        self.assertEqual((rows[0]["goals"], rows[0]["matches_played"]), (2, 1))
        self.assertEqual(summarize_player_stats(games, position="ST", min_matches=2), [])

    def test_element_and_club_after_transfer(self):
        games = [match("ST", 2), match("ST", 1, club=30)]
        filters = dict(club_id=10, position="ST", player_elements={7: "Fire"}, sort_by="assists")
        rows = summarize_player_stats(games, element=" fire ", **filters)
        self.assertEqual((rows[0]["goals"], rows[0]["assists"]), (2, 1))
        self.assertEqual(summarize_player_stats(games, element="Water", **filters), [])

    def test_older_match_without_lineup(self):
        game = match("ST", 2)
        del game["lineups"]
        self.assertEqual(summarize_player_stats([game])[0]["goals"], 2)
        self.assertEqual(summarize_player_stats([game], position="ST"), [])
