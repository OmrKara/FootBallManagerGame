from random import Random
from threading import RLock

from fastapi import HTTPException

from backend.career_elements import assign_starting_elements, career_bonus_rules
from backend.demo_data import sample_season
from backend.fixtures import generate_fixtures
from backend.season_engine import SeasonEngine
from backend.transfer_offers import TransferOffers


class Career:
    def __init__(self):
        fixtures, teams = sample_season()
        assign_starting_elements(teams)
        self.season = SeasonEngine(fixtures, teams, career_bonus_rules())
        self.season_no = 1
        self.history = {}
        self.rng = Random(7)
        self.offers = TransferOffers()
        self.lock = RLock()

    def start_next_season(self, expected_season):
        with self.lock:
            if expected_season != self.season_no:
                raise HTTPException(409, "Ekrandaki sezon güncel değil.")

            if not self.season.finished:
                raise HTTPException(409, "Yeni sezona geçmek için mevcut sezon bitmeli.")

            previous = self.season
            club_ids = list(previous.teams)
            fixtures = [
                {"match_id": match_id, **fixture}
                for match_id, fixture in enumerate(generate_fixtures(club_ids), start=1)
            ]

            # Güncel kadrolar, bütçeler ve dizilişler aynı takımlarla taşınır.
            new_season = SeasonEngine(fixtures, previous.teams, previous.bonus_rules)

            self.history[self.season_no] = {
                "season_no": self.season_no,
                "standings": previous.standings(),
                "matches": previous.completed_matches,
            }

            self.season = new_season
            self.season_no += 1

            return {
                "season_no": self.season_no,
                "next_week": new_season.next_week,
                "finished": new_season.finished,
                "standings": new_season.standings(),
            }
