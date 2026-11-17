def validate_lineup(club_player_ids, formation_slot_ids, selections):
    errors = []

    if len(selections) != 11:
        errors.append("İlk 11 tam olarak 11 seçim içermeli.")

    selected_players = set()
    selected_slots = set()

    for selection in selections:
        player_id = selection["player_id"]
        slot_id = selection["slot_id"]

        if player_id not in club_player_ids:
            errors.append(f"{player_id} numaralı oyuncu bu kulübün kadrosunda yok.")

        if player_id in selected_players:
            errors.append(f"{player_id} numaralı oyuncu birden fazla kez seçilmiş.")

        if slot_id not in formation_slot_ids:
            errors.append(f"{slot_id} numaralı slot seçilen formasyonda yok.")

        if slot_id in selected_slots:
            errors.append(f"{slot_id} numaralı slota birden fazla oyuncu atanmış.")

        selected_players.add(player_id)
        selected_slots.add(slot_id)

    missing_slots = sorted(formation_slot_ids - selected_slots)

    if missing_slots:
        missing_text = ", ".join(str(slot_id) for slot_id in missing_slots)
        errors.append(f"Boş kalan formasyon slotları: {missing_text}.")

    return {"valid": not errors, "errors": errors}