def add_match_ratings(match):
    """Tamamlanan maçta, oyuncunun o gün oynadığı mevkiyi kullan."""
    positions = {
        slot["player_id"]: slot["position"]
        for lineup in (match.get("lineups") or {}).values()
        for slot in lineup
    }
    for stat in match["player_stats"]:
        if stat.get("rating") is not None:
            continue
        position = positions.get(stat["player_id"])
        opponent_score = "away_goals" if stat["team"] == "home" else "home_goals"
        conceded = match.get(opponent_score)
        if position is None or conceded is None or stat["minutes_played"] <= 0:
            stat["rating"] = None
            continue

        value = 6.0 + stat["goals"] + 0.5 * stat["assists"]
        if position in {"GK", "CB", "LB", "RB"}:
            if conceded == 0:
                value += 1.0
            elif conceded == 1:
                value += 0.5
        stat["rating"] = min(10.0, value)
