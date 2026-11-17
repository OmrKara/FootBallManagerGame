import random

from backend.match_rating import add_match_ratings
from backend.match_details import build_match_details
from backend.match_simulation import simulate_match
from backend.team_power import calculate_team_power


def build_match_lineup(team):
    slots = team["formation_slots"]

    return [
        {
            "slot_id": selection["slot_id"],
            "position": slots[selection["slot_id"]],
            "player_id": selection["player_id"],
        }
        for selection in sorted(team["selections"], key=lambda item: item["slot_id"])
    ]


def play_match(home_team, away_team, bonus_rules, *, rng=None):
    teams = {"home": home_team, "away": away_team}
    powers = {}
    lineups = {}
    errors = {}

    for side, team in teams.items():
        result = calculate_team_power(
            team["players"],
            team["formation_slots"],
            team["selections"],
            bonus_rules,
        )

        if not result["valid"]:
            errors[side] = result["errors"]
            continue

        powers[side] = result
        lineups[side] = {
            selection["player_id"]: team["players"][selection["player_id"]]
            for selection in team["selections"]
        }

    if errors:
        return {"valid": False, "errors": errors}

    if set(lineups["home"]) & set(lineups["away"]):
        return {
            "valid": False,
            "errors": {"match": ["Bir oyuncu iki takımın ilk 11'inde yer alamaz."]},
        }

    if rng is None:
        rng = random.Random()

    score = simulate_match(
        powers["home"]["final_power"],
        powers["away"]["final_power"],
        rng=rng,
    )

    match = build_match_details(
        score,
        lineups["home"],
        lineups["away"],
        rng=rng,
    )

    match["lineups"] = {
        "home": build_match_lineup(home_team),
        "away": build_match_lineup(away_team),
    }

    add_match_ratings(match)

    match["formations"] = {
        "home": home_team["formation"],
        "away": away_team["formation"],
    }

    return {
        "valid": True,
        "team_power": powers,
        "match": match,
    }