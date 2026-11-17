import random


ASSIST_CHANCE = 0.70


def choose_player(players, player_ids, attribute, rng):
    weights = [players[player_id][attribute] for player_id in player_ids]

    if sum(weights) == 0:
        return rng.choice(player_ids)

    return rng.choices(player_ids, weights=weights, k=1)[0]


def build_match_details(match_result, home_lineup, away_lineup, *, rng=None):
    if rng is None:
        rng = random.Random()

    if len(home_lineup) != 11 or len(away_lineup) != 11:
        raise ValueError("Her takım için sahadaki 11 oyuncu gerekli.")

    if set(home_lineup) & set(away_lineup):
        raise ValueError("Bir oyuncu aynı maçta iki takımda oynayamaz.")

    teams = {"home": home_lineup, "away": away_lineup}
    stats = {}

    for side, players in teams.items():
        for player_id in players:
            stats[player_id] = {
                "player_id": player_id,
                "team": side,
                "minutes_played": 90,
                "goals": 0,
                "assists": 0,
            }

    events = []
    goal_counts = {"home": 0, "away": 0}

    for goal in match_result["events"]:
        side = goal["team"]
        if goal["event_type"] != "GOAL" or side not in teams:
            raise ValueError("Maç simülasyonundan geçerli bir gol olayı bekleniyor.")

        players = teams[side]
        scorer = choose_player(players, list(players), "shooting", rng)

        goal_counts[side] += 1
        stats[scorer]["goals"] += 1
        events.append({**goal, "player_id": scorer})

        if rng.random() < ASSIST_CHANCE:
            teammates = [player_id for player_id in players if player_id != scorer]
            assistant = choose_player(players, teammates, "passing", rng)

            stats[assistant]["assists"] += 1
            events.append({
                "minute": goal["minute"],
                "team": side,
                "event_type": "ASSIST",
                "player_id": assistant,
            })

    if (goal_counts["home"], goal_counts["away"]) != (
        match_result["home_goals"], match_result["away_goals"]
    ):
        raise ValueError("Skor ile gol olaylarının sayısı uyuşmuyor.")

    return {
        "home_goals": goal_counts["home"],
        "away_goals": goal_counts["away"],
        "events": events,
        "player_stats": list(stats.values()),
    }