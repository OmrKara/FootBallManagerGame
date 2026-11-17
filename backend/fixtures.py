def generate_fixtures(club_ids, *, double_round=True):
    clubs = list(club_ids)

    if len(clubs) < 2:
        raise ValueError("Fikstür için en az iki kulüp gerekli.")

    if any(type(club_id) is not int or club_id <= 0 for club_id in clubs):
        raise ValueError("Kulüp ID'leri pozitif tam sayı olmalı.")

    if len(set(clubs)) != len(clubs):
        raise ValueError("Bir kulüp sezonda iki kez yer alamaz.")

    # Tek sayıda kulüp varsa None ile eşleşen takım o hafta bay geçer.
    if len(clubs) % 2 == 1:
        clubs.append(None)

    first_half = []
    week_count = len(clubs) - 1

    for week in range(1, week_count + 1):
        for i in range(len(clubs) // 2):
            home = clubs[i]
            away = clubs[-1 - i]

            if home is None or away is None:
                continue

            if i == 0 and week % 2 == 0:
                home, away = away, home

            first_half.append({
                "week_no": week,
                "home_club_id": home,
                "away_club_id": away,
            })

        # İlk kulüp sabit kalır, diğerleri bir sıra döner.
        clubs = [clubs[0], clubs[-1], *clubs[1:-1]]

    if not double_round:
        return first_half

    second_half = [
        {
            "week_no": game["week_no"] + week_count,
            "home_club_id": game["away_club_id"],
            "away_club_id": game["home_club_id"],
        }
        for game in first_half
    ]

    return first_half + second_half