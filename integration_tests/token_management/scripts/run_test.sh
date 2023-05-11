#!/bin/bash
set -e

if ! [[ " ${1} " =~ " localnet "|" devnet " ]]; then
    echo "Token management tests not available on ${1}"
    exit 0
fi

python -m mxops \
            execute \
            -n $1 \
            -s integration_test_token_management \
            -c \
            integration_tests/setup_scenes/01_accounts.yaml \
            integration_tests/token_management/mxops_scenes
