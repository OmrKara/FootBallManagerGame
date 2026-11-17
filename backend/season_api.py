from contextlib import contextmanager
from threading import Lock
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from backend.demo_data import DEMO_FORMATIONS, formation_slots
from backend.career import Career
from backend.career_store import MemoryCareerStore
from backend.career_save import dump_career, load_career
from typing import Literal
from fastapi import Query
from backend.player_stats import summarize_player_stats
from backend.team_power import calculate_team_power
from backend.formation_stats import summarize_formation_stats
from backend.transfer_market import list_market_players
from backend.transfer_offers import OfferConflict
from backend.finance import transfer_finance_summary
from backend.auth import current_user
from backend import sql_api
from backend.fixture_filters import matches_club_filters
from backend.club_generation import new_user_career
from backend.display_names import named_fixture, named_players, named_standings, player_names


DEMO_USER_CLUB_ID = 10


class AdvanceWeekRequest(BaseModel):
    expected_week: int = Field(ge=1)
    expected_season: int = Field(default=1, ge=1, strict=True)

class NewSeasonRequest(BaseModel):
    expected_season: int = Field(ge=1)


def fixture_summary(fixture, completed):
    played = completed is not None

    return {
        "match_id": fixture["match_id"],
        "week_no": fixture["week_no"],
        "home_club_id": fixture["home_club_id"],
        "away_club_id": fixture["away_club_id"],
        "status": "played" if played else "scheduled",
        "home_goals": completed["home_goals"] if played else None,
        "away_goals": completed["away_goals"] if played else None,
    }


class LineupSelection(BaseModel):
    slot_id: int = Field(gt=0)
    player_id: int = Field(gt=0)


class SaveLineupRequest(BaseModel):
    expected_week: int = Field(ge=1)
    expected_season: int = Field(default=1, ge=1, strict=True)
    selections: list[LineupSelection]
    formation: str | None = None


class CreateOfferRequest(BaseModel):
    player_id: int = Field(gt=0, strict=True)
    amount: int = Field(gt=0, strict=True)
    expected_week: int = Field(ge=1, strict=True)
    expected_season: int = Field(default=1, ge=1, strict=True)


demo_career = Career()
career_store = MemoryCareerStore()
user_careers = {}
careers_lock = Lock()


def get_demo_career():
    return demo_career


def get_user_career(user: dict = Depends(current_user)):
    user_id = user["user_id"]
    with careers_lock:
        if user_id not in user_careers:
            career = career_store.load(user_id)
            if career is None:
                career = new_user_career(DEMO_USER_CLUB_ID)
                career_store.save(user_id, career)
            user_careers[user_id] = career
        return user_careers[user_id]


@contextmanager
def edit_demo_career(career):
    with career.lock:
        yield career


def user_editor(user: dict = Depends(current_user)):
    @contextmanager
    def edit(career):
        with career.lock:
            # İşlem veya kayıt başarısız olursa çalışan kariyer değişmez.
            working = load_career(dump_career(career))
            yield working
            career_store.save(user["user_id"], working)
            career.season = working.season
            career.season_no = working.season_no
            career.history = working.history
            career.rng = working.rng
            career.offers = working.offers

    return edit


def demo_editor():
    return edit_demo_career


