import json
from contextlib import closing

from backend.postgres_career_load import read_rows, read_season_state
from backend.postgres_career_setup import insert_many


class WeekConflict(ValueError):
    pass


KEY = "career_id,season_no,match_id,"
STATS = "player_id,team,minutes_played,goals,assists,rating"


def read_week_career(cur, uid):
    career = read_season_state(cur, uid)
    if career is None:
        return None
    career.season.completed_matches = read_completed_matches(cur, uid, career.season_no, career.season.fixtures)
    return career


def read_completed_matches(cur, uid, number, season_fixtures):
    fixtures = {f["match_id"]: f for f in season_fixtures}
    games = {}
    for row in read_rows(cur, "match_result", "match_id,home_goals,away_goals,home_formation,away_formation",
                         uid, "match_id", number):
        mid = row["match_id"]
        games[mid] = dict(fixtures[mid], home_goals=row["home_goals"], away_goals=row["away_goals"],
                          formations={"home": row["home_formation"], "away": row["away_formation"]},
                          lineups={"home": [], "away": []}, events=[], player_stats=[])
    for row in read_rows(cur, "match_lineup", "match_id,team,slot_id,position,player_id",
                         uid, "match_id,team,slot_id", number):
        game = games[row.pop("match_id")]
        game["lineups"][row.pop("team")].append(row)
    for table, columns, destination in (
        ("match_event", "minute,team,event_type,player_id", "events"),
        ("match_player_stat", STATS, "player_stats"),
    ):
        for row in read_rows(cur, table, "match_id," + columns, uid, "match_id,sequence_no", number):
            games[row.pop("match_id")][destination].append(row)
    return [games[mid] for mid in fixtures if mid in games]


def save_match(cur, uid, number, game):
    key = (uid, number, game["match_id"])
    insert_many(cur, "match_result", KEY + "home_goals,away_goals,home_formation,away_formation",
                [(*key, game["home_goals"], game["away_goals"], game["formations"]["home"],
                  game["formations"]["away"])])
    insert_many(cur, "match_lineup", KEY + "team,slot_id,position,player_id", (
        (*key, side, p["slot_id"], p["position"], p["player_id"])
        for side, players in game["lineups"].items() for p in players
    ))
    insert_many(cur, "match_event", KEY + "sequence_no,minute,team,event_type,player_id", (
        (*key, i, e["minute"], e["team"], e["event_type"], e["player_id"])
        for i, e in enumerate(game["events"])
    ))
    insert_many(cur, "match_player_stat", KEY + "sequence_no," + STATS, (
        (*key, i, *(p[field] for field in STATS.split(",")))
        for i, p in enumerate(game["player_stats"])
    ))


def advance_sql_week(user_id, expected_season, expected_week, *, connect=None):
    if connect is None:
        from backend.db import get_connection
        connect = get_connection
    with closing(connect()) as conn:
        try:
            with closing(conn.cursor()) as cur:
                # Kariyer satırı kilidi, aynı hesaba gelen iki haftayı sıraya alır.
                cur.execute("""UPDATE public.career SET season_no=season_no
                               WHERE career_id=? AND season_no=? RETURNING career_id""",
                            (user_id, expected_season))
                if cur.fetchone() is None:
                    raise WeekConflict("Kariyer veya sezon güncel değil.")
                career = read_week_career(cur, user_id)
                season = career.season
                if season.finished or expected_week != season.next_week:
                    raise WeekConflict("Hafta güncel değil veya sezon tamamlandı.")
                result = season.advance_week(expected_week, rng=career.rng)
                if not result["valid"]:
                    raise ValueError(result["errors"])
                for game in result["matches"]:
                    save_match(cur, user_id, expected_season, game)
                if season.finished:
                    cur.executemany("""UPDATE public.player SET age=?, defending=?, passing=?, shooting=?
                                       WHERE career_id=? AND player_id=?""", [
                        (p["age"], p["defending"], p["passing"], p["shooting"], user_id, pid)
                        for team in season.teams.values() for pid, p in team["players"].items()
                    ])
                cur.execute("UPDATE public.season SET next_week=? WHERE career_id=? AND season_no=?",
                            (season.next_week, user_id, expected_season))
                cur.execute("UPDATE public.career SET rng_state=? WHERE career_id=?",
                            (json.dumps(career.rng.getstate()), user_id))
            conn.commit()
        except Exception:
            conn.rollback()
            raise
    return result
