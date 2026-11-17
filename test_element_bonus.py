import unittest

from backend.element_bonus import apply_element_bonuses


def bonus_rule(element, required, defense=0, midfield=0, attack=0):
    return {
        "element": element,
        "required_count": required,
        "defense_bonus_pct": defense,
        "midfield_bonus_pct": midfield,
        "attack_bonus_pct": attack,
    }


class ElementBonusTests(unittest.TestCase):
    def setUp(self):
        self.power = {"DEF": 80, "MID": 90, "ATT": 100}
        self.elements = ["Fire"] * 4 + ["Water"] * 3 + ["Earth"] * 2 + ["Air"] * 2

    def test_no_threshold_reached(self):
        rules = [bonus_rule("Fire", 5, attack=10)]
        result = apply_element_bonuses(self.power, self.elements, rules)

        self.assertEqual(result["active_bonuses"], [])
        self.assertEqual(result["final_power"], self.power)

    def test_only_highest_fire_tier_applies(self):
        rules = [
            bonus_rule("Fire", 4, attack=10),
            bonus_rule("Fire", 2, attack=5),
        ]
        result = apply_element_bonuses(self.power, self.elements, rules)

        self.assertEqual(result["element_counts"]["Fire"], 4)
        self.assertEqual(result["active_bonuses"], [rules[0]])
        self.assertEqual(result["final_power"], {"DEF": 80, "MID": 90, "ATT": 110})

    def test_different_elements_combine(self):
        rules = [
            bonus_rule("Fire", 4, attack=10),
            bonus_rule("Water", 3, defense=2, midfield=2, attack=2),
            bonus_rule("Earth", 2, defense=5),
            bonus_rule("Air", 2, midfield=3),
        ]
        result = apply_element_bonuses(self.power, self.elements, rules)

        self.assertEqual(result["bonus_percent"], {"DEF": 7, "MID": 5, "ATT": 12})
        self.assertEqual(
            result["final_power"],
            {"DEF": 85.6, "MID": 94.5, "ATT": 112},
        )

    def test_incomplete_lineup(self):
        with self.assertRaises(ValueError):
            apply_element_bonuses(self.power, self.elements[:10], [])


if __name__ == "__main__":
    unittest.main()