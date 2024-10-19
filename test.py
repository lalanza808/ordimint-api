#!/usr/bin/env

"""
Generate orders and send transactions to simulate
minting experience on regtest.
"""

import json
import subprocess
from time import sleep
from random import randrange

from api.models import Order
from api.lib.ord import Ord


ord_address = json.loads(subprocess.run("ord -r wallet receive".split(), capture_output=True).stdout)["addresses"][0]


for i in range(200):
    Ord().queue_order(
        address=ord_address,
        amount=randrange(1,2),
        fee=randrange(10,50)
    )

while Order.select().where(Order.ord_address == None):
    sleep(2)

for order in Order.select().where(Order.ord_address != None, Order.tx_id == None):
    while True:
        tx_id = subprocess.check_output(f"bitcoin-cli -regtest -rpcwallet=test sendtoaddress {order.ord_address} {str(order.total_as_btc())}".split(), timeout=10)
        if tx_id:
            print(f"Sent {order.total_as_btc()} btc to {order.ord_address} in tx {tx_id}")
            order.tx_id = tx_id
            order.save()
            break
    subprocess.run("bitcoin-cli -regtest -rpcwallet=test -generate 1".split(), stdout=subprocess.DEVNULL)
    sleep(1)

while True:
    subprocess.run("bitcoin-cli -regtest -rpcwallet=test -generate 1".split(), stdout=subprocess.DEVNULL)
    sleep(5)