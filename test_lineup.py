import unittest

from backend.lineup import validate_lineup


class LineupTests(unittest.TestCase):
    def setUp(self):
        self.club_players = set(range(101, 119))
        self.slots = set(range(1, 12))
        self.lineup = [
            {"slot_id": slot, "player_id": 100 + slot}
            for slot in range(1, 12)
        ]

    def check_lineup(self):
        return validate_lineup(self.club_players, self.slots, self.lineup)

    def test_valid_lineup(self):
        self.assertEqual(self.check_lineup(), {"valid": True, "errors": []})

    def test_missing_player(self):
        self.lineup.pop()
        result = self.check_lineup()

        self.assertFalse(result["valid"])
        self.assertIn("Boş kalan formasyon slotları: 11.", result["errors"])

    def test_duplicate_player(self):
        self.lineup[1]["player_id"] = 101
        result = self.check_lineup()

        self.assertFalse(result["valid"])
        self.assertIn(
            "101 numaralı oyuncu birden fazla kez seçilmiş.",
            result["errors"],
        )

    def test_player_from_another_club(self):
        self.lineup[0]["player_id"] = 999
        result = self.check_lineup()

        self.assertFalse(result["valid"])
        self.assertIn(
            "999 numaralı oyuncu bu kulübün kadrosunda yok.",
            result["errors"],
        )

    def test_duplicate_slot(self):
        self.lineup[1]["slot_id"] = 1
        result = self.check_lineup()

        self.assertFalse(result["valid"])
        self.assertIn(
            "1 numaralı slota birden fazla oyuncu atanmış.",
            result["errors"],
        )
        self.assertIn("Boş kalan formasyon slotları: 2.", result["errors"])


if __name__ == "__main__":
    unittest.main()