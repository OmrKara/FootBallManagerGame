"""Kariyeri JSON metnine dönüştürür ve bağımsız bir kariyer olarak geri kurar."""
import json

from backend.career import Career
from backend.match_rating import add_match_ratings
from backend.season_engine import SeasonEngine


def dump_career(career):
    with career.lock:
        season = career.season
        record = {
            "version": 1,
            "season_no": career.season_no,
            "history": career.history,
            "fixtures": season.fixtures,
            "teams": season.teams,
            "bonus_rules": season.bonus_rules,
            "next_week": season.next_week,
            "completed_matches": season.completed_matches,
            "offers": career.offers.offers,
            "next_offer_id": career.offers.next_id,
            "transfers": career.offers.transfers,
            "rng_state": career.rng.getstate(),
        }
        return json.dumps(record, ensure_ascii=False)


def int_keys(mapping):
    # JSON nesne anahtarlarını metin olarak okur.
    return {int(key): value for key, value in mapping.items()}


def load_career(text):
    record = json.loads(text)
    if record.get("version") != 1:
        raise ValueError("Desteklenmeyen kariyer kayıt sürümü.")

    teams = int_keys(record["teams"])
    for team in teams.values():
        team["players"] = int_keys(team["players"])
        team["formation_slots"] = int_keys(team["formation_slots"])

    season = SeasonEngine(record["fixtures"], teams, record["bonus_rules"])
    season.completed_matches = record["completed_matches"]
    season.next_week = record["next_week"]

    career = Career()
    career.season = season
    career.season_no = record["season_no"]
    career.history = int_keys(record["history"])
    for match in season.completed_matches:
        if any("rating" not in row for row in match["player_stats"]):
            add_match_ratings(match)
    for archive in career.history.values():
        for match in archive["matches"]:
            if any("rating" not in row for row in match["player_stats"]):
                add_match_ratings(match)
    career.offers.offers = int_keys(record["offers"])
    career.offers.next_id = record["next_offer_id"]
    career.offers.transfers = record["transfers"]
    version, state, gaussian = record["rng_state"]
    career.rng.setstate((version, tuple(state), gaussian))
    return career
