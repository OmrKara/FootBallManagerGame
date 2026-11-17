"""Yeni kariyerlerde dört elementin dağılımı ve bonus kuralları."""

# Sırasıyla DEF, MID, ATT yüzdeleri. Her elementte yalnız en yüksek eşik uygulanır.
BONUS_TIERS = {
    "Fire":  [(4, 0, 0, 5), (6, 0, 0, 10)],
    "Earth": [(4, 5, 0, 0), (6, 10, 0, 0)],
    "Air":   [(4, 0, 5, 0), (6, 0, 10, 0)],
    "Water": [(4, 2, 2, 2), (6, 4, 4, 4)],
}


def career_bonus_rules():
    return [
        {
            "element": element,
            "required_count": count,
            "defense_bonus_pct": defense,
            "midfield_bonus_pct": midfield,
            "attack_bonus_pct": attack,
        }
        for element, tiers in BONUS_TIERS.items()
        for count, defense, midfield, attack in tiers
    ]


def assign_starting_elements(teams):
    # İlk kulüpte ilk 11: 4 Fire, 3 Earth, 2 Air, 2 Water. Yedek: Earth.
    # Diğer kulüplerde elementler döner; dört bonus da ligde görülebilir.
    elements = ("Fire", "Earth", "Air", "Water")
    pattern = (0, 0, 0, 0, 1, 1, 1, 2, 2, 3, 3)
    for offset, team in enumerate(teams.values()):
        starters = {s["player_id"]: s["slot_id"] for s in team["selections"]}
        for player_id, player in team["players"].items():
            slot = starters.get(player_id)
            group = pattern[slot - 1] if slot is not None else 1
            player["element"] = elements[(group + offset) % len(elements)]
