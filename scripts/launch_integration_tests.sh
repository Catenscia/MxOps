#!/bin/bash
set -e

if [ "$1" == "localnet" ]; then
  echo "Executing integration test on the localnet"
elif [ "$1" == "devnet" ]; then
  echo "Executing integration test on the devnet"
else
  echo "Invalid netork argument"
  exit 1
fi

# Execute the integration tests
echo "Starting integration tests scenes"

./integration_tests/piggy_bank/scripts/run_test.sh $1
./integration_tests/wrapping/scripts/run_test.sh $1
./integration_tests/token_management/scripts/run_test.sh $1
