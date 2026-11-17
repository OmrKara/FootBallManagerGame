import math
import random


# Hücum ile rakip savunma eşit olduğunda gol ihtimali %15 olur.
GOAL_FACTOR = 0.30


def power_share(first, second):
    total = first + second
    if total == 0:
        return 0.5

    return first / total


def simulate_match(home_power, away_power, *, rng=None):
    for power in (home_power, away_power):
        for region in ("DEF", "MID", "ATT"):
            value = power.get(region)
            if value is None or not math.isfinite(value) or value < 0:
                raise ValueError(f"{region} için geçerli bir takım gücü gerekli.")

    if rng is None:
        rng = random.Random()

    home_chance = power_share(home_power["MID"], away_power["MID"])
    home_goal_chance = GOAL_FACTOR * power_share(home_power["ATT"], away_power["DEF"])
    away_goal_chance = GOAL_FACTOR * power_share(away_power["ATT"], home_power["DEF"])

    goals = {"home": 0, "away": 0}
    events = []

    for start_minute in range(1, 91, 5):
        if rng.random() < home_chance:
            side = "home"
            goal_chance = home_goal_chance
        else:
            side = "away"
            goal_chance = away_goal_chance

        if rng.random() < goal_chance:
            minute = rng.randint(start_minute, start_minute + 4)
            goals[side] += 1
            events.append({
                "minute": minute,
                "team": side,
                "event_type": "GOAL",
            })

    return {
        "home_goals": goals["home"],
        "away_goals": goals["away"],
        "events": events,
    }