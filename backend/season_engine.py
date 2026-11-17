from backend.standings import calculate_standings
from backend.week_engine import play_week
from backend.player_development import develop_players

class SeasonEngine:
    def __init__(self, fixtures, teams, bonus_rules):
        if not fixtures:
            raise ValueError("Sezon fikstürü boş olamaz.")

        # Gerçek uygulamada bu ID'ler MATCH tablosundan gelecek.
        match_ids = [game.get("match_id") for game in fixtures]
        if None in match_ids or len(set(match_ids)) != len(match_ids):
            raise ValueError("Her fikstür maçının ayrı bir match_id değeri olmalı.")

        weeks = sorted({game["week_no"] for game in fixtures})
        if weeks != list(range(1, len(weeks) + 1)):
            raise ValueError("Sezon haftaları 1'den başlayıp sırayla ilerlemeli.")

        self.fixtures = fixtures
        self.teams = teams
        self.bonus_rules = bonus_rules
        self.last_week = weeks[-1]
        self.next_week = 1
        self.completed_matches = []

    @property
    def finished(self):
        return self.next_week is None

    def standings(self):
        return calculate_standings(self.teams.keys(), self.completed_matches)

    def advance_week(self, expected_week, *, rng=None):
        if self.finished:
            return {"valid": False, "errors": ["Sezon tamamlandı."]}

        if expected_week != self.next_week:
            return {
                "valid": False,
                "errors": [
                    f"İstenen hafta {expected_week}, "
                    f"oynanacak hafta {self.next_week}."
                ],
            }

        result = play_week(
            expected_week,
            self.fixtures,
            self.teams,
            self.bonus_rules,
            rng=rng,
        )

        if not result["valid"]:
            return result

        all_matches = self.completed_matches + result["matches"]
        table = calculate_standings(self.teams.keys(), all_matches)

        if expected_week == self.last_week:
            develop_players(self.teams, all_matches, rng=rng)

        # Maçlar ve puan tablosu hazır olduğunda sezonu ilerlet.
        self.completed_matches = all_matches
        self.next_week = (
            None if expected_week == self.last_week else expected_week + 1
        )

        return {
            "valid": True,
            "played_week": expected_week,
            "next_week": self.next_week,
            "finished": self.finished,
            "matches": result["matches"],
            "standings": table,
        }