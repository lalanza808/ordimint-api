from datetime import datetime, timezone
from decimal import Decimal

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def log(text, color=bcolors.WARNING):
    now = datetime.now(timezone.utc)
    print(f'{color}[{now.isoformat()}] {text}{bcolors.ENDC}')

def to_sats(btc):
    return int(Decimal(str(btc)) * 10**8)
