#!/bin/bash
set -e

# Ensure dependencies are synced
uv sync

# Check if there are at least 2 arguments and second is "faucet"
if [ $# -ge 2 ] && [ "$2" = "faucet" ]; then
    bash integration_tests/scripts/setup.sh $1
fi

# execute integration_tests
bash scripts/launch_integration_tests.sh $1
