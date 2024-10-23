#!/usr/bin/env

"""
Summarize the mint details and sent and received Bitcoin.
"""

import json
import subprocess
from decimal import Decimal

from api.lib.mint import Mint
from api.models import Order, Inscription


received_sats = 0
expected_sats = 0
spent_sats = 0
balance = 0

def from_atomic(sats):
    satoshi = Decimal('0.00000001')
    return (Decimal(str(sats)) * satoshi).quantize(satoshi)

for order in Order.select().where(Order.completed == True):
    expected_sats += order.sats_for_mint
    received_sats += (order.sats_for_mint + order.sats_for_fees)

for inscription in Inscription.select().where(Inscription.completed == True):
    spent_sats += inscription.total_fees

try:
    balance = subprocess.run(f"ord -r wallet balance".split(), capture_output=True, timeout=10)
    cardinal = json.loads(balance.stdout)["cardinal"]
    mint = Mint().show()
    print(f"Price {mint['price']} sats")
    print(f"Inscribe Sats {mint['inscribe_sats']} sats")
    print(f"Postage {mint['postage']} sats")
    print(f"Supply {mint['supply']}/{mint['total_supply']}")
    print(f"Expecting to make {from_atomic(expected_sats)} btc from sales.\nReceived {from_atomic(received_sats)} btc so far.\nSpent {from_atomic(spent_sats)} btc on inscription fees.\nCurrent balance is {from_atomic(cardinal)} btc")
except:
    pass


