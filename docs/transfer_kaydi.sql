CREATE TABLE public.transfer_offer (
    career_id BIGINT NOT NULL, offer_id INTEGER NOT NULL,
    buyer_club_id INTEGER NOT NULL, seller_club_id INTEGER NOT NULL,
    player_id INTEGER NOT NULL, amount BIGINT NOT NULL CHECK (amount > 0),
    created_season INTEGER NOT NULL, created_week INTEGER NOT NULL CHECK (created_week > 0),
    status TEXT NOT NULL CHECK (status IN ('PENDING','CANCELLED','REJECTED','ACCEPTED')),
    reason TEXT, resolved_week INTEGER,
    PRIMARY KEY (career_id,offer_id),
    CHECK (buyer_club_id <> seller_club_id),
    FOREIGN KEY (career_id,buyer_club_id) REFERENCES public.club,
    FOREIGN KEY (career_id,seller_club_id) REFERENCES public.club,
    FOREIGN KEY (career_id,player_id) REFERENCES public.player,
    FOREIGN KEY (career_id,created_season) REFERENCES public.season
);
CREATE UNIQUE INDEX transfer_one_pending ON public.transfer_offer
    (career_id,buyer_club_id,player_id) WHERE status='PENDING';

CREATE TABLE public.transfer (
    career_id BIGINT NOT NULL, transfer_no INTEGER NOT NULL, offer_id INTEGER NOT NULL,
    season_no INTEGER NOT NULL, week_no INTEGER NOT NULL CHECK (week_no > 0),
    PRIMARY KEY (career_id,transfer_no), UNIQUE (career_id,offer_id),
    FOREIGN KEY (career_id,offer_id) REFERENCES public.transfer_offer,
    FOREIGN KEY (career_id,season_no) REFERENCES public.season
);
