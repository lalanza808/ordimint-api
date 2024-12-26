from api.models import Inscription
from api.config import secrets


class Mint(object):
    """
    Summary information about the mint. Used for diagnostics
    and for informing the frontend about mint details.
    """
    def __init__(self):
        pass

    def show(self):
        supply = len(Inscription.select().where(
            Inscription.completed == True  # noqa: E712
        ))
        pending = len(Inscription.select().where(
            Inscription.completed == False  # noqa: E712
        ))
        ids = Inscription.select().where(
            Inscription.completed == True
        ).order_by(Inscription.create_date.asc())
        return {
            "price": int(secrets["MINT_SATS"]),
            "total_supply": int(secrets["TOTAL_SUPPLY"]),
            "supply": supply,
            "minted_out": supply >= int(secrets["TOTAL_SUPPLY"]),
            "max_mint": int(secrets["MAX_MINT"]),
            "pending": pending,
            "chain": secrets["CHAIN"],
            "inscribe_sats": secrets["INSCRIBE_SATS"],
            "postage": secrets["POSTAGE"],
            "inscriptions": [f"{i.tx_id}:0" for i in ids]
        }
