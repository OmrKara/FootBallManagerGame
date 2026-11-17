def matches_club_filters(game, club_id, opponent_id=None, venue=None, result=None):
    if opponent_id is None and venue is None and result is None:
        return True

    home = game["home_club_id"]
    away = game["away_club_id"]
    if club_id not in (home, away):
        return False

    at_home = home == club_id
    opponent = away if at_home else home
    if opponent_id is not None and opponent_id != opponent:
        return False
    if venue is not None and venue != ("home" if at_home else "away"):
        return False
    if result is None:
        return True
    if game["status"] != "played":
        return False

    difference = game["home_goals"] - game["away_goals"]
    if not at_home:
        difference = -difference
    if difference == 0:
        return result == "draw"
    return result == ("win" if difference > 0 else "loss")
