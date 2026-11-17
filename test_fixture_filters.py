import unittest

from backend.fixture_filters import matches_club_filters


class FixtureFilterTests(unittest.TestCase):
    def setUp(self):
        self.game = dict(home_club_id=20, away_club_id=10, status="played",
                         home_goals=0, away_goals=2)

    def test_away_victory_and_opponent(self):
        self.assertTrue(matches_club_filters(self.game, 10, 20, "away", "win"))
        self.assertTrue(matches_club_filters(self.game, 20, 10, "home", "loss"))
        self.assertFalse(matches_club_filters(self.game, 10, 30, "away", "win"))
        self.assertFalse(matches_club_filters(self.game, 10, 20, "home", "win"))

    def test_draw_and_scheduled(self):
        self.game["away_goals"] = 0
        self.assertTrue(matches_club_filters(self.game, 10, result="draw"))
        self.game.update(status="scheduled", home_goals=None, away_goals=None)
        self.assertFalse(matches_club_filters(self.game, 10, result="draw"))
        self.assertTrue(matches_club_filters(self.game, 10, venue="away"))

    def test_unfiltered_list_keeps_other_clubs(self):
        self.assertTrue(matches_club_filters(self.game, 30))
        self.assertFalse(matches_club_filters(self.game, 30, result="win"))
