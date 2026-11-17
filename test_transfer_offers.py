import unittest

from backend.demo_data import sample_season
from backend.transfer_offers import OfferConflict, TransferOffers


class TransferOfferTests(unittest.TestCase):
    def setUp(self):
        _, self.teams = sample_season()
        self.book = TransferOffers()

    def test_offer_records_real_seller_without_moving_player(self):
        offer = self.book.create(self.teams, 10, 2011, 380_000, 1)

        self.assertEqual(offer["buyer_club_id"], 10)
        self.assertEqual(offer["seller_club_id"], 20)
        self.assertEqual(offer["status"], "PENDING")
        self.assertIn(2011, self.teams[20]["players"])
        self.assertNotIn(2011, self.teams[10]["players"])

    def test_duplicate_pending_offer_is_rejected(self):
        self.book.create(self.teams, 10, 2011, 380_000, 1)

        with self.assertRaises(OfferConflict):
            self.book.create(self.teams, 10, 2011, 400_000, 1)

        self.assertEqual(len(self.book.list_for_buyer(10)), 1)

    def test_cancel_keeps_history_and_allows_new_offer(self):
        first = self.book.create(self.teams, 10, 2011, 380_000, 1)
        self.book.cancel(first["offer_id"], 10)
        second = self.book.create(self.teams, 10, 2011, 400_000, 1)

        rows = self.book.list_for_buyer(10)
        self.assertNotEqual(first["offer_id"], second["offer_id"])
        self.assertEqual([r["status"] for r in rows], ["PENDING", "CANCELLED"])
        self.assertEqual([r["amount"] for r in rows], [400_000, 380_000])

    def test_other_club_cannot_cancel_offer(self):
        offer = self.book.create(self.teams, 10, 2011, 380_000, 1)

        with self.assertRaises(KeyError):
            self.book.cancel(offer["offer_id"], 30)

        self.assertEqual(self.book.list_for_buyer(10)[0]["status"], "PENDING")

    def test_own_or_unknown_player_cannot_receive_offer(self):
        with self.assertRaises(OfferConflict):
            self.book.create(self.teams, 10, 1011, 380_000, 1)

        with self.assertRaises(KeyError):
            self.book.create(self.teams, 10, 99999, 380_000, 1)

        self.assertEqual(self.book.list_for_buyer(10), [])

    def test_accepted_transfer_moves_player_and_money_once(self):
        offer = self.book.create(self.teams, 10, 2011, 400_000, 1)
        result = self.book.resolve(self.teams, offer["offer_id"], 10, 1)

        self.assertEqual(result["status"], "ACCEPTED")
        self.assertIn(2011, self.teams[10]["players"])
        self.assertNotIn(2011, self.teams[20]["players"])

        with self.assertRaises(OfferConflict):
            self.book.resolve(self.teams, offer["offer_id"], 10, 1)

        self.assertEqual(self.teams[10]["budget"], 1_600_000)
        self.assertEqual(self.teams[20]["budget"], 2_400_000)
        self.assertEqual(len(self.book.transfers), 1)
        self.assertEqual(self.book.transfers[0]["fee"], 400_000)

    def test_low_offer_rejected_without_moving_player(self):
        offer = self.book.create(self.teams, 10, 2011, 380_000, 1)
        result = self.book.resolve(self.teams, offer["offer_id"], 10, 1)

        self.assertEqual(result["status"], "REJECTED")
        self.assertIn(2011, self.teams[20]["players"])
        self.assertEqual(self.teams[10]["budget"], 2_000_000)
        self.assertEqual(self.book.transfers, [])

    def test_bot_keeps_starting_goalkeeper(self):
        offer = self.book.create(self.teams, 10, 2000, 600_000, 1)
        result = self.book.resolve(self.teams, offer["offer_id"], 10, 1)

        self.assertEqual(result["status"], "REJECTED")
        self.assertIn(2000, self.teams[20]["players"])

    def test_insufficient_budget_leaves_offer_pending(self):
        self.teams[10]["budget"] = 300_000
        offer = self.book.create(self.teams, 10, 2011, 400_000, 1)

        with self.assertRaises(OfferConflict):
            self.book.resolve(self.teams, offer["offer_id"], 10, 1)

        self.assertEqual(self.book.list_for_buyer(10)[0]["status"], "PENDING")
        self.assertEqual(self.teams[10]["budget"], 300_000)
        self.assertEqual(self.teams[20]["budget"], 2_000_000)
        self.assertIn(2011, self.teams[20]["players"])
        self.assertEqual(self.book.transfers, [])