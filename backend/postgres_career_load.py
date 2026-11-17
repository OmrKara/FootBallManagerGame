import json
from contextlib import closing

from backend.career import Career
from backend.season_engine import SeasonEngine


def read_rows(cursor, table, columns, user_id, order_by, season_no=None):
    sql = f"SELECT {columns} FROM public.{table} WHERE career_id=?"
    params = [user_id]
    if season_no is not None:
        sql += " AND season_no=?"
        params.append(season_no)
    # Tablo, sütun ve sıralama adları modüldeki sabitlerden gelir.
    cursor.execute(sql + " ORDER BY " + order_by, tuple(params))
    keys = columns.split(",")
    return [dict(zip(keys, row)) for row in cursor.fetchall()]


def read_season_state(cursor, user_id, *, initial_only=False):
    cursor.execute("SELECT season_no,rng_state FROM public.career WHERE career_id=?", (user_id,))
    header = cursor.fetchone()
    if header is None:
        return None
    number, rng_state = header
    cursor.execute("SELECT next_week,last_week FROM public.season WHERE career_id=? AND season_no=?",
                   (user_id, number))
    state = cursor.fetchone()
    if state is None:
        raise ValueError("Kariyerin aktif sezon kaydı eksik.")
    if initial_only and (number != 1 or state[0] != 1):
        raise ValueError("Bu okuyucu yalnızca ilk hafta oynanmadan önceki kariyeri yükler.")

    clubs = read_rows(cursor, "club", "club_id,name,budget,formation", user_id, "club_id")
    teams = {}
    for club in clubs:
        club_id = club.pop("club_id")
        teams[club_id] = dict(club, players={}, selections=[], formation_slots={})

    columns = ("player_id,club_id,first_name,last_name,age,primary_position,element,"
               "market_value,defending,strength,stamina,passing,dribbling,shooting,pace")
    players = {}
    for player in read_rows(cursor, "player", columns, user_id, "player_id"):
        player_id = player.pop("player_id")
        club_id = player.pop("club_id")
        player["compatibility"] = {}
        teams[club_id]["players"][player_id] = player
        players[player_id] = player

    for row in read_rows(cursor, "player_position", "player_id,position,compatibility",
                         user_id, "player_id,position"):
        players[row["player_id"]]["compatibility"][row["position"]] = row["compatibility"]

    for row in read_rows(cursor, "lineup_selection", "club_id,slot_id,position,player_id",
                         user_id, "club_id,slot_id"):
        team = teams[row["club_id"]]
        slot = row["slot_id"]
        team["formation_slots"][slot] = row["position"]
        team["selections"].append({"slot_id": slot, "player_id": row["player_id"]})

    fixtures = read_rows(cursor, "fixture", "match_id,week_no,home_club_id,away_club_id",
                         user_id, "week_no,match_id", number)
    rules = read_rows(cursor, "career_bonus_rule",
                      "element,required_count,defense_bonus_pct,midfield_bonus_pct,attack_bonus_pct",
                      user_id, "element,required_count")
    season = SeasonEngine(fixtures, teams, rules)
    if season.last_week != state[1]:
        raise ValueError("Sezon uzunluğu ile fikstür uyuşmuyor.")
    season.next_week = state[0]
    career = Career()
    career.season = season
    career.season_no = number
    version, internal, gaussian = json.loads(rng_state)
    career.rng.setstate((version, tuple(internal), gaussian))
    return career


def read_initial_career(cursor, user_id):
    return read_season_state(cursor, user_id, initial_only=True)


def load_initial_career(user_id, *, connect=None):
    if connect is None:
        from backend.db import get_connection
        connect = get_connection
    with closing(connect()) as conn:
        try:
            with closing(conn.cursor()) as cursor:
                cursor.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY")
                career = read_initial_career(cursor, user_id)
            conn.commit()
            return career
        except Exception:
            conn.rollback()
            raise
