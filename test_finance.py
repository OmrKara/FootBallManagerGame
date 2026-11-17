import unittest

from backend.demo_data import sample_season
from backend.finance import transfer_finance_summary
from backend.transfer_offers import TransferOffers


class FinanceTests(unittest.TestCase):
    def setUp(self):
        _, self.teams = sample_season()
        self.book = TransferOffers()

    def summary(self, club_id):
        return transfer_finance_summary(
            club_id,
            self.teams[club_id]["budget"],
            self.book.transfers,
        )

    def test_same_transfer_is_expense_for_buyer_and_income_for_seller(self):
        low = self.book.create(self.teams, 10, 2011, 380_000, 1)
        self.book.resolve(self.teams, low["offer_id"], 10, 1)

        accepted = self.book.create(self.teams, 10, 2011, 400_000, 1)
        self.book.resolve(self.teams, accepted["offer_id"], 10, 1)

        buyer = self.summary(10)
        seller = self.summary(20)

        self.assertEqual(buyer["budget"], 1_600_000)
        self.assertEqual(buyer["transfer_expense"], 400_000)
        self.assertEqual(buyer["net_transfer"], -400_000)
        self.assertEqual(len(buyer["movements"]), 1)
        self.assertEqual(buyer["movements"][0]["type"], "TRANSFER_OUT")
        self.assertEqual(buyer["movements"][0]["offer_id"], accepted["offer_id"])

        self.assertEqual(seller["budget"], 2_400_000)
        self.assertEqual(seller["transfer_income"], 400_000)
        self.assertEqual(seller["movements"][0]["type"], "TRANSFER_IN")
        self.assertEqual(seller["movements"][0]["amount"], 400_000)
        self.assertEqual(buyer["net_transfer"] + seller["net_transfer"], 0)

    def test_reading_twice_does_not_change_finances(self):
        offer = self.book.create(self.teams, 10, 2011, 400_000, 1)
        self.book.resolve(self.teams, offer["offer_id"], 10, 1)

        first = self.summary(10)
        second = self.summary(10)

        self.assertEqual(first, second)
        self.assertEqual(self.teams[10]["budget"], 1_600_000)
        self.assertEqual(len(self.book.transfers), 1)
        self.assertEqual(self.summary(30)["movements"], [])