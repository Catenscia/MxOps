#!/bin/bash
set -e

# Execute the integration tests
echo "Starting integration tests scenes"

./integration_tests/piggy_bank/scripts/run_test.sh $1
./integration_tests/wrapping/scripts/run_test.sh $1
./integration_tests/token_management/scripts/run_test.sh $1
./integration_tests/data_store/scripts/run_test.sh $1

