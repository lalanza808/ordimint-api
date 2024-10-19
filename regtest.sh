#!/bin/bash

set -x

echo -e "Restarting bitcoind and ord server..."
pkill -ef "bitcoind -regtest"
pkill -ef "ord -r"
sleep 2
rm -rf ~/.local/share/ord/regtest
rm -rf ~/.bitcoin/regtest/
bitcoind -regtest -daemon -fallbackfee=0.00000001
sleep 5
ord -r wallet create
bitcoin-cli -regtest createwallet test
bitcoin-cli -regtest -rpcwallet=test -generate 101 > /dev/null
ord -r server --http-port 8080 &
