def club_name(teams, club_id):
    return teams[club_id].get("name") or f"Kulüp {club_id}"


def player_names(teams):
    names = {}
    for team in teams.values():
        for player_id, player in team["players"].items():
            full_name = " ".join(
                part for part in (player.get("first_name"), player.get("last_name"))
                if part
            )
            names[player_id] = full_name or f"Oyuncu {player_id}"
    return names


def named_standings(rows, teams):
    return [
        {**row, "club_name": club_name(teams, row["club_id"])}
        for row in rows
    ]


def named_fixture(row, teams):
    if row is None:
        return None

    return {
        **row,
        "home_club_name": club_name(teams, row["home_club_id"]),
        "away_club_name": club_name(teams, row["away_club_id"]),
    }


def named_players(rows, names):
    return [
        {**row, "player_name": names.get(row["player_id"], f"Oyuncu {row['player_id']}")}
        for row in rows
    ]