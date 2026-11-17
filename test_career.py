import unittest
from unittest.mock import patch

from backend import season_api


class CareerTests(unittest.TestCase):
    def setUp(self):
        self.enterContext(patch.object(season_api, "user_careers", {}))
        self.user_a = {"user_id": 1, "username": "deniz"}
        self.user_b = {"user_id": 2, "username": "ece"}

    def test_advancing_one_career_keeps_other_at_week_one(self):
        career_a = season_api.get_user_career(self.user_a)
        career_b = season_api.get_user_career(self.user_b)

        result = career_a.season.advance_week(1, rng=career_a.rng)

        self.assertTrue(result["valid"])
        self.assertEqual(career_a.season.next_week, 2)
        self.assertEqual(career_b.season.next_week, 1)
        self.assertEqual(career_b.season.completed_matches, [])

    def test_transfer_only_changes_buyers_career(self):
        career_a = season_api.get_user_career(self.user_a)
        career_b = season_api.get_user_career(self.user_b)
        teams_a = career_a.season.teams
        teams_b = career_b.season.teams

        # Kulüp 10, kulüp 20'nin yedek kalecisini satın alıyor.
        offer = career_a.offers.create(teams_a, 10, 2011, 400_000, 1)
        career_a.offers.resolve(teams_a, offer["offer_id"], 10, 1)

        self.assertIn(2011, teams_a[10]["players"])
        self.assertNotIn(2011, teams_a[20]["players"])
        self.assertEqual(teams_a[10]["budget"], 1_600_000)
        self.assertEqual(teams_a[20]["budget"], 2_400_000)

        self.assertNotIn(2011, teams_b[10]["players"])
        self.assertIn(2011, teams_b[20]["players"])
        self.assertEqual(teams_b[10]["budget"], 2_000_000)
        self.assertEqual(teams_b[20]["budget"], 2_000_000)
        self.assertEqual(career_b.offers.list_for_buyer(10), [])
        self.assertEqual(career_b.offers.transfers, [])

    def test_same_user_returns_to_existing_career(self):
        first_visit = season_api.get_user_career(self.user_a)
        result = first_visit.season.advance_week(1, rng=first_visit.rng)
        self.assertTrue(result["valid"])

        # Yeni bir girişte aynı kullanıcı kimliğiyle kariyer tekrar istenir.
        returning_user = {"user_id": 1, "username": "deniz"}
        second_visit = season_api.get_user_career(returning_user)

        self.assertIs(first_visit, second_visit)
        self.assertEqual(second_visit.season.next_week, 2)