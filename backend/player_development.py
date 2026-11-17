from collections import Counter
from random import Random


POSITION_ATTRIBUTE = {
    "GK": "defending",
    "RB": "defending",
    "CB": "defending",
    "LB": "defending",
    "CM": "passing",
    "CAM": "passing",
    "RM": "passing",
    "LM": "passing",
    "RW": "shooting",
    "LW": "shooting",
    "ST": "shooting",
}


def season_change(age, regular_player, contributions, rng):
    if age <= 23:
        change = 1 if regular_player else 0
    elif age < 35:
        roll = rng.random()
        if roll < 0.15:
            change = -1
        elif roll < 0.85:
            change = 0
        else:
            change = 1
    else:
        change = -1

    if regular_player and contributions >= 3:
        change += 1

    return change


def develop_players(teams, matches, *, rng=None):
    if rng is None:
        rng = Random()

    club_matches = Counter()
    appearances = Counter()
    contributions = Counter()

    for match in matches:
        club_matches[match["home_club_id"]] += 1
        club_matches[match["away_club_id"]] += 1

        for row in match["player_stats"]:
            if row["minutes_played"] > 0:
                appearances[row["player_id"]] += 1

        for event in match["events"]:
            if event["event_type"] in ("GOAL", "ASSIST"):
                contributions[event["player_id"]] += 1

    updates = []

    for club_id, team in teams.items():
        for player_id, player in team["players"].items():
            # Eski örnek kadrolarda yaş ve ana mevki bulunmayabilir.
            if "age" not in player or "primary_position" not in player:
                continue

            age = player["age"]
            attribute = POSITION_ATTRIBUTE[player["primary_position"]]
            before = player[attribute]
            regular_player = (
                club_matches[club_id] > 0
                and appearances[player_id] * 2 >= club_matches[club_id]
            )
            change = season_change(
                age, regular_player, contributions[player_id], rng
            )
            after = max(0, min(100, before + change))
            updates.append((player, attribute, after, age + 1))

    for player, attribute, after, new_age in updates:
        player[attribute] = after
        player["age"] = new_age