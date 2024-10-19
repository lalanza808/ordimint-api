import json

import requests
from redis import Redis

from api.config import secrets
from api.helpers import log, bcolors


redis = Redis()

class Mempool(object):
  def __init__(self):
    self.chain = secrets["CHAIN"]
    if self.chain == "mainnet":
      self.url = "https://mempool.space/api/v1"
    elif self.chain == "testnet":
      self.url = "https://mempool.space/testnet/api/v1"
    elif self.chain == "regtest":
      pass
    else:
      raise Exception(f"CHAIN must be mainnet, regtest, or testnet, you specified \"{self.chain}\"")

  def get_fees(self):
    if self.chain == "regtest":
      return {"fastestFee": 2}
    url = self.url + "/fees/recommended"
    key_name = "fees"
    data = redis.get(key_name)
    if data:
      log("cache hit", bcolors.OKGREEN)
      return json.loads(data)
    else:
      log("cache miss", bcolors.FAIL)
      try:
        res = requests.get(url)
        res.raise_for_status()
        redis.setex(
          name=key_name,
          time=600,
          value=json.dumps(res.json())
        )
        return res.json()
      except Exception as e:
        print(e)
        return {}