def summarize_formation_stats(completed_matches, club_id):
    totals = {}

    for match in completed_matches:
        if match["home_club_id"] == club_id:
            side = "home"
            goals_for = match["home_goals"]
            goals_against = match["away_goals"]
        elif match["away_club_id"] == club_id:
            side = "away"
            goals_for = match["away_goals"]
            goals_against = match["home_goals"]
        else:
            continue

        formation = match["formations"][side]

        if formation not in totals:
            totals[formation] = {
                "formation": formation,
                "played": 0,
                "won": 0,
                "drawn": 0,
                "lost": 0,
                "goals_for": 0,
                "goals_against": 0,
            }

        row = totals[formation]
        row["played"] += 1
        row["goals_for"] += goals_for
        row["goals_against"] += goals_against

        if goals_for > goals_against:
            row["won"] += 1
        elif goals_for == goals_against:
            row["drawn"] += 1
        else:
            row["lost"] += 1

    for row in totals.values():
        row["win_pct"] = round(100 * row["won"] / row["played"], 2)

    return sorted(
        totals.values(),
        key=lambda row: (-row["win_pct"], -row["played"], row["formation"]),
    )