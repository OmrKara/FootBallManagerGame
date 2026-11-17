from itertools import product
from random import Random

from backend.career import Career

ADJECTIVES = ("Çevik", "Gümüş", "Altın", "Kızıl", "Cesur", "Hızlı", "Mavi", "Kara")
ANIMALS = ("Şahinler", "Kurtlar", "Kartallar", "Kaplanlar", "Aslanlar", "Panterler")
FIRST_NAMES = ("Arda", "Deniz", "Ege", "Mert", "Kerem", "Can", "Efe", "Umut",
               "Berk", "Ozan", "Onur", "Alp", "Emre", "Yiğit", "Ulaş", "Kaan")
SURNAMES = ("Yıldız", "Kaya", "Demir", "Aksoy", "Aydın", "Güneş", "Yılmaz",
            "Çelik", "Eren", "Yalçın", "Öztürk", "Sezer", "Taş", "Bulut")
ATTRIBUTES = ("defending", "strength", "stamina", "passing", "dribbling", "shooting", "pace")
ELEMENTS = ("Fire", "Earth", "Air", "Water")


def draw_element(rng):
    return rng.choice(ELEMENTS) if rng.random() < 0.70 else None


def new_user_career(club_id, rng=None):
    rng = Random() if rng is None else rng
    career = Career()
    teams = career.season.teams
    bot_names = iter(rng.sample(list(product(ADJECTIVES, ANIMALS)), len(teams) - 1))
    count = sum(len(team["players"]) for team in teams.values())
    names = iter(rng.sample(list(product(FIRST_NAMES, SURNAMES)), count))
    for team_id, team in teams.items():
        team["name"] = None if team_id == club_id else " ".join(next(bot_names))
        for player in team["players"].values():
            player["first_name"], player["last_name"] = next(names)
            for attribute in ATTRIBUTES:
                player[attribute] = rng.randint(50, 90)
            player["element"] = draw_element(rng)
    return career
