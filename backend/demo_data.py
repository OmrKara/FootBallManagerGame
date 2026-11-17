from backend.fixtures import generate_fixtures

DEMO_FORMATIONS = {
    "4-3-3": [
        "GK", "RB", "CB", "CB", "LB",
        "CM", "CM", "CAM", "RW", "ST", "LW",
    ],
    "4-4-2": [
        "GK", "RB", "CB", "CB", "LB",
        "CM", "CM", "ST", "RM", "ST", "LM",
    ],
}


def formation_slots(name):
    return dict(enumerate(DEMO_FORMATIONS[name], start=1))


def make_team(first_id):
    slots = formation_slots("4-3-3")
    players = {}
    selections = []

    ages = [36, 22, 31, 35, 21, 27, 24, 20, 26, 23, 32]

    for slot_id, position in slots.items():
        player_id = first_id + slot_id - 1
        players[player_id] = {
            "age": ages[slot_id - 1],
            "primary_position": position,
            "defending": 80,
            "strength": 60,
            "stamina": 70,
            "passing": 90,
            "dribbling": 60,
            "shooting": 70,
            "pace": 80,
            "element": "Fire" if slot_id <= 4 else "Earth",
            "market_value": 500_000 + slot_id * 50_000,
            "compatibility": {position: 100},
        }
        selections.append({"slot_id": slot_id, "player_id": player_id})
    players[first_id + 7]["compatibility"]["ST"] = 75
    players[first_id + 8]["compatibility"]["RM"] = 85
    players[first_id + 10]["compatibility"]["LM"] = 85
    # Kulübe bir yedek ekliyoruz, ilk 11'e seçmiyoruz.

    players[first_id + 11] = players[first_id].copy()
    players[first_id + 11]["age"] = 19
    players[first_id + 11]["market_value"] = 400_000

    return {
        "players": players,
        "formation_slots": slots,
        "selections": selections,
        "formation": "4-3-3",
        "budget": 2_000_000,
    }

def sample_season():
    club_ids = [10, 20, 30, 40]
    teams = {club_id: make_team(club_id * 100) for club_id in club_ids}

    fixtures = [
        {"match_id": match_id, **game}
        for match_id, game in enumerate(generate_fixtures(club_ids), start=1)
    ]
    return fixtures, teams