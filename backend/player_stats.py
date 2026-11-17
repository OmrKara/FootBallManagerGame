def summarize_player_stats(completed_matches, *, sort_by="goals",
                           club_id=None, min_matches=1, position=None,
                           element=None, player_elements=None):
    if sort_by not in ("goals", "assists", "rating"):
        raise ValueError("Sıralama goals, assists veya rating olmalı.")

    if min_matches < 1:
        raise ValueError("Minimum maç sayısı en az 1 olmalı.")

    position = position.strip().upper() if position else None
    element = element.strip().casefold() if element else None
    if element and player_elements is None:
        raise ValueError("Element filtresi için oyuncuların elementleri gerekli.")

    totals = {}
    ratings = {}

    for match in completed_matches:
        clubs = {
            "home": match["home_club_id"],
            "away": match["away_club_id"],
        }

        if position:
            matching_players = {
                slot["player_id"]
                for lineup in (match.get("lineups") or {}).values()
                for slot in lineup
                if slot["position"] == position
            }

        for stat in match["player_stats"]:
            match_club_id = clubs[stat["team"]]

            if club_id is not None and match_club_id != club_id:
                continue

            player_id = stat["player_id"]

            if position and player_id not in matching_players:
                continue
            if element and (player_elements.get(player_id) or "none").casefold() != element:
                continue

            if player_id not in totals:
                totals[player_id] = {
                    "player_id": player_id,
                    "matches_played": 0,
                    "minutes_played": 0,
                    "goals": 0,
                    "assists": 0,
                }

            if sort_by == "rating" and stat.get("rating") is not None:
                ratings.setdefault(player_id, []).append(stat["rating"])

            row = totals[player_id]
            row["matches_played"] += 1
            row["minutes_played"] += stat["minutes_played"]
            row["goals"] += stat["goals"]
            row["assists"] += stat["assists"]

    rows = [
        row for row in totals.values()
        if row["matches_played"] >= min_matches
    ]

    if sort_by == "rating":
        ranked = []
        for row in rows:
            scores = ratings.get(row["player_id"], [])
            if len(scores) < min_matches:
                continue
            last = scores[-5:]
            ranked.append({
                **row,
                "rated_matches": len(scores),
                "avg_rating": round(sum(scores) / len(scores), 2),
                "last_5_rating": round(sum(last) / len(last), 2),
            })
        return sorted(ranked, key=lambda row: (-row["avg_rating"], row["player_id"]))

    secondary = "assists" if sort_by == "goals" else "goals"

    return sorted(
        rows,
        key=lambda row: (
            -row[sort_by],
            -row[secondary],
            row["player_id"],
        ),
    )
