from backend.demo_data import DEMO_FORMATIONS, formation_slots
from backend.postgres_career_load import read_rows, read_season_state
from backend.postgres_career_setup import insert_many
from backend.postgres_transaction import career_transaction
from backend.team_power import calculate_team_power


class ClubConflict(ValueError):
    """Mevcut kulüp veya sezon durumu isteğe izin vermiyor."""


def name_sql_club(uid, name, *, connect=None):
    if not isinstance(name, str) or len(name) > 60:
        raise ValueError("Kulüp adı 1 ile 60 karakter arasında olmalı.")
    name = " ".join(name.split())
    if not name:
        raise ValueError("Kulüp adı boş olamaz.")

    with career_transaction(uid, connect) as (cur, managed):
        clubs = read_rows(cur, "club", "club_id,name", uid, "club_id")
        own = next(c for c in clubs if c["club_id"] == managed)
        if own["name"] and own["name"] != name:
            raise ClubConflict("Kulübün adı zaten seçilmiş.")
        if any(c["club_id"] != managed and (c["name"] or "").casefold() == name.casefold()
               for c in clubs):
            raise ClubConflict("Bu kulüp adı ligde kullanılıyor.")
        if own["name"] != name:
            cur.execute("UPDATE public.club SET name=? WHERE career_id=? AND club_id=?",
                        (name, uid, managed))
            own["name"] = name
    return {"club_id": managed, "name": name, "clubs": clubs}


def save_sql_lineup(uid, selections, expected_season, expected_week, formation=None, *, connect=None):
    with career_transaction(uid, connect) as (cur, managed):
        career = read_season_state(cur, uid)
        season = career.season
        if season.finished or (career.season_no, season.next_week) != (expected_season, expected_week):
            raise ClubConflict("Sezon tamamlandı veya ekrandaki sezon/hafta güncel değil.")

        team = season.teams[managed]
        name = team["formation"] if formation is None else formation
        if name not in DEMO_FORMATIONS:
            raise ValueError("Bilinmeyen formasyon.")
        slots = formation_slots(name)
        power = calculate_team_power(team["players"], slots, selections, season.bonus_rules)
        if not power["valid"]:
            raise ValueError(power["errors"])

        cur.execute("UPDATE public.club SET formation=? WHERE career_id=? AND club_id=?",
                    (name, uid, managed))
        cur.execute("DELETE FROM public.lineup_selection WHERE career_id=? AND club_id=?",
                    (uid, managed))
        insert_many(cur, "lineup_selection", "career_id,club_id,slot_id,position,player_id", (
            (uid, managed, s["slot_id"], slots[s["slot_id"]], s["player_id"]) for s in selections
        ))
    return dict(club_id=managed, season_no=career.season_no, next_week=season.next_week,
                formation=name, selections=selections, power=power)
