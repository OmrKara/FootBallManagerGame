def calculate_standings(club_ids, completed_matches):
    table = {}

    for club_id in club_ids:
        if club_id in table:
            raise ValueError("Bir kulüp aynı sezonda iki kez listelenemez.")

        table[club_id] = {
            "club_id": club_id,
            "played": 0,
            "won": 0,
            "drawn": 0,
            "lost": 0,
            "goals_for": 0,
            "goals_against": 0,
            "goal_difference": 0,
            "points": 0,
        }

    seen_matches = set()

    for match in completed_matches:
        match_id = match["match_id"]
        home_id = match["home_club_id"]
        away_id = match["away_club_id"]
        home_goals = match["home_goals"]
        away_goals = match["away_goals"]

        if match_id in seen_matches:
            raise ValueError(f"{match_id} numaralı maç listede iki kez bulunuyor.")

        if home_id == away_id:
            raise ValueError("Bir kulüp kendi kendisiyle maç yapamaz.")

        if home_id not in table or away_id not in table:
            raise ValueError("Maçtaki iki kulüp de bu sezona ait olmalı.")

        for goals in (home_goals, away_goals):
            if type(goals) is not int or goals < 0:
                raise ValueError("Tamamlanan maçın gol sayıları negatif olmayan tam sayı olmalı.")

        seen_matches.add(match_id)
        home = table[home_id]
        away = table[away_id]

        home["played"] += 1
        away["played"] += 1
        home["goals_for"] += home_goals
        home["goals_against"] += away_goals
        away["goals_for"] += away_goals
        away["goals_against"] += home_goals

        if home_goals > away_goals:
            home["won"] += 1
            away["lost"] += 1
        elif home_goals < away_goals:
            away["won"] += 1
            home["lost"] += 1
        else:
            home["drawn"] += 1
            away["drawn"] += 1

    for row in table.values():
        row["points"] = 3 * row["won"] + row["drawn"]
        row["goal_difference"] = row["goals_for"] - row["goals_against"]

    return sorted(
        table.values(),
        key=lambda row: (
            -row["points"],
            -row["goal_difference"],
            -row["goals_for"],
            row["club_id"],
        ),
    )