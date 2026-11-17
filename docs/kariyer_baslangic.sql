-- PostgreSQL sözleşmesi. Önkoşul: public.user_account(user_id) PK.
-- Kariyerin anahtarı, sahibi olan hesabın kimliğidir (hesap başına tek kariyer).
CREATE TABLE public.career (
    career_id BIGINT PRIMARY KEY REFERENCES public.user_account(user_id),
    managed_club_id INTEGER NOT NULL,
    season_no INTEGER NOT NULL CHECK (season_no > 0),
    rng_state TEXT NOT NULL
);
CREATE TABLE public.club (
    career_id BIGINT REFERENCES public.career ON DELETE CASCADE,
    club_id INTEGER,
    name TEXT,
    budget BIGINT NOT NULL CHECK (budget >= 0),
    formation TEXT NOT NULL,
    PRIMARY KEY (career_id, club_id),
    UNIQUE (career_id, name)
);
CREATE TABLE public.player (
    career_id BIGINT, player_id INTEGER, club_id INTEGER NOT NULL,
    first_name TEXT NOT NULL, last_name TEXT NOT NULL,
    age INTEGER NOT NULL CHECK (age >= 0), primary_position TEXT NOT NULL,
    element TEXT CHECK (element IN ('Fire', 'Earth', 'Air', 'Water')),
    market_value BIGINT NOT NULL CHECK (market_value >= 0),
    defending INTEGER NOT NULL CHECK (defending BETWEEN 0 AND 100),
    strength INTEGER NOT NULL CHECK (strength BETWEEN 0 AND 100),
    stamina INTEGER NOT NULL CHECK (stamina BETWEEN 0 AND 100),
    passing INTEGER NOT NULL CHECK (passing BETWEEN 0 AND 100),
    dribbling INTEGER NOT NULL CHECK (dribbling BETWEEN 0 AND 100),
    shooting INTEGER NOT NULL CHECK (shooting BETWEEN 0 AND 100),
    pace INTEGER NOT NULL CHECK (pace BETWEEN 0 AND 100),
    PRIMARY KEY (career_id, player_id),
    FOREIGN KEY (career_id, club_id) REFERENCES public.club ON DELETE CASCADE
);
CREATE TABLE public.player_position (
    career_id BIGINT, player_id INTEGER, position TEXT,
    compatibility INTEGER NOT NULL CHECK (compatibility BETWEEN 1 AND 100),
    PRIMARY KEY (career_id, player_id, position),
    FOREIGN KEY (career_id, player_id) REFERENCES public.player ON DELETE CASCADE
);
CREATE TABLE public.lineup_selection (
    career_id BIGINT, club_id INTEGER, slot_id INTEGER CHECK (slot_id BETWEEN 1 AND 11),
    position TEXT NOT NULL, player_id INTEGER NOT NULL,
    PRIMARY KEY (career_id, club_id, slot_id),
    UNIQUE (career_id, player_id),
    FOREIGN KEY (career_id, club_id) REFERENCES public.club ON DELETE CASCADE,
    FOREIGN KEY (career_id, player_id) REFERENCES public.player ON DELETE CASCADE
);
CREATE TABLE public.season (
    career_id BIGINT REFERENCES public.career ON DELETE CASCADE, season_no INTEGER,
    next_week INTEGER CHECK (next_week > 0), last_week INTEGER NOT NULL CHECK (last_week > 0),
    PRIMARY KEY (career_id, season_no)
);
CREATE TABLE public.fixture (
    career_id BIGINT, season_no INTEGER, match_id INTEGER,
    week_no INTEGER NOT NULL CHECK (week_no > 0),
    home_club_id INTEGER NOT NULL, away_club_id INTEGER NOT NULL,
    PRIMARY KEY (career_id, season_no, match_id),
    CHECK (home_club_id <> away_club_id),
    FOREIGN KEY (career_id, season_no) REFERENCES public.season ON DELETE CASCADE,
    FOREIGN KEY (career_id, home_club_id) REFERENCES public.club,
    FOREIGN KEY (career_id, away_club_id) REFERENCES public.club
);
CREATE TABLE public.career_bonus_rule (
    career_id BIGINT REFERENCES public.career ON DELETE CASCADE,
    element TEXT, required_count INTEGER CHECK (required_count BETWEEN 1 AND 11),
    defense_bonus_pct INTEGER NOT NULL, midfield_bonus_pct INTEGER NOT NULL,
    attack_bonus_pct INTEGER NOT NULL,
    PRIMARY KEY (career_id, element, required_count)
);
