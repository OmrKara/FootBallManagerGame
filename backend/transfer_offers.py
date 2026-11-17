class OfferConflict(ValueError):
    pass


class TransferOffers:
    def __init__(self):
        self.offers = {}
        self.next_id = 1
        self.transfers = []

    def create(self, teams, buyer_club_id, player_id, amount, week_no):
        if type(amount) is not int or amount <= 0:
            raise ValueError("Teklif tutarı pozitif tam sayı olmalı.")

        if player_id in teams[buyer_club_id]["players"]:
            raise OfferConflict("Kendi oyuncuna transfer teklifi veremezsin.")

        seller_club_id = next(
            (
                club_id for club_id, team in teams.items()
                if player_id in team["players"]
            ),
            None,
        )
        if seller_club_id is None:
            raise KeyError("Oyuncu bulunamadı.")

        for offer in self.offers.values():
            if (
                offer["buyer_club_id"] == buyer_club_id
                and offer["player_id"] == player_id
                and offer["status"] == "PENDING"
            ):
                raise OfferConflict("Bu oyuncu için zaten bekleyen bir teklifin var.")

        offer = {
            "offer_id": self.next_id,
            "buyer_club_id": buyer_club_id,
            "seller_club_id": seller_club_id,
            "player_id": player_id,
            "amount": amount,
            "created_week": week_no,
            "status": "PENDING",
        }

        self.offers[self.next_id] = offer
        self.next_id += 1
        return offer.copy()

    def list_for_buyer(self, buyer_club_id):
        return [
            offer.copy()
            for offer in reversed(self.offers.values())
            if offer["buyer_club_id"] == buyer_club_id
        ]

    def cancel(self, offer_id, buyer_club_id):
        offer = self.offers.get(offer_id)

        if offer is None or offer["buyer_club_id"] != buyer_club_id:
            raise KeyError("Teklif bulunamadı.")

        if offer["status"] != "PENDING":
            raise OfferConflict("Yalnızca bekleyen teklifler geri çekilebilir.")

        offer["status"] = "CANCELLED"
        return offer.copy()

    def resolve(self, teams, offer_id, buyer_club_id, week_no, *, season_no=1):
        offer = self.offers.get(offer_id)

        if offer is None or offer["buyer_club_id"] != buyer_club_id:
            raise KeyError("Teklif bulunamadı.")

        if offer["status"] != "PENDING":
            raise OfferConflict("Yalnızca bekleyen teklifler değerlendirilebilir.")

        seller = teams[offer["seller_club_id"]]
        buyer = teams[buyer_club_id]
        player_id = offer["player_id"]
        amount = offer["amount"]
        player = seller["players"].get(player_id)

        if player is None or player_id in buyer["players"]:
            raise OfferConflict("Oyuncunun kulüp bilgisi değişmiş.")

        starter_ids = {item["player_id"] for item in seller["selections"]}

        if player_id in starter_ids or amount < player["market_value"]:
            reason = (
                "Oyuncu satıcının ilk 11'inde."
                if player_id in starter_ids
                else "Teklif piyasa değerinin altında."
            )
            offer.update(status="REJECTED", reason=reason)
            return offer.copy()

        if buyer["budget"] < amount:
            raise OfferConflict("Transferi tamamlamak için bütçe yetersiz.")

        transfer = {
            "offer_id": offer_id,
            "player_id": player_id,
            "from_club_id": offer["seller_club_id"],
            "to_club_id": buyer_club_id,
            "fee": amount,
            "season_no": season_no,
            "week_no": week_no,
        }

        buyer["players"][player_id] = seller["players"].pop(player_id)
        buyer["budget"] -= amount
        seller["budget"] += amount
        self.transfers.append(transfer)
        offer.update(status="ACCEPTED", resolved_week=week_no)

        return offer.copy()