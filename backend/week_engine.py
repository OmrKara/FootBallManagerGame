import random

from backend.match_engine import play_match


def play_week(week_no, fixtures, teams, bonus_rules, *, rng=None):
    weekly_games = [game for game in fixtures if game["week_no"] == week_no]

    if not weekly_games:
        return {
            "valid": False,
            "errors": [f"{week_no}. hafta için fikstürde maç bulunamadı."],
        }

    participating = set()
    errors = []

    for game in weekly_games:
        for club_id in (game["home_club_id"], game["away_club_id"]):
            if club_id in participating:
                errors.append(f"{club_id} numaralı kulüp aynı haftada iki kez yer alıyor.")
            if club_id not in teams:
                errors.append(f"{club_id} numaralı kulübün kadrosu bulunamadı.")

            participating.add(club_id)

    if errors:
        return {"valid": False, "errors": errors}

    if rng is None:
        rng = random.Random()

    results = []

    for game in weekly_games:
        home_id = game["home_club_id"]
        away_id = game["away_club_id"]

        result = play_match(
            teams[home_id],
            teams[away_id],
            bonus_rules,
            rng=rng,
        )

        if not result["valid"]:
            return {
                "valid": False,
                "errors": [{
                    "home_club_id": home_id,
                    "away_club_id": away_id,
                    "details": result["errors"],
                }],
            }

        results.append({
            **game,
            **result["match"],
        })

    return {
        "valid": True,
        "week_no": week_no,
        "matches": results,
    }