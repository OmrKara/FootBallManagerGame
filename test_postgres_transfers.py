import sqlite3
import unittest
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from pathlib import Path

import test_postgres_career_load as block3
from backend.postgres_career_load import read_season_state
from backend.postgres_transfers import (
    cancel_sql_offer, create_sql_offer, read_transfer_book, resolve_sql_offer,
)
from backend.transfer_offers import OfferConflict


class SqlTransferTests(unittest.TestCase):
    def setUp(self):
        fixture = block3.CareerLoadTests()
        self.addCleanup(fixture.doCleanups)
        fixture.setUp()
        self.connect = fixture.connect
        fixture.create(1)
        sql = (Path(__file__).parent / "docs/transfer_kaydi.sql").read_text(encoding="utf-8")
        with closing(self.connect()) as db:
            db.executescript(sql.replace("REFERENCES public.", "REFERENCES ")
                              .replace("ON public.transfer_offer\n", "ON transfer_offer\n")
                              .replace("INDEX transfer_one_pending", "INDEX public.transfer_one_pending"))

    def offer(self, amount=400_000):
        return create_sql_offer(1, 2011, amount, 1, 1, connect=self.connect)["offer_id"]

    def resolve(self, offer_id):
        return resolve_sql_offer(1, offer_id, connect=self.connect)

    def test_concurrent_accept_moves_player_and_money_once(self):
        oid = self.offer()
        def attempt(_):
            try:
                return self.resolve(oid)["status"]
            except OfferConflict:
                return "CONFLICT"
        with ThreadPoolExecutor(2) as pool:
            self.assertEqual(sorted(pool.map(attempt, range(2))), ["ACCEPTED", "CONFLICT"])
        with closing(self.connect()) as db:
            teams = read_season_state(db.cursor(), 1).season.teams
            self.assertIn(2011, teams[10]["players"])
            self.assertNotIn(2011, teams[20]["players"])
            self.assertEqual((teams[10]["budget"], teams[20]["budget"]), (1_600_000, 2_400_000))
            transfers = read_transfer_book(db.cursor(), 1).transfers
            self.assertEqual([r["fee"] for r in transfers], [400_000])

    def test_cancel_reject_and_insufficient_budget(self):
        oid = self.offer()
        with self.assertRaises(OfferConflict):
            self.offer()
        self.assertEqual(cancel_sql_offer(1, oid, connect=self.connect)["status"], "CANCELLED")
        self.assertEqual(self.resolve(self.offer(100))["status"], "REJECTED")
        expensive = self.offer(3_000_000)
        with self.assertRaises(OfferConflict):
            self.resolve(expensive)
        with closing(self.connect()) as db:
            book = read_transfer_book(db.cursor(), 1)
            self.assertEqual(book.offers[expensive]["status"], "PENDING")
            self.assertEqual(book.transfers, [])

    def test_failed_history_insert_rolls_back_and_can_be_retried(self):
        oid = self.offer()
        with closing(self.connect()) as db:
            db.execute("""CREATE TRIGGER public.fail_history BEFORE INSERT ON transfer
                          BEGIN SELECT RAISE(ABORT,'failure'); END""")
        with self.assertRaises(sqlite3.IntegrityError):
            self.resolve(oid)
        with closing(self.connect()) as db:
            self.assertEqual(read_transfer_book(db.cursor(), 1).offers[oid]["status"], "PENDING")
            teams = read_season_state(db.cursor(), 1).season.teams
            self.assertIn(2011, teams[20]["players"])
            self.assertEqual([teams[c]["budget"] for c in (10, 20)], [2_000_000]*2)
            db.execute("DROP TRIGGER public.fail_history")
        self.assertEqual(self.resolve(oid)["status"], "ACCEPTED")
