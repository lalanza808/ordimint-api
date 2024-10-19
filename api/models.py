from enum import Enum
from uuid import uuid4
from decimal import Decimal
from datetime import datetime, timezone

from playhouse.sqliteq import SqliteQueueDatabase
from peewee import Model, CharField, DateTimeField
from peewee import ForeignKeyField, IntegerField, BooleanField


db = SqliteQueueDatabase("data/db.sqlite")

def gen_uuid():
    return str(uuid4())

def get_now():
    return datetime.now(timezone.utc)

class TxStatus(Enum):
    WAITING = "waiting"
    PENDING = "pending"
    CONFIRMED = "confirmed"

class Order(Model):
    id = CharField(default=gen_uuid, primary_key=True)
    create_date = DateTimeField(default=get_now)
    receiver_address = CharField()
    amount_minting = IntegerField()
    fee = IntegerField()

    # calculated based on amount specified
    sats_for_mint = IntegerField()

    # generated after creation by ord cli
    ord_address = CharField(null=True)
    sats_for_fees = IntegerField(null=True)

    # updated after the fact on interval of checking mempool
    tx_status = CharField(default=TxStatus.WAITING.value)
    tx_id = CharField(null=True)
    completed = BooleanField(default=False)

    class Meta:
        database = db

    def total_as_btc(self):
        satoshi = Decimal('0.00000001')
        return (Decimal(self.sats_for_mint + self.sats_for_fees) * satoshi).quantize(satoshi)

    def get_inscriptions(self):
        return Inscription.select().where(Inscription.order == self.id)

    def show(self):
        return self.__dict__["__data__"]


class Inscription(Model):
    id = CharField(default=gen_uuid, primary_key=True)
    token_id = IntegerField(default=0)
    create_date = DateTimeField(default=get_now)
    order = ForeignKeyField(Order)
    tx_id = CharField(null=True)
    tx_status = CharField(default=TxStatus.WAITING.value)
    completed = BooleanField(default=False)
    total_fees = IntegerField(null=True)

    def show(self):
        return self.__dict__["__data__"]

    class Meta:
        database = db


db.create_tables([Order, Inscription])