def list_market_players(teams, buyer_club_id, *, position=None, element=None,
                        min_value=None, max_value=None):
    if min_value is not None and max_value is not None and min_value > max_value:
        raise ValueError("En düşük değer, en yüksek değerden büyük olamaz.")

    position = position.strip().upper() if position else None
    element = element.strip().casefold() if element else None
    results = []

    for club_id, team in teams.items():
        if club_id == buyer_club_id:
            continue

        for player_id, player in team["players"].items():
            value = player["market_value"]
            compatibility = player["compatibility"]

            if position and position not in compatibility:
                continue
            if element and (player["element"] or "none").casefold() != element:
                continue
            if min_value is not None and value < min_value:
                continue
            if max_value is not None and value > max_value:
                continue

            results.append({
                "player_id": player_id,
                "club_id": club_id,
                "element": player["element"],
                "market_value": value,
                "compatibility": dict(compatibility),
                "club_name": team.get("name"),
                **{field: player.get(field) for field in (
                    "first_name", "last_name", "age", "primary_position",
                    "defending", "strength", "stamina", "passing",
                    "dribbling", "shooting", "pace",
                )},
            })

    return sorted(results, key=lambda row: (row["market_value"], row["player_id"]))