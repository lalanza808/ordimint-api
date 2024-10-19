from pydantic import BaseModel
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from api.models import Order, Inscription
from api.lib.ord import Ord
from api.lib.mint import Mint
from api.lib.mempool import Mempool


app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class CreateOrder(BaseModel):
    amount: int = 1
    address: str
    fee: int

class UpdateOrder(BaseModel):
    order_id: str
    tx_id: str


@app.get("/fees")
def fees():
    return Mempool().get_fees()

@app.post("/create", status_code=201)
def create(order: CreateOrder):
    """
    Create an order in the queue.
    """
    if Mint().show()["minted_out"]:
        return HTTPException(status_code=400, detail="Supply is minted out. Unable to queue new orders.")
    order = Ord().queue_order(
        address=order.address,
        amount=order.amount,
        fee=order.fee
    )
    return {"order_id": order.id}

@app.post("/update")
def update(update: UpdateOrder):
    """
    Update an order with a sent transaction ID.
    """
    order = Order.get(id=update.order_id)
    if order:
        order.tx_id = update.tx_id
        order.save()
        return order.show()
    else:
        return {}

@app.get("/status")
def state():
    """
    Return the overall status of the mint such as minted supply.
    """
    return Mint().show()

@app.get("/orders/{address}")
def orders(address: str):
    """
    Retrieve orders for a given wallet address.
    """
    orders = Order.select().where(Order.receiver_address == address)
    return {"orders": [order.show() for order in orders]}

@app.get("/inscriptions/{address}")
def inscriptions(address: str):
    """
    Get the inscriptions for a given address.
    """
    inscriptions = Inscription.select(
        Inscription, Order
    ).join(Order).where(
        Order.receiver_address == address
    )
    return {"inscriptions": [i.show() for i in inscriptions]}

@app.get("/debug")
def metrics(address: str = None):
    """
    Return all data entered into the database.
    """
    all_orders = Order.select()
    all_inscriptions = Inscription.select()
    if address:
        all_orders = all_orders.where(Order.receiver_address == address)
    res = {
        "wallets": {},
        "totals": {
            "orders": len(all_orders),
            "inscriptions": len(all_inscriptions)
        }
    }
    for order in all_orders:
        if order.receiver_address not in res["wallets"]:
            res["wallets"][order.receiver_address] = {
                "orders": [],
                "inscriptions": []
            }
        res["wallets"][order.receiver_address]["orders"].append(order.show())
    for address in res["wallets"]:
        address_inscriptions = Inscription.select(
            Inscription, Order
        ).join(Order).where(
            Order.receiver_address == address
        )
        res["wallets"][address]["inscriptions"] = [i.show() for i in address_inscriptions]
    return res
