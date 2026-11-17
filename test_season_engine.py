import random
import unittest

from backend.season_engine import SeasonEngine
from backend.demo_data import sample_season


class SeasonEngineTests(unittest.TestCase):
    def setUp(self):
        fixtures, teams = sample_season()
        self.season = SeasonEngine(fixtures, teams, [])
        self.rng = random.Random(7)

    def test_second_week_keeps_first_week_results(self):
        first = self.season.advance_week(1, rng=self.rng)
        second = self.season.advance_week(2, rng=self.rng)

        self.assertTrue(first["valid"])
        self.assertTrue(second["valid"])
        self.assertEqual(second["next_week"], 3)
        self.assertEqual(len(self.season.completed_matches), 4)
        self.assertEqual(self.season.completed_matches[:2], first["matches"])
        self.assertTrue(all(row["played"] == 2 for row in second["standings"]))

    def test_repeat_request_does_not_play_another_week(self):
        self.season.advance_week(1, rng=self.rng)
        repeated = self.season.advance_week(1, rng=self.rng)

        self.assertFalse(repeated["valid"])
        self.assertEqual(self.season.next_week, 2)
        self.assertEqual(len(self.season.completed_matches), 2)

    def test_failed_week_can_be_fixed_and_retried(self):
        selections = self.season.teams[30]["selections"]
        removed = selections.pop()

        failed = self.season.advance_week(1, rng=self.rng)

        self.assertFalse(failed["valid"])
        self.assertEqual(self.season.next_week, 1)
        self.assertEqual(self.season.completed_matches, [])

        selections.append(removed)
        retry = self.season.advance_week(1, rng=self.rng)

        self.assertTrue(retry["valid"])
        self.assertEqual(self.season.next_week, 2)

    def test_season_finishes_after_last_week(self):
        for week_no in range(1, 7):
            result = self.season.advance_week(week_no, rng=self.rng)
            self.assertTrue(result["valid"])

        self.assertTrue(result["finished"])
        self.assertIsNone(result["next_week"])
        self.assertEqual(len(self.season.completed_matches), 12)
        self.assertTrue(all(row["played"] == 6 for row in result["standings"]))

        extra = self.season.advance_week(7, rng=self.rng)
        self.assertFalse(extra["valid"])
        self.assertEqual(len(self.season.completed_matches), 12)


def show_sample_season():
    fixtures, teams = sample_season()
    season = SeasonEngine(fixtures, teams, [])
    rng = random.Random(7)

    while not season.finished:
        result = season.advance_week(season.next_week, rng=rng)
        if not result["valid"]:
            print(result["errors"])
            return

        print(f"\n{result['played_week']}. hafta")
        for game in result["matches"]:
            print(
                f"  Kulüp {game['home_club_id']} - Kulüp {game['away_club_id']}"
                f"   {game['home_goals']}-{game['away_goals']}"
            )

    print("\nSezon sonu puan durumu")
    for rank, row in enumerate(season.standings(), start=1):
        print(
            f"{rank}. Kulüp {row['club_id']} | "
            f"{row['played']} maç | {row['points']} puan | "
            f"averaj {row['goal_difference']:+d}"
        )


if __name__ == "__main__":
    show_sample_season()