import json
import unittest
from contextlib import closing, contextmanager
from pathlib import Path
import asyncio
from urllib.parse import urlsplit
from unittest.mock import patch

from fastapi import FastAPI
from backend import season_api as api, sql_api, club_profile
import test_postgres_career_load as block3


async def request(app, method, url, body=None):
    path = urlsplit(url)
    messages = []
    async def receive():
        return {"type": "http.request", "body": json.dumps(body).encode(), "more_body": False}
    async def send(message):
        messages.append(message)
    await app({"type": "http", "asgi": {"version": "3.0"}, "http_version": "1.1",
               "scheme": "http", "method": method, "path": path.path,
               "query_string": path.query.encode(), "root_path": "",
               "headers": [(b"content-type", b"application/json")], "server": ("test", 80),
               "client": ("test", 1)}, receive, send)
    return messages[0]["status"], json.loads(b"".join(m.get("body", b"") for m in messages))


class ApiModeTests(unittest.TestCase):
    def exercise(self, sql):
        app = FastAPI()
        reader = sql_api.read_sql_career if sql else api.get_user_career
        app.include_router(api.make_season_router("/career/season", "Kariyer", reader,
                                                  api.user_editor, sql=sql))
        # Kulüp router'ının başlangıç anındaki mod seçimini de sınar.
        from importlib import reload
        with patch.object(api, "active_career", reader), patch.object(api, "use_sql", sql):
            app.include_router(reload(club_profile).router)
        reload(club_profile)
        self.enterContext(patch.object(api, "user_careers", {}))
        self.enterContext(patch.object(api, "career_store", api.MemoryCareerStore()))
        user = {"user_id": 1}
        app.dependency_overrides[api.current_user] = lambda: user

        def call(method, path, data=None, status=200):
            code, result = asyncio.run(request(app, method, "/career/" + path, data))
            self.assertEqual(code, status, result)
            return result

        call("PUT", "club", {"name": "Ankara Yıldızları"})
        self.assertEqual(call("GET", "club")["name"], "Ankara Yıldızları")
        k = call("GET", "season/lineup")
        stamp = {"expected_week": 1, "expected_season": 1}
        call("PUT", "season/lineup", dict(stamp, selections=k["selections"]))
        data = dict(stamp, player_id=2011, amount=400000)
        offer = call("POST", "season/transfer-offers", data, 201)
        call("POST", f"season/transfer-offers/{offer['offer_id']}/cancel")
        offer = call("POST", "season/transfer-offers", data, 201)
        call("POST", f"season/transfer-offers/{offer['offer_id']}/resolve")
        self.assertEqual(call("GET", "season/finance")["budget"], 1600000)
        self.assertEqual(len(call("GET", "season/transfers")["transfers"]), 1)
        for week in range(1, 7):
            call("POST", "season/advance", dict(stamp, expected_week=week))
        call("POST", "season/advance", stamp, status=409)
        first = call("GET", "season/matches/1?event_type=GOAL")
        table = call("GET", "season/player-stats?sort_by=rating")
        call("POST", "season/new-season", {"expected_season": 1})
        self.assertEqual(call("GET", "season/matches/1?season_no=1&event_type=GOAL"), first)
        self.assertEqual(call("GET", "season/player-stats?season_no=1&sort_by=rating"), table)
        self.assertEqual(len(call("GET", "season/history/1")["matches"]), 12)
        self.assertEqual(call("GET", "season/matches/1")["status"], "scheduled")
        user["user_id"] = 2
        self.assertEqual(call("GET", "season")["budget"], 2000000)
        call("GET", "season/history/1", status=404)

    def test_memory_http(self):
        self.exercise(False)

    def test_sql_http(self):
        fixture = block3.CareerLoadTests()
        self.addCleanup(fixture.doCleanups)
        fixture.setUp()
        with closing(fixture.connect()) as db:
            for filename in ("hafta_kaydi.sql", "transfer_kaydi.sql"):
                ddl = (Path(__file__).parent / "docs" / filename).read_text(encoding="utf-8")
                db.executescript(ddl.replace("REFERENCES public.", "REFERENCES ")
                                 .replace("ON public.transfer_offer\n", "ON transfer_offer\n")
                                 .replace("INDEX transfer_one_pending", "INDEX public.transfer_one_pending"))
        @contextmanager
        def sqlite_snapshot():
            with closing(fixture.connect()) as db, closing(db.cursor()) as cur:
                cur.execute("BEGIN")
                yield cur
        with patch.object(sql_api, "connect", fixture.connect), patch.object(sql_api, "snapshot", sqlite_snapshot):
            self.exercise(True)
