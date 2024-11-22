#!/bin/bash
set -e

if ! [[ " ${1} " =~ " localnet "|" devnet "|" chain-simulator " ]]; then
    echo "integration tests not available on ${1}"
    exit 0
fi

# Execute the integration tests
echo "Starting integration tests scenes"

./integration_tests/piggy_bank/scripts/run_test.sh $1
./integration_tests/wrapping/scripts/run_test.sh $1
./integration_tests/token_management/scripts/run_test.sh $1
./integration_tests/data_store/scripts/run_test.sh $1

