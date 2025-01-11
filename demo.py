#!/usr/bin/env

"""
Simple simulation for a demo.
"""

from time import sleep

from api.models import Order, Inscription

ord_address = ""
tx_id = ""


order = Order.select().first()
print(f"Found order {order.id}")
order.ord_address = ord_address
order.save()
input("Press enter: ")

order.tx_id = tx_id
order.save()
print("Updated tx for order")
input("Press enter: ")

order.completed = True
order.save()
sleep(5)
print("Order marked as completed")
for _ in range(order.amount_minting):
    i = Inscription.create(
        order=order.id
    )
    print(f"Inscription {i.id} created")

for i in order.get_inscriptions():
    i.tx_id = tx_id
    i.save()
    sleep(5)
    i.completed = True
    i.save()

# for order in Order.select().where(Order.ord_address != None, Order.tx_id == None):
#     while True:
#         tx_id = subprocess.check_output(f"bitcoin-cli -regtest -rpcwallet=test sendtoaddress {order.ord_address} {str(order.total_as_btc())}".split(), timeout=10)
#         if tx_id:
#             print(f"Sent {order.total_as_btc()} btc to {order.ord_address} in tx {tx_id}")
#             order.tx_id = tx_id
#             order.save()
#             break
#     subprocess.run("bitcoin-cli -regtest -rpcwallet=test -generate 1".split(), stdout=subprocess.DEVNULL)

# while True:
#     subprocess.run("bitcoin-cli -regtest -rpcwallet=test -generate 1".split(), stdout=subprocess.DEVNULL)
#     sleep(90)
