#!/usr/bin/env

"""
Process queued orders to get ord wallet addresses assigned and
calculate the total mint costs with inscription fees included.
FCFS.
"""

from time import sleep

from api.lib.ord import Ord
from api.lib.mint import Mint
from api.models import Order, Inscription


def process_orders() -> bool:
    ord = Ord()

    # generate addresses for queued orders
    for order in Order.select().where(Order.ord_address == None).order_by(Order.create_date.asc()).limit(30):
        ord.generate_address(order)

    # check transactions for orders
    for order in Order.select().where(Order.completed == False, Order.tx_id != None).order_by(Order.create_date.asc()).limit(20):
        ord.confirm_payment(order)

    # check for inscriptions to be sent
    inscriptions = Inscription.select().where(Inscription.tx_id == None).order_by(Inscription.create_date.asc()).limit(5)
    for inscription_id in [i.id for i in inscriptions]:
        ord.inscribe_image(inscription_id)

if __name__ == '__main__':
    while True:
        if Mint().show()["minted_out"]:
            print("supply minted out!")
            exit()
        process_orders()
        sleep(1)
