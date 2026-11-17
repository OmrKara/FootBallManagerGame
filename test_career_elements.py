import unittest
from unittest.mock import patch

from backend.career import Career
from backend.career_save import dump_career, load_career
from backend.match_simulation import simulate_match
from backend.team_power import calculate_team_power


class CareerElementTests(unittest.TestCase):
    def power(self, career, club_id):
        team = career.season.teams[club_id]
        return calculate_team_power(team["players"], team["formation_slots"],
                                    team["selections"], career.season.bonus_rules)

    def test_each_club_starts_with_its_own_bonus(self):
        career = Career()
        for club, expected in [(10, (0, 0, 5)), (20, (5, 0, 0)),
                               (30, (0, 5, 0)), (40, (2, 2, 2))]:
            power = self.power(career, club)
            self.assertEqual(set(power["element_counts"]), {"Fire", "Earth", "Air", "Water"})
            self.assertEqual(power["bonus_percent"], dict(zip(("DEF", "MID", "ATT"), expected)))

    def test_changed_lineup_reaches_match_simulator(self):
        career = Career()
        before = self.power(career, 10)
        career.season.teams[10]["selections"][0]["player_id"] = 1011
        after = self.power(career, 10)
        self.assertEqual(before["base_power"], after["base_power"])
        self.assertEqual(after["bonus_percent"], {"DEF": 5, "MID": 0, "ATT": 0})
        with patch("backend.match_engine.simulate_match", wraps=simulate_match) as simulate:
            result = career.season.advance_week(1, rng=career.rng)
        self.assertTrue(result["valid"])
        self.assertEqual(simulate.call_args_list[0].args[0], after["final_power"])

    def test_rules_survive_save_and_new_season(self):
        career = Career()
        expected = career.season.bonus_rules
        while not career.season.finished:
            result = career.season.advance_week(career.season.next_week, rng=career.rng)
            self.assertTrue(result["valid"])
        restored = load_career(dump_career(career))
        restored.start_next_season(1)
        self.assertEqual(restored.season.bonus_rules, expected)
        self.assertEqual(self.power(restored, 10)["bonus_percent"]["ATT"], 5)
