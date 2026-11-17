"""Kişisel kariyer için PostgreSQL okuma ve yazma bağlantıları."""
import os
from contextlib import closing, contextmanager

from fastapi import Depends, HTTPException, Request

from backend.auth import current_user
from backend.postgres_career_setup import ensure_career
from backend.postgres_club import ClubConflict, name_sql_club, save_sql_lineup
from backend.postgres_season import read_season_archive, start_sql_season
from backend.postgres_transfers import (
    cancel_sql_offer, create_sql_offer, read_transfer_book, resolve_sql_offer,
)
from backend.postgres_week import WeekConflict, advance_sql_week, read_week_career
from backend.transfer_offers import OfferConflict


def postgres_enabled():
    mode = os.environ.get("BIL372_USER_STORE", "memory").strip().lower()
    if mode not in ("memory", "postgres"):
        raise ValueError("BIL372_USER_STORE memory veya postgres olmalı.")
    return mode == "postgres"


def connect():
    from backend.db import get_connection
    return get_connection()


@contextmanager
def snapshot():
    with closing(connect()) as db, closing(db.cursor()) as cur:
        cur.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY")
        yield cur


def read_sql_career(request: Request, user: dict = Depends(current_user)):
    uid = user["user_id"]
    season_arg = request.path_params.get("season_no", request.query_params.get("season_no"))
    try:
        requested = int(season_arg) if season_arg is not None else None
    except (ValueError, TypeError):
        raise HTTPException(422, "Geçersiz sezon numarası.")
    for attempt in range(2):
        with snapshot() as cur:
            career = read_week_career(cur, uid)
            if career is not None:
                career.offers = read_transfer_book(cur, uid)
                if requested is not None and 0 < requested < career.season_no:
                    try:
                        career.history[requested] = read_season_archive(cur, uid, requested)
                    except KeyError as error:
                        raise HTTPException(404, error.args[0]) from error
                return career
        if attempt == 0:
            ensure_career(uid, connect=connect)
    raise HTTPException(404, "Kariyer bulunamadı.")


def sql_user_id(user: dict = Depends(current_user)):
    uid = user["user_id"]
    ensure_career(uid, connect=connect)
    return uid


def run(command, uid, *args):
    try:
        return command(uid, *args, connect=connect)
    except (ClubConflict, WeekConflict, OfferConflict) as error:
        raise HTTPException(409, str(error)) from error
    except KeyError as error:
        raise HTTPException(404, error.args[0]) from error
    except ValueError as error:
        raise HTTPException(422, error.args[0]) from error
