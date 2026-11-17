import unittest

from backend.team_power import calculate_team_power


class TeamPowerTests(unittest.TestCase):
    def setUp(self):
        positions = [
            "GK", "RB", "CB", "CB", "LB", "CM",
            "CM", "CAM", "RW", "ST", "LW",
        ]
        self.slots = dict(enumerate(positions, start=1))
        self.players = {}
        self.selections = []

        for slot_id, position in self.slots.items():
            player_id = 100 + slot_id
            self.players[player_id] = {
                "defending": 80,
                "strength": 60,
                "stamina": 70,
                "passing": 90,
                "dribbling": 60,
                "shooting": 70,
                "pace": 80,
                "element": "Fire" if slot_id <= 4 else "Earth",
                "compatibility": {position: 100},
            }
            self.selections.append({"slot_id": slot_id, "player_id": player_id})

    def calculate(self, rules=None):
        return calculate_team_power(
            self.players, self.slots, self.selections, rules or []
        )

    def test_base_power_from_attributes(self):
        result = self.calculate()

        self.assertTrue(result["valid"])
        self.assertEqual(result["base_power"], {"DEF": 72, "MID": 77, "ATT": 71})
        self.assertEqual(result["final_power"], result["base_power"])

    def test_compatibility_uses_selected_position(self):
        player = self.players[101]
        player["compatibility"] = {"GK": 50, "CB": 100}

        result = self.calculate()

        self.assertTrue(result["valid"])
        self.assertEqual(
            result["base_power"],
            {"DEF": 68.73, "MID": 73.5, "ATT": 67.77},
        )

    def test_element_bonus_applied_after_base_power(self):
        rules = [{
            "element": "Fire",
            "required_count": 4,
            "defense_bonus_pct": 0,
            "midfield_bonus_pct": 0,
            "attack_bonus_pct": 10,
        }]

        result = self.calculate(rules)

        self.assertEqual(result["element_counts"], {"Fire": 4, "Earth": 7})
        self.assertEqual(result["base_power"]["ATT"], 71)
        self.assertEqual(result["final_power"]["ATT"], 78.1)

    def test_invalid_lineup_stops_calculation(self):
        self.selections[1]["player_id"] = 101

        result = self.calculate()

        self.assertFalse(result["valid"])
        self.assertNotIn("final_power", result)

    def test_missing_position_compatibility(self):
        self.players[101]["compatibility"] = {"CB": 90}

        result = self.calculate()

        self.assertFalse(result["valid"])
        self.assertIn("GK", result["errors"][0])


if __name__ == "__main__":
    unittest.main()