import unittest
from collections import Counter, defaultdict
from itertools import combinations, permutations

from backend.fixtures import generate_fixtures


class FixtureTests(unittest.TestCase):
    def test_double_round_has_every_home_away_pair_once(self):
        clubs = [10, 20, 30, 40]
        games = generate_fixtures(clubs)

        pairs = Counter(
            (game["home_club_id"], game["away_club_id"])
            for game in games
        )

        self.assertEqual(pairs, Counter(permutations(clubs, 2)))
        self.assertEqual(
            Counter(game["week_no"] for game in games),
            {week: 2 for week in range(1, 7)},
        )

    def test_no_club_plays_twice_in_one_week(self):
        clubs = [10, 20, 30, 40, 50, 60]
        by_week = defaultdict(list)

        for game in generate_fixtures(clubs):
            by_week[game["week_no"]].extend(
                [game["home_club_id"], game["away_club_id"]]
            )

        for participants in by_week.values():
            self.assertCountEqual(participants, clubs)

    def test_odd_league_gives_each_club_one_bye_per_half(self):
        clubs = [10, 20, 30, 40, 50]
        games = generate_fixtures(clubs, double_round=False)
        by_week = defaultdict(list)

        for game in games:
            by_week[game["week_no"]].extend(
                [game["home_club_id"], game["away_club_id"]]
            )

        self.assertEqual(set(by_week), {1, 2, 3, 4, 5})

        byes = []
        for participants in by_week.values():
            self.assertEqual(len(participants), 4)
            self.assertEqual(len(set(participants)), 4)
            byes.extend(set(clubs) - set(participants))

        self.assertCountEqual(byes, clubs)

    def test_single_round_has_every_pair_once(self):
        clubs = [10, 20, 30, 40]
        games = generate_fixtures(clubs, double_round=False)

        pairs = Counter(
            tuple(sorted((game["home_club_id"], game["away_club_id"])))
            for game in games
        )

        self.assertEqual(pairs, Counter(combinations(clubs, 2)))

    def test_invalid_club_lists(self):
        for clubs in ([], [10], [10, 10], [10, 0]):
            with self.subTest(clubs=clubs):
                with self.assertRaises(ValueError):
                    generate_fixtures(clubs)


if __name__ == "__main__":
    unittest.main()