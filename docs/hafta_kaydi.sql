CREATE TABLE public.match_result (
    career_id BIGINT NOT NULL, season_no INTEGER NOT NULL, match_id INTEGER NOT NULL,
    home_goals INTEGER NOT NULL CHECK(home_goals>=0), away_goals INTEGER NOT NULL CHECK(away_goals>=0), home_formation TEXT NOT NULL, away_formation TEXT NOT NULL,
    PRIMARY KEY (career_id,season_no,match_id),
    FOREIGN KEY (career_id,season_no,match_id) REFERENCES public.fixture(career_id,season_no,match_id) ON DELETE CASCADE
);

CREATE TABLE public.match_lineup (
    career_id BIGINT NOT NULL, season_no INTEGER NOT NULL, match_id INTEGER NOT NULL,
    team TEXT NOT NULL, slot_id INTEGER NOT NULL, position TEXT NOT NULL, player_id INTEGER NOT NULL,
    PRIMARY KEY (career_id,season_no,match_id,team,slot_id),
    FOREIGN KEY (career_id,season_no,match_id) REFERENCES public.match_result(career_id,season_no,match_id) ON DELETE CASCADE,
    CHECK(team IN ('home','away')),
    FOREIGN KEY (career_id,player_id) REFERENCES public.player(career_id,player_id)
);

CREATE TABLE public.match_event (
    career_id BIGINT NOT NULL, season_no INTEGER NOT NULL, match_id INTEGER NOT NULL,
    sequence_no INTEGER NOT NULL, minute INTEGER NOT NULL, team TEXT NOT NULL, event_type TEXT NOT NULL, player_id INTEGER NOT NULL,
    PRIMARY KEY (career_id,season_no,match_id,sequence_no),
    FOREIGN KEY (career_id,season_no,match_id) REFERENCES public.match_result(career_id,season_no,match_id) ON DELETE CASCADE,
    CHECK(team IN ('home','away')),
    FOREIGN KEY (career_id,player_id) REFERENCES public.player(career_id,player_id)
);

CREATE TABLE public.match_player_stat (
    career_id BIGINT NOT NULL, season_no INTEGER NOT NULL, match_id INTEGER NOT NULL,
    sequence_no INTEGER NOT NULL, player_id INTEGER NOT NULL, team TEXT NOT NULL, minutes_played INTEGER NOT NULL, goals INTEGER NOT NULL, assists INTEGER NOT NULL, rating DOUBLE PRECISION,
    PRIMARY KEY (career_id,season_no,match_id,player_id),
    FOREIGN KEY (career_id,season_no,match_id) REFERENCES public.match_result(career_id,season_no,match_id) ON DELETE CASCADE,
    CHECK(team IN ('home','away')),
    FOREIGN KEY (career_id,player_id) REFERENCES public.player(career_id,player_id)
);
