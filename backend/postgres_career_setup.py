import json
from contextlib import closing


def insert_many(cursor, table, columns, rows):
    # Tablo ve sütun adları yalnızca aşağıdaki sabitlerden gelir.
    markers = ", ".join("?" for _ in columns.split(","))
    data = list(rows)
    if data:
        cursor.executemany(f"INSERT INTO public.{table} ({columns}) VALUES ({markers})", data)


def insert_world(cursor, key, career):
    season = career.season
    teams = season.teams
    insert_many(cursor, "club", "career_id,club_id,name,budget,formation", (
        (key, cid, t["name"], t["budget"], t["formation"]) for cid, t in teams.items()
    ))
    attributes = ("first_name", "last_name", "age", "primary_position", "element",
                  "market_value", "defending", "strength", "stamina", "passing",
                  "dribbling", "shooting", "pace")
    insert_many(cursor, "player", "career_id,player_id,club_id," + ",".join(attributes), (
        (key, pid, cid, *(p[field] for field in attributes))
        for cid, t in teams.items() for pid, p in t["players"].items()
    ))
    insert_many(cursor, "player_position", "career_id,player_id,position,compatibility", (
        (key, pid, position, score) for t in teams.values()
        for pid, p in t["players"].items() for position, score in p["compatibility"].items()
    ))
    insert_many(cursor, "lineup_selection", "career_id,club_id,slot_id,position,player_id", (
        (key, cid, s["slot_id"], t["formation_slots"][s["slot_id"]], s["player_id"])
        for cid, t in teams.items() for s in t["selections"]
    ))
    insert_many(cursor, "career_bonus_rule",
                "career_id,element,required_count,defense_bonus_pct,midfield_bonus_pct,attack_bonus_pct", (
        (key, r["element"], r["required_count"], r["defense_bonus_pct"],
         r["midfield_bonus_pct"], r["attack_bonus_pct"]) for r in season.bonus_rules
    ))
    cursor.execute("INSERT INTO public.season (career_id,season_no,next_week,last_week) VALUES (?,?,?,?)",
                   (key, career.season_no, season.next_week, season.last_week))
    insert_many(cursor, "fixture", "career_id,season_no,match_id,week_no,home_club_id,away_club_id", (
        (key, career.season_no, g["match_id"], g["week_no"], g["home_club_id"], g["away_club_id"])
        for g in season.fixtures
    ))


def ensure_career(user_id, *, connect=None, make_career=None):
    """İlk çağrıda dünyayı oluşturur. Sonraki çağrılar aynı kariyer kimliğini döndürür."""
    if connect is None:
        from backend.db import get_connection
        connect = get_connection
    if make_career is None:
        from backend.club_generation import new_user_career
        make_career = new_user_career

    managed_club = 10
    with closing(connect()) as conn:
        # get_connection varsayılan olarak autocommit=False kullanır.
        try:
            with closing(conn.cursor()) as cur:
                cur.execute("""
                    INSERT INTO public.career (career_id, managed_club_id, season_no, rng_state)
                    VALUES (?, ?, 1, ?) ON CONFLICT (career_id) DO NOTHING
                    RETURNING career_id
                """, (user_id, managed_club, ""))
                if cur.fetchone() is not None:
                    career = make_career(managed_club)
                    insert_world(cur, user_id, career)
                    cur.execute("UPDATE public.career SET rng_state=? WHERE career_id=?",
                                (json.dumps(career.rng.getstate()), user_id))
            conn.commit()
        except Exception:
            conn.rollback()
            raise
    return user_id
