from contextlib import closing, contextmanager


@contextmanager
def career_transaction(uid, connect=None):
    if connect is None:
        from backend.db import get_connection
        connect = get_connection
    with closing(connect()) as conn:
        try:
            with closing(conn.cursor()) as cur:
                # Hafta ilerletme ve diğer transferlerle aynı kariyer satırını kilitle.
                cur.execute("""UPDATE public.career SET season_no=season_no WHERE career_id=?
                               RETURNING managed_club_id""", (uid,))
                row = cur.fetchone()
                if row is None:
                    raise KeyError("Kariyer bulunamadı.")
                yield cur, row[0]
            conn.commit()
        except Exception:
            conn.rollback()
            raise
