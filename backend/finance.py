def transfer_finance_summary(club_id, budget, transfers):
    income = 0
    expense = 0
    movements = []

    for transfer in transfers:
        fee = transfer["fee"]

        if transfer["to_club_id"] == club_id:
            kind = "TRANSFER_OUT"
            amount = -fee
            other_club_id = transfer["from_club_id"]
            expense += fee
        elif transfer["from_club_id"] == club_id:
            kind = "TRANSFER_IN"
            amount = fee
            other_club_id = transfer["to_club_id"]
            income += fee
        else:
            continue

        movements.append({
            "offer_id": transfer["offer_id"],
            "season_no": transfer.get("season_no", 1),
            "week_no": transfer["week_no"],
            "player_id": transfer["player_id"],
            "other_club_id": other_club_id,
            "type": kind,
            "amount": amount,
        })

    return {
        "club_id": club_id,
        "budget": budget,
        "transfer_income": income,
        "transfer_expense": expense,
        "net_transfer": income - expense,
        "movements": movements[::-1],
    }