import random
import unittest

from backend.match_engine import play_match


from backend.demo_data import make_team


def sample_match():
    rules = [{
        "element": "Fire",
        "required_count": 4,
        "defense_bonus_pct": 0,
        "midfield_bonus_pct": 0,
        "attack_bonus_pct": 10,
    }]

    return play_match(
        make_team(101),
        make_team(201),
        rules,
        rng=random.Random(7),
    )


class MatchEngineTests(unittest.TestCase):
    def test_full_match_uses_bonus_and_only_selected_players(self):
        result = sample_match()
        self.assertTrue(result["valid"])

        home = result["team_power"]["home"]
        self.assertEqual(home["base_power"]["ATT"], 71)
        self.assertEqual(home["final_power"]["ATT"], 78.1)

        match = result["match"]
        expected_ids = set(range(101, 112)) | set(range(201, 212))
        actual_ids = {p["player_id"] for p in match["player_stats"]}

        self.assertEqual(len(match["player_stats"]), 22)
        self.assertEqual(actual_ids, expected_ids)

        for side in ("home", "away"):
            player_goals = sum(
                p["goals"] for p in match["player_stats"] if p["team"] == side
            )
            self.assertEqual(player_goals, match[f"{side}_goals"])

    def test_reports_both_invalid_teams(self):
        home = make_team(101)
        away = make_team(201)
        home["selections"].pop()
        away["selections"][1]["player_id"] = 201

        result = play_match(home, away, [])

        self.assertFalse(result["valid"])
        self.assertEqual(set(result["errors"]), {"home", "away"})
        self.assertNotIn("match", result)

    def test_player_cannot_play_for_both_sides(self):
        result = play_match(make_team(101), make_team(101), [])

        self.assertFalse(result["valid"])
        self.assertIn("match", result["errors"])

    def test_match_keeps_both_starting_lineups_in_slot_order(self):
        home = make_team(101)
        away = make_team(201)
        home["selections"].reverse()

        result = play_match(home, away, [], rng=random.Random(7))
        lineups = result["match"]["lineups"]

        self.assertEqual([p["slot_id"] for p in lineups["home"]], list(range(1, 12)))
        self.assertEqual(len(lineups["away"]), 11)
        self.assertEqual(lineups["home"][0], {
            "slot_id": 1, "position": "GK", "player_id": 101,
        })
        self.assertEqual(lineups["away"][0], {
            "slot_id": 1, "position": "GK", "player_id": 201,
        })

    def test_changing_next_lineup_preserves_previous_match(self):
        home = make_team(101)
        away = make_team(201)

        # İlk maça yedek kaleci 112 çıkıyor.
        home["selections"][0]["player_id"] = 112
        first = play_match(home, away, [], rng=random.Random(7))

        # Sonraki maç için eski kaleci geri dönüyor.
        home["selections"][0]["player_id"] = 101
        second = play_match(home, away, [], rng=random.Random(8))

        first_keeper = first["match"]["lineups"]["home"][0]
        second_keeper = second["match"]["lineups"]["home"][0]

        self.assertEqual(first_keeper["player_id"], 112)
        self.assertEqual(second_keeper["player_id"], 101)

if __name__ == "__main__":
    unittest.main()