import subprocess
import json

from api.models import Order, Inscription, TxStatus
from api.helpers import bcolors, log, to_sats
from api.config import secrets
from api.lib.mint import Mint


class Ord(object):
    """
    Commands for using bitcoin-cli and ord cli to interact
    with ord server and bitcoind. Performs the order queueing,
    transaction confirming, address generation, and inscribing.
    """
    def __init__(self):
        chain = secrets["CHAIN"]
        self.mint_sats = int(secrets["MINT_SATS"])
        self.postage = int(secrets["POSTAGE"])
        self.supply_len = len(secrets["TOTAL_SUPPLY"])
        self.image_path = secrets["IMAGE_PATH"]
        self.inscribe_sats = int(secrets["INSCRIBE_SATS"])
        if chain == "mainnet":
            self.ord = "ord"
            self.btccli = "bitcoin-cli -chain=main -rpcwallet=ord"
        elif chain == "regtest":
            self.ord = "ord -r"
            self.btccli = "bitcoin-cli -chain=regtest -rpcwallet=ord"
        elif chain == "testnet":
            self.ord = "ord -t"
            self.btccli = "bitcoin-cli -chain=testnet -rpcwallet=ord"
        else:
            raise Exception(f"CHAIN must be mainnet, regtest, or testnet, you specified \"{chain}\"")

    def queue_order(self, address: str, amount: int, fee: int) -> Order:
        """
        Create an open order in the database without an address. This queues it
        to be assigned a unique ord wallet to receive funds for and the total
        sats expected to receive, after which users can send funds to the
        address to claim an inscription FCFS.
        """
        if Mint().show()["minted_out"]:
            log("Unable to queue new order, minted out", bcolors.FAIL)
            return
        mm = int(secrets["MAX_MINT"])
        if amount > mm:
            amount = mm
        order = Order.create(
            receiver_address=address,
            sats_for_mint=amount * self.mint_sats,
            sats_for_fees=amount * (self.inscribe_sats + self.postage) * fee,
            amount_minting=amount,
            fee=fee
        )
        log(f"Queued order {order.id}: {order.show()}")
        return order

    def generate_address(self, order: Order):
        """
        Given a queued order create a new ord wallet address and assign it.
        """
        res = subprocess.run(f"{self.ord} wallet receive".split(), capture_output=True)
        if res.stderr:
            log(f"Error with ord cli: {res.stderr}", bcolors.FAIL)
            return order
        else:
            try:
                data = json.loads(res.stdout)
                order.ord_address = data["addresses"][0]
                order.save()
                log(f"Generated ord address {order.ord_address} for order {order.id}")
                return True
            except Exception as e:
                log(f"Error unmarshalling JSON: {e}", bcolors.FAIL)
                log(res, bcolors.FAIL)
                return False

    def confirm_payment(self, order: Order):
        """
        Confirm a given payment has beeen made against an order
        and create (an) Inscription object(s).
        """
        res = subprocess.run(f"{self.btccli} gettransaction {order.tx_id}".split(), capture_output=True)
        if res.stderr:
            log(f"[!] Error with bitcoin-cli: {res.stderr}", bcolors.FAIL)
        else:
            try:
                data = json.loads(res.stdout)
                sent_sats = to_sats(data["amount"])
                received_address = data["details"][0]["address"]
                confirmations = data["confirmations"]
                expecting_sats = order.sats_for_mint + order.sats_for_fees
                log(f"Found payment of {data["amount"]} BTC ({sent_sats} sats) for order {order.id} in tx id {order.tx_id}. Expecting {expecting_sats} sats. Confirming correctness.")

                correct_address = received_address == order.ord_address
                correct_sats = sent_sats >= expecting_sats
                correct_confirmations = confirmations >= 1

                if correct_address and correct_sats and correct_confirmations:
                    log(f"Successful payment for order {order.id}!", bcolors.OKGREEN)
                    order.completed = True
                    order.tx_status = TxStatus.CONFIRMED.value
                    order.save()

                    log(f"Creating {order.amount_minting} inscriptions for order {order.id}")
                    for _ in range(order.amount_minting):
                        Inscription.create(
                            order=order.id
                        )
                else:
                    log(f"No payment yet for order {order.id}", bcolors.FAIL)

                return True
            except Exception as e:
                log(f"Error unmarshalling JSON: {e}", bcolors.FAIL)
                log(res)
                return False

    def inscribe_image(self, inscription_id: str):
      """
      Inscribe images for the given inscription. Increment based on last inscribed
      numerical ID.
      """
      inscription = Inscription.get(id=inscription_id)
      order = inscription.order
      latest_token = Inscription.select().order_by(Inscription.token_id.desc()).first()
      next_token = latest_token.token_id + 1
      token_id = f"{next_token:0{self.supply_len}d}"
      path = f"/home/lance/Downloads/corpses/public/images/{token_id}.png"
      if Mint().show()["minted_out"]:
          log("Cannot inscribe, supply is minted!", bcolors.FAIL)
          return
      log(f"Attempting to inscribe {inscription_id} at {path}")
      res = subprocess.run(f"{self.ord} wallet inscribe --fee-rate {order.fee} --file {path} --postage {self.postage}sat --destination {order.receiver_address}".split(), capture_output=True)
      if res.stderr:
          log(f"Error with ord cli: {res.stderr}", bcolors.FAIL)
      else:
          try:
              data = json.loads(res.stdout)
              cost = str(data["total_fees"])
              inscription.tx_id = data["reveal"]
              inscription.tx_status = TxStatus.PENDING.value
              inscription.completed = True
              inscription.total_fees = cost
              inscription.token_id = next_token
              inscription.save()
              log(f"Sent inscription {token_id} ({inscription_id}) for order {order.id} to {order.receiver_address} for {cost} sats, user sent {order.sats_for_fees}", bcolors.OKGREEN)
          except Exception as e:
              log(f"{res}: {e}", bcolors.FAIL)
