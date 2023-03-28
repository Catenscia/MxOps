#!/bin/bash

echo "Launching the localnet"

mxpy testnet clean
mxpy testnet config
mxpy testnet start