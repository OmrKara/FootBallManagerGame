from backend.element_bonus import apply_element_bonuses
from backend.lineup import validate_lineup


POWER_WEIGHTS = {
    "DEF": {"defending": 0.50, "strength": 0.30, "stamina": 0.20},
    "MID": {"passing": 0.50, "dribbling": 0.30, "stamina": 0.20},
    "ATT": {"shooting": 0.50, "pace": 0.30, "dribbling": 0.20},
}


def calculate_team_power(players, formation_slots, selections, bonus_rules):
    lineup = validate_lineup(set(players), set(formation_slots), selections)

    if not lineup["valid"]:
        return lineup

    if len(formation_slots) != 11:
        return {"valid": False, "errors": ["Formasyon 11 slot içermeli."]}

    totals = {"DEF": 0.0, "MID": 0.0, "ATT": 0.0}
    elements = []
    errors = []

    for selection in selections:
        player_id = selection["player_id"]
        player = players[player_id]
        position = formation_slots[selection["slot_id"]]
        compatibility = player["compatibility"].get(position)

        if compatibility is None:
            errors.append(
                f"{player_id} numaralı oyuncunun {position} pozisyonu için "
                "uyum kaydı bulunamadı."
            )
            continue

        if not 1 <= compatibility <= 100:
            errors.append(
                f"{player_id} numaralı oyuncunun pozisyon uyumu "
                "1 ile 100 arasında olmalı."
            )
            continue

        for region, weights in POWER_WEIGHTS.items():
            contribution = sum(
                player[attribute] * weight
                for attribute, weight in weights.items()
            )
            totals[region] += contribution * compatibility / 100

        elements.append(player["element"])

    if errors:
        return {"valid": False, "errors": errors}

    base_power = {
        region: round(total / 11, 2)
        for region, total in totals.items()
    }
    bonuses = apply_element_bonuses(base_power, elements, bonus_rules)

    return {
        "valid": True,
        "errors": [],
        "base_power": base_power,
        **bonuses,
    }