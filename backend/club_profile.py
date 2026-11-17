from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from backend.season_api import DEMO_USER_CLUB_ID, active_career, user_editor, use_sql
from backend import sql_api

router = APIRouter(prefix="/career", tags=["Kulüp"])


class ClubName(BaseModel):
    name: str = Field(min_length=1, max_length=60)


def club_profile(career):
    teams = career.season.teams
    return {
        "club_id": DEMO_USER_CLUB_ID,
        "name": teams[DEMO_USER_CLUB_ID].get("name"),
        "clubs": [{"club_id": key, "name": team.get("name")} for key, team in teams.items()],
    }


@router.get("/club")
def get_club(career=Depends(active_career)):
    with career.lock:
        return club_profile(career)


def name_club(request: ClubName, career=Depends(active_career), edit=Depends(user_editor)):
    name = " ".join(request.name.split())
    if not name:
        raise HTTPException(422, "Kulüp adı boş olamaz.")
    with edit(career) as working:
        teams = working.season.teams
        team = teams[DEMO_USER_CLUB_ID]
        if team.get("name") and team["name"] != name:
            raise HTTPException(409, "Kulübün adı zaten seçilmiş.")
        if any(key != DEMO_USER_CLUB_ID and (other.get("name") or "").casefold() == name.casefold()
               for key, other in teams.items()):
            raise HTTPException(409, "Bu kulüp adı ligde kullanılıyor.")
        team["name"] = name
        return club_profile(working)

def name_club_sql(request: ClubName, uid=Depends(sql_api.sql_user_id)):
    return sql_api.run(sql_api.name_sql_club, uid, request.name)


router.put("/club")(name_club_sql if use_sql else name_club)
