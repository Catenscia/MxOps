#!/bin/bash
set -e

if ! [[ " ${1} " =~ " localnet "|" devnet " ]]; then
    echo "Token management tests not available on ${1}"
    exit 0
fi

# execute integration test for the fungible token
python -m mxops \
            data \
            delete \
            -n $1 \
            -s integration_test_token_management \
            -y

python -m mxops \
            execute \
            -n $1 \
            -s integration_test_token_management \
            integration_tests/setup_scenes/01_accounts.yaml \
            integration_tests/token_management/mxops_scenes