def make_season_router(prefix, tag, get_career, get_editor, *, sql=False):
    router = APIRouter(prefix=prefix, tags=[tag])
    writes = APIRouter()

    @router.get("")
    def get_season(career: Career = Depends(get_career)):
        with career.lock:
            season = career.season
            club_id = DEMO_USER_CLUB_ID

            completed_by_id = {
                match["match_id"]: match
                for match in season.completed_matches
            }

            last_match = None
            next_match = None

            for fixture in season.fixtures:
                if club_id not in (fixture["home_club_id"], fixture["away_club_id"]):
                    continue

                completed = completed_by_id.get(fixture["match_id"])
                week = fixture["week_no"]

                if completed is not None:
                    if last_match is None or week > last_match["week_no"]:
                        last_match = fixture_summary(fixture, completed)
                elif next_match is None or week < next_match["week_no"]:
                    next_match = fixture_summary(fixture, None)

            return {
                "club_id": club_id,
                "budget": season.teams[club_id]["budget"],
                "season_no": career.season_no,
                "next_week": season.next_week,
                "last_week": season.last_week,
                "finished": season.finished,
                "standings": named_standings(season.standings(), season.teams),
                "last_match": named_fixture(last_match, season.teams),
                "next_match": named_fixture(next_match, season.teams),
            }

    @writes.post("/advance")
    def advance_season_week(request: AdvanceWeekRequest, career: Career = Depends(get_career),
        edit=Depends(get_editor),
    ):
        with edit(career) as career:
            if career.season.finished:
                raise HTTPException(status_code=409, detail="Sezon tamamlandı.")

            if (request.expected_season, request.expected_week) != (career.season_no, career.season.next_week):
                raise HTTPException(
                    status_code=409,
                    detail={
                        "message": "Ekrandaki sezon veya hafta güncel değil.",
                        "season_no": career.season_no,
                        "next_week": career.season.next_week,
                    },
                )

            result = career.season.advance_week(request.expected_week, rng=career.rng)

            if not result["valid"]:
                raise HTTPException(status_code=422, detail=result["errors"])

            return result

    def season_games(career, season_no):
        if season_no is None or season_no == career.season_no:
            return career.season.fixtures, career.season.completed_matches
        if season_no not in career.history:
            raise HTTPException(404, "Sezon bulunamadı.")
        matches = career.history[season_no]["matches"]
        return matches, matches

    @router.get("/fixtures")
    def get_fixtures(
        week_no: int | None = None,
        season_no: int | None = None,
        opponent_id: int | None = None,
        venue: Literal["home", "away"] | None = None,
        result: Literal["win", "draw", "loss"] | None = None,
        career: Career = Depends(get_career),
    ):
        with career.lock:
            fixtures, completed = season_games(career, season_no)
            if week_no is not None:
                last_week = max(game["week_no"] for game in fixtures)
                if not 1 <= week_no <= last_week:
                    raise HTTPException(422, f"Hafta 1 ile {last_week} arasında olmalı.")

            by_id = {game["match_id"]: game for game in completed}
            rows = []
            for fixture in fixtures:
                if week_no is not None and fixture["week_no"] != week_no:
                    continue
                row = fixture_summary(fixture, by_id.get(fixture["match_id"]))
                if matches_club_filters(row, DEMO_USER_CLUB_ID, opponent_id, venue, result):
                    rows.append(named_fixture(row, career.season.teams))
            return rows

    @router.get("/matches/{match_id}")
    def get_match_detail(
        match_id: int,
        season_no: int | None = None,
        event_type: Literal["GOAL", "ASSIST"] | None = None,
        career: Career = Depends(get_career),
    ):
        with career.lock:
            fixtures, matches = season_games(career, season_no)
            fixture = next(
                (game for game in fixtures if game["match_id"] == match_id),
                None,
            )

            if fixture is None:
                raise HTTPException(status_code=404, detail="Maç bulunamadı.")

            completed = next(
                (game for game in matches if game["match_id"] == match_id),
                None,
            )

            events = completed["events"] if completed is not None else []
            if event_type is not None:
                events = [
                    event for event in events
                    if event["event_type"] == event_type
                ]

            teams = career.season.teams
            names = player_names(teams)
            lineups = None

            if completed is not None:
                lineups = {
                    side: named_players(players, names)
                    for side, players in completed["lineups"].items()
                }

            return {
                **named_fixture(fixture_summary(fixture, completed), teams),
                "lineups": lineups,
                "events": named_players(events, names),
                "player_stats": named_players(
                    completed["player_stats"] if completed is not None else [],
                    names,
                ),
                "formations": completed["formations"] if completed is not None else None,
            }

    @router.get("/player-stats")
    def get_player_stats(
        sort_by: Literal["goals", "assists", "rating"] = "goals",
        club_id: int | None = None,
        min_matches: int = Query(default=1, ge=1),
        position: str | None = None,
        element: str | None = None,
        season_no: int | None = None,
        career: Career = Depends(get_career)):
        with career.lock:
            if club_id is not None and club_id not in career.season.teams:
                raise HTTPException(status_code=404, detail="Kulüp bulunamadı.")

            player_elements = None
            if element:
                player_elements = {
                    player_id: player["element"]
                    for team in career.season.teams.values()
                    for player_id, player in team["players"].items()
                }

            _, completed_matches = season_games(career, season_no)
            rows = summarize_player_stats(
                completed_matches,
                sort_by=sort_by,
                club_id=club_id,
                min_matches=min_matches,
                position=position,
                element=element,
                player_elements=player_elements,
            )
            return named_players(rows, player_names(career.season.teams))

    @router.get("/lineup")
    def get_user_lineup(career: Career = Depends(get_career)):
        with career.lock:
            team = career.season.teams[DEMO_USER_CLUB_ID]

            return {
                "club_id": DEMO_USER_CLUB_ID,
                "season_no": career.season_no,
                "next_week": career.season.next_week,
                "finished": career.season.finished,
                "players": [
                    {"player_id": player_id, **player}
                    for player_id, player in team["players"].items()
                ],
                "formation_slots": [
                    {"slot_id": slot_id, "position": position}
                    for slot_id, position in team["formation_slots"].items()
                ],
                "selections": team["selections"],
                "power": calculate_team_power(
                    team["players"],
                    team["formation_slots"],
                    team["selections"],
                    career.season.bonus_rules,
                ),
                "formation": team["formation"],
            }

    @writes.put("/lineup")
    def save_user_lineup(request: SaveLineupRequest, career: Career = Depends(get_career),
        edit=Depends(get_editor),
    ):
        with edit(career) as career:
            if career.season.finished:
                raise HTTPException(status_code=409, detail="Sezon tamamlandı.")

            if (request.expected_season, request.expected_week) != (career.season_no, career.season.next_week):
                raise HTTPException(
                    status_code=409,
                    detail={
                        "message": "Ekrandaki sezon veya hafta güncel değil.",
                        "season_no": career.season_no,
                        "next_week": career.season.next_week,
                    },
                )

            team = career.season.teams[DEMO_USER_CLUB_ID]
            name = team["formation"] if request.formation is None else request.formation

            if name not in DEMO_FORMATIONS:
                raise HTTPException(status_code=422, detail="Bilinmeyen formasyon.")

            new_slots = formation_slots(name)
            selections = [
                {"slot_id": item.slot_id, "player_id": item.player_id}
                for item in request.selections
            ]

            power = calculate_team_power(
                team["players"],
                new_slots,
                selections,
                career.season.bonus_rules,
            )

            if not power["valid"]:
                raise HTTPException(status_code=422, detail=power["errors"])

            team.update({
                "formation": name,
                "formation_slots": new_slots,
                "selections": selections,
            })

            return {
                "club_id": DEMO_USER_CLUB_ID,
                "season_no": career.season_no,
                "next_week": career.season.next_week,
                "formation": name,
                "selections": selections,
                "power": power,
            }

    @router.get("/formations")
    def get_formations(_career: Career = Depends(get_career)):
        return [
            {
                "name": name,
                "slots": [
                    {"slot_id": slot_id, "position": position}
                    for slot_id, position in formation_slots(name).items()
                ],
            }
            for name in DEMO_FORMATIONS
        ]

    @router.get("/formation-stats")
    def get_formation_stats(club_id: int = DEMO_USER_CLUB_ID, career: Career = Depends(get_career)):
        with career.lock:
            if club_id not in career.season.teams:
                raise HTTPException(status_code=404, detail="Kulüp bulunamadı.")

            return summarize_formation_stats(career.season.completed_matches, club_id)

    @router.get("/transfer-market")
    def get_transfer_market(
        position: str | None = None,
        element: str | None = None,
        min_value: int | None = Query(default=None, ge=0),
        max_value: int | None = Query(default=None, ge=0),
        career: Career = Depends(get_career)):
        with career.lock:
            try:
                return list_market_players(
                    career.season.teams,
                    DEMO_USER_CLUB_ID,
                    position=position,
                    element=element,
                    min_value=min_value,
                    max_value=max_value,
                )
            except ValueError as error:
                raise HTTPException(status_code=422, detail=str(error)) from error

    @router.get("/transfer-offers")
    def get_transfer_offers(career: Career = Depends(get_career)):
        with career.lock:
            return career.offers.list_for_buyer(DEMO_USER_CLUB_ID)

    @writes.post("/transfer-offers", status_code=201)
    def create_transfer_offer(request: CreateOfferRequest, career: Career = Depends(get_career),
        edit=Depends(get_editor),
    ):
        with edit(career) as career:
            if career.season.finished:
                raise HTTPException(status_code=409, detail="Sezon tamamlandı.")

            if (request.expected_season, request.expected_week) != (career.season_no, career.season.next_week):
                raise HTTPException(
                    status_code=409,
                    detail={
                        "message": "Ekrandaki sezon veya hafta güncel değil.",
                        "season_no": career.season_no,
                        "next_week": career.season.next_week,
                    },
                )

            try:
                return career.offers.create(
                    career.season.teams,
                    DEMO_USER_CLUB_ID,
                    request.player_id,
                    request.amount,
                    career.season.next_week,
                )
            except KeyError as error:
                raise HTTPException(status_code=404, detail=error.args[0]) from error
            except OfferConflict as error:
                raise HTTPException(status_code=409, detail=str(error)) from error

    @writes.post("/transfer-offers/{offer_id}/cancel")
    def cancel_transfer_offer(offer_id: int, career: Career = Depends(get_career),
        edit=Depends(get_editor),
    ):
        with edit(career) as career:
            try:
                return career.offers.cancel(offer_id, DEMO_USER_CLUB_ID)
            except KeyError as error:
                raise HTTPException(status_code=404, detail=error.args[0]) from error
            except OfferConflict as error:
                raise HTTPException(status_code=409, detail=str(error)) from error

    @writes.post("/transfer-offers/{offer_id}/resolve")
    def resolve_transfer_offer(offer_id: int, career: Career = Depends(get_career),
        edit=Depends(get_editor),
    ):
        with edit(career) as career:
            if career.season.finished:
                raise HTTPException(status_code=409, detail="Sezon tamamlandı.")

            try:
                return career.offers.resolve(
                    career.season.teams,
                    offer_id,
                    DEMO_USER_CLUB_ID,
                    career.season.next_week,
                    season_no=career.season_no,
                )
            except KeyError as error:
                raise HTTPException(status_code=404, detail=error.args[0]) from error
            except OfferConflict as error:
                raise HTTPException(status_code=409, detail=str(error)) from error

    @router.get("/transfers")
    def get_user_transfers(career: Career = Depends(get_career)):
        with career.lock:
            club_id = DEMO_USER_CLUB_ID
            history = [
                row.copy()
                for row in reversed(career.offers.transfers)
                if club_id in (row["from_club_id"], row["to_club_id"])
            ]
            return {
                "club_id": club_id,
                "budget": career.season.teams[club_id]["budget"],
                "transfers": history,
            }

    @router.get("/finance")
    def get_user_finance(career: Career = Depends(get_career)):
        with career.lock:
            club_id = DEMO_USER_CLUB_ID
            return transfer_finance_summary(
                club_id,
                career.season.teams[club_id]["budget"],
                career.offers.transfers,
            )

    @writes.post("/new-season")
    def start_new_season(
        request: NewSeasonRequest,
        career: Career = Depends(get_career),
        edit=Depends(get_editor),
    ):
        with edit(career) as career:
            return career.start_next_season(request.expected_season)

    @router.get("/history/{season_no}")
    def get_finished_season(
        season_no: int,
        career: Career = Depends(get_career),
    ):
        with career.lock:
            if season_no not in career.history:
                raise HTTPException(404, "Arşivde bu sezon bulunamadı.")
            return career.history[season_no]

    router.include_router(sql_writes() if sql else writes)
    return router


