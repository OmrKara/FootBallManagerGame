import unittest

from fastapi import HTTPException

from backend.season_api import Career


class NewSeasonTests(unittest.TestCase):
    def finish_season(self, career):
        while not career.season.finished:
            result = career.season.advance_week(
                career.season.next_week,
                rng=career.rng,
            )
            self.assertTrue(result["valid"])

    def test_unfinished_season_cannot_be_replaced(self):
        career = Career()

        with self.assertRaises(HTTPException) as error:
            career.start_next_season(1)

        self.assertEqual(error.exception.status_code, 409)
        self.assertEqual(career.season_no, 1)
        self.assertEqual(career.season.next_week, 1)
        self.assertEqual(career.history, {})

    def test_new_season_keeps_transfer_and_developed_players(self):
        career = Career()
        teams = career.season.teams
        offer = career.offers.create(teams, 10, 2011, 400_000, 1)
        career.offers.resolve(teams, offer["offer_id"], 10, 1)

        self.finish_season(career)
        keeper = teams[10]["players"][1000]
        age_after_final = keeper["age"]
        defending_after_final = keeper["defending"]

        result = career.start_next_season(1)

        self.assertEqual(result["season_no"], 2)
        self.assertEqual(result["next_week"], 1)
        self.assertFalse(result["finished"])
        self.assertTrue(all(row["played"] == 0 for row in result["standings"]))
        self.assertEqual(career.season.completed_matches, [])

        club = career.season.teams[10]
        self.assertIn(2011, club["players"])
        self.assertEqual(club["budget"], 1_600_000)
        self.assertEqual(club["players"][1000]["age"], age_after_final)
        self.assertEqual(club["players"][1000]["defending"], defending_after_final)

    def test_first_season_history_survives_second_season_match(self):
        career = Career()
        self.finish_season(career)
        final_table = career.season.standings()

        career.start_next_season(1)
        result = career.season.advance_week(1, rng=career.rng)

        self.assertTrue(result["valid"])
        self.assertEqual(len(career.season.completed_matches), 2)
        self.assertEqual(len(career.history[1]["matches"]), 12)
        self.assertEqual(career.history[1]["standings"], final_table)

    def test_repeated_request_does_not_advance_again(self):
        career = Career()
        self.finish_season(career)
        career.start_next_season(1)

        with self.assertRaises(HTTPException) as error:
            career.start_next_season(1)

        self.assertEqual(error.exception.status_code, 409)
        self.assertEqual(career.season_no, 2)
        self.assertEqual(career.season.next_week, 1)
        self.assertEqual(list(career.history), [1])