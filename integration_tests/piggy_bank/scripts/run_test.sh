#!/bin/bash
set -e

if ! [[ " ${1} " =~ " localnet "|" devnet "|" chain-simulator " ]]; then
    echo "Piggy bank tests not available on ${1}"
    exit 0
fi

python -m mxops \
            execute \
            -n $1 \
            -s integration_test_piggy_bank_user_exploit \
            -c \
            integration_tests/setup_scenes/01_accounts.yaml \
            integration_tests/piggy_bank/mxops_scenes/user_exploit
