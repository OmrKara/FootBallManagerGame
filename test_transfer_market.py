import unittest

from backend.demo_data import sample_season
from backend.transfer_market import list_market_players


class TransferMarketTests(unittest.TestCase):
    def setUp(self):
        _, self.teams = sample_season()

    def test_market_contains_only_other_clubs(self):
        rows = list_market_players(self.teams, 10)

        self.assertEqual(len(rows), 36)
        self.assertEqual({row["club_id"] for row in rows}, {20, 30, 40})

    def test_combined_filters_include_exact_price_boundary(self):
        rows = list_market_players(
            self.teams, 10,
            position="gk", element="fire",
            min_value=400_000, max_value=400_000,
        )

        self.assertEqual(
            [row["player_id"] for row in rows],
            [2011, 3011, 4011],
        )

    def test_secondary_position_is_searchable(self):
        rows = list_market_players(self.teams, 10, position="ST")
        by_id = {row["player_id"]: row for row in rows}

        self.assertEqual(by_id[2007]["compatibility"]["ST"], 75)
        self.assertEqual(by_id[2009]["compatibility"]["ST"], 100)

    def test_invalid_price_range(self):
        with self.assertRaises(ValueError):
            list_market_players(self.teams, 10, min_value=600_000, max_value=400_000)

    def test_market_returns_player_details_before_offer(self):
        from backend.demo_data import sample_season
        from backend.transfer_market import list_market_players

        _, teams = sample_season()
        market = list_market_players(teams, 10)

        player = next(row for row in market if row["player_id"] == 2011)
        source = teams[20]["players"][2011]

        self.assertEqual(player["club_id"], 20)
        for field in (
            "age", "primary_position", "defending", "strength", "stamina",
            "passing", "dribbling", "shooting", "pace",
        ):
            with self.subTest(field=field):
                self.assertEqual(player[field], source[field])