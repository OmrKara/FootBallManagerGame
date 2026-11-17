from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from backend.db import get_connection
from backend.season_api import router as season_router
from backend.auth import router as auth_router
from backend.season_api import career_router
from backend.club_profile import router as club_profile_router

app = FastAPI(title="Futbol Kulübü Yönetim Sistemi")
app.include_router(season_router)
app.include_router(auth_router)
app.include_router(career_router)
app.include_router(club_profile_router)

WEB_DIR = Path(__file__).resolve().parent.parent / "web"
app.mount("/static", StaticFiles(directory=WEB_DIR), name="static")

@app.get("/")
def ana_sayfa():
    return FileResponse(WEB_DIR / "index.html")

@app.get("/db-test")
def veritabani_test():
    baglanti = get_connection()
    try:
        sonuc = baglanti.cursor().execute("SELECT current_database()").fetchone()
        return {"veritabani": sonuc[0]}
    finally:
        baglanti.close()