def sql_writes():
    routes = APIRouter()

    @routes.post("/advance")
    def advance(request: AdvanceWeekRequest, uid=Depends(sql_api.sql_user_id)):
        return sql_api.run(sql_api.advance_sql_week, uid, request.expected_season, request.expected_week)

    @routes.put("/lineup")
    def save_lineup(request: SaveLineupRequest, uid=Depends(sql_api.sql_user_id)):
        picks = [{"slot_id": s.slot_id, "player_id": s.player_id} for s in request.selections]
        return sql_api.run(sql_api.save_sql_lineup, uid, picks, request.expected_season,
                           request.expected_week, request.formation)

    @routes.post("/transfer-offers", status_code=201)
    def create_offer(request: CreateOfferRequest, uid=Depends(sql_api.sql_user_id)):
        return sql_api.run(sql_api.create_sql_offer, uid, request.player_id, request.amount,
                           request.expected_season, request.expected_week)

    @routes.post("/transfer-offers/{offer_id}/cancel")
    def cancel(offer_id: int, uid=Depends(sql_api.sql_user_id)):
        return sql_api.run(sql_api.cancel_sql_offer, uid, offer_id)

    @routes.post("/transfer-offers/{offer_id}/resolve")
    def resolve(offer_id: int, uid=Depends(sql_api.sql_user_id)):
        return sql_api.run(sql_api.resolve_sql_offer, uid, offer_id)

    @routes.post("/new-season")
    def start(request: NewSeasonRequest, uid=Depends(sql_api.sql_user_id)):
        return sql_api.run(sql_api.start_sql_season, uid, request.expected_season)

    return routes


router = make_season_router("/demo/season", "Demo sezonu", get_demo_career, demo_editor)
use_sql = sql_api.postgres_enabled()
active_career = sql_api.read_sql_career if use_sql else get_user_career
career_router = make_season_router("/career/season", "Kariyer", active_career, user_editor, sql=use_sql)
