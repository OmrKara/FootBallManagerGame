from backend.postgres_transaction import career_transaction as transfer_transaction

from backend.postgres_career_load import read_rows, read_season_state
from backend.transfer_offers import OfferConflict, TransferOffers


def read_transfer_book(cur, uid):
    book = TransferOffers()
    columns = ("offer_id,buyer_club_id,seller_club_id,player_id,amount,"
               "created_week,status,reason,resolved_week")
    for row in read_rows(cur, "transfer_offer", columns, uid, "offer_id"):
        offer = {k: v for k, v in row.items() if v is not None}
        book.offers[offer["offer_id"]] = offer
    book.next_id = max(book.offers, default=0) + 1

    for row in read_rows(cur, "transfer", "offer_id,season_no,week_no", uid, "transfer_no"):
        offer = book.offers[row["offer_id"]]
        book.transfers.append(dict(row, player_id=offer["player_id"], fee=offer["amount"],
                                   from_club_id=offer["seller_club_id"], to_club_id=offer["buyer_club_id"]))
    return book


def create_sql_offer(uid, player_id, amount, expected_season, expected_week, *, connect=None):
    with transfer_transaction(uid, connect) as (cur, buyer):
        career = read_season_state(cur, uid)
        season = career.season
        if season.finished or (career.season_no, season.next_week) != (expected_season, expected_week):
            raise OfferConflict("Sezon veya hafta güncel değil.")
        book = read_transfer_book(cur, uid)
        offer = book.create(season.teams, buyer, player_id, amount, expected_week)
        cur.execute("""INSERT INTO public.transfer_offer
            (career_id,offer_id,buyer_club_id,seller_club_id,player_id,amount,created_season,created_week,status)
            VALUES (?,?,?,?,?,?,?,?,?)""", (uid, offer["offer_id"], buyer, offer["seller_club_id"],
                                             player_id, amount, expected_season, expected_week, offer["status"]))
    return offer


def cancel_sql_offer(uid, offer_id, *, connect=None):
    with transfer_transaction(uid, connect) as (cur, buyer):
        offer = read_transfer_book(cur, uid).cancel(offer_id, buyer)
        cur.execute("UPDATE public.transfer_offer SET status=? WHERE career_id=? AND offer_id=?",
                    (offer["status"], uid, offer_id))
    return offer


def resolve_sql_offer(uid, offer_id, *, connect=None):
    with transfer_transaction(uid, connect) as (cur, buyer):
        career = read_season_state(cur, uid)
        season = career.season
        if season.finished:
            raise OfferConflict("Sezon tamamlandı.")
        book = read_transfer_book(cur, uid)
        offer = book.resolve(season.teams, offer_id, buyer, season.next_week, season_no=career.season_no)
        cur.execute("""UPDATE public.transfer_offer SET status=?,reason=?,resolved_week=?
                       WHERE career_id=? AND offer_id=?""",
                    (offer["status"], offer.get("reason"), offer.get("resolved_week"), uid, offer_id))
        if offer["status"] == "ACCEPTED":
            seller = offer["seller_club_id"]
            cur.execute("UPDATE public.player SET club_id=? WHERE career_id=? AND player_id=?",
                        (buyer, uid, offer["player_id"]))
            for club_id in (seller, buyer):
                cur.execute("UPDATE public.club SET budget=? WHERE career_id=? AND club_id=?",
                            (season.teams[club_id]["budget"], uid, club_id))
            cur.execute("""INSERT INTO public.transfer (career_id,transfer_no,offer_id,season_no,week_no)
                           VALUES (?,?,?,?,?)""", (uid, len(book.transfers), offer_id,
                                                   career.season_no, season.next_week))
    return offer
