from backend.postgres_career_load import read_rows
from backend.postgres_career_setup import insert_many
from backend.postgres_transaction import career_transaction
from backend.postgres_week import read_completed_matches, read_week_career
from backend.standings import calculate_standings


def start_sql_season(uid, expected_season, *, connect=None):
    with career_transaction(uid, connect) as (cur, _):
        career = read_week_career(cur, uid)
        result = career.start_next_season(expected_season)
        number = career.season_no
        season = career.season
        cur.execute("""INSERT INTO public.season (career_id,season_no,next_week,last_week)
                       VALUES (?,?,?,?)""", (uid, number, season.next_week, season.last_week))
        insert_many(cur, "fixture", "career_id,season_no,match_id,week_no,home_club_id,away_club_id", (
            (uid, number, f["match_id"], f["week_no"], f["home_club_id"], f["away_club_id"])
            for f in season.fixtures
        ))
        cur.execute("UPDATE public.career SET season_no=? WHERE career_id=?", (number, uid))
    return result


def read_season_archive(cur, uid, season_no):
    """Yalnızca kullanıcının geçmiş sezonlarını, kaydedilen maçlardan oluşturur."""
    cur.execute("""SELECT s.season_no FROM public.season s
                   JOIN public.career c ON c.career_id=s.career_id
                   WHERE s.career_id=? AND s.season_no=? AND s.next_week IS NULL
                     AND s.season_no < c.season_no""", (uid, season_no))
    if cur.fetchone() is None:
        raise KeyError("Arşivde bu sezon bulunamadı.")
    fixtures = read_rows(cur, "fixture", "match_id,week_no,home_club_id,away_club_id",
                         uid, "week_no,match_id", season_no)
    matches = read_completed_matches(cur, uid, season_no, fixtures)
    clubs = sorted({f[side] for f in fixtures for side in ("home_club_id", "away_club_id")})
    return {"season_no": season_no, "matches": matches, "standings": calculate_standings(clubs, matches)}
