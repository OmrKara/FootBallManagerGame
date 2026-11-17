from collections import Counter


def apply_element_bonuses(base_power, lineup_elements, bonus_rules):
    if len(lineup_elements) != 11:
        raise ValueError("Element hesabı için ilk 11'in elementleri gerekli.")

    element_counts = Counter(element for element in lineup_elements if element is not None)
    active_rules = {}

    for rule in bonus_rules:
        element = rule["element"]
        required = rule["required_count"]

        if element_counts[element] < required:
            continue

        current_rule = active_rules.get(element)
        if current_rule is None or required > current_rule["required_count"]:
            active_rules[element] = rule

    total_bonus = {"DEF": 0, "MID": 0, "ATT": 0}

    for rule in active_rules.values():
        total_bonus["DEF"] += rule["defense_bonus_pct"]
        total_bonus["MID"] += rule["midfield_bonus_pct"]
        total_bonus["ATT"] += rule["attack_bonus_pct"]

    final_power = {}

    for region, percent in total_bonus.items():
        final_power[region] = round(base_power[region] * (1 + percent / 100), 2)

    return {
        "element_counts": dict(element_counts),
        "active_bonuses": list(active_rules.values()),
        "bonus_percent": total_bonus,
        "final_power": final_power,
    }